//===----------------------------------------------------------------------===//
//
// NAME         : triangulator_kimi
// NAMESPACE    : HGT
// PURPOSE      : Provide function for converting HGT file to 3D mesh.
// COPYRIGHT    : Public Domain / https://creativecommons.org/public-domain/cc0/
// AUTHORS      : Kimi 2.6, driven by Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provides functions for taking a HGT (height) files which
//                are a data file of the Shuttle Radar Topography Mission
//                (SRTM) and producing a 3D mesh (also known as triangulation)
//                from it.
//
// The resulting 3D mesh should not simply contain 3601 * 3601 points (or 1201
// by 1202 for STRM3) and should be simplified.
//
// PROMPT       : Write a function in C++ that triangulates a digital elevation
// model (provided as the row and column counts and array of heights in
// column-major order) where the outputs are the points and facets (triangles)
// that represent the model. The algorithm should work incrementally and simply
// the triangulation as it goes to reduce total memory usage.
//
// INITAL ISSUES: The following problems existed in the code generated code.
// - std::invalid_argument was undefined due to missing include of <stdexcept>.
//   Most humans would likely forget that quite often.
// - std::iota was undefined due to missing include <numeric>.
// - Conversion from 'size_t' to 'int', possible loss of data
//   * Use size_t instead of int in for loop.
// - Runtime: Slow - took 1290 seconds (21.5 minutes) for single HGT.
//   - Single threaded so could generate multiple tiles sat same time.
//   - 38% time spent in canRemoveTriangle()
//   - 12% in FreeHeap - of which this was in rebuildEdgeMap()
//   - 8% in std::hash::find()
//   - 1024 active rows and 30% reduction. Resulting lply was 83MB.
//     There were 1072984 vertices out of a 12967201.
// - Runtime even slower -  7286.809s (around 2 hours).
//    - Increased simplification factor.
//   - 87.8% spent in canRemoveTriangle.
//   - There were 1335315 vertices out of a 12967201 and 2660689 facets.
// - Runtime acceptable - 402 seconds (just under 7 minutes) for single HGT.
//   - Replaced the version that doesn't hash the X and Y coordinates.
// - Runtime after this latest prompt - 240 seconds for single HGT.
//     Go ahead and eliminate the edge map entirely.
//   - 36% time in std::priority_queue::pop()
//   - 21% in simplifyActiveRegion
//   - 10% in checkNeighbor() within computeTriangleError().
//  - There were 1442401 vertices out of 12967201 and 2882400 facets.
//
//===----------------------------------------------------------------------===//

#include "triangulator_kimi.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <memory>
#include <numeric>
#include <queue>
#include <span>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using Triangulator::Kimi::Point;
using Triangulator::Kimi::Triangle;

struct Edge {
    const size_t v0, v1;
    Edge(size_t a, size_t b) : v0(std::min(a, b)), v1(std::max(a, b)) {}

    inline bool operator==(const Edge& other) const {
        return v0 == other.v0 && v1 == other.v1;
    }
};

struct EdgeHash {
    size_t operator()(const Edge& e) const {
        return std::hash<size_t>()(e.v0) ^ (std::hash<size_t>()(e.v1) << 1);
    }
};

// -----------------------------------------------------------------------------
// Incremental DEM Triangulator with Memory-Bounded Simplification
// -----------------------------------------------------------------------------

class IncrementalDEMTriangulator {
public:
    // Parameters:
    //   max_active_rows: How many rows to keep in the active window
    //   target_reduction: Target fraction of triangles to remove (0.0 = none, 0.9 = aggressive)
    //   error_threshold: Maximum allowed geometric error from simplification
    IncrementalDEMTriangulator(size_t max_active_rows = 64,
                               double target_reduction = 0.5,
                               double error_threshold = 1.0)
        : max_active_rows_(max_active_rows)
        , target_reduction_(target_reduction)
        , error_threshold_(error_threshold)
        , cols_(0)
        , current_row_(0)
        , finalized_row_(0)
        , cell_size_x_(1.0)
        , cell_size_y_(1.0)
        , active_triangle_count_(0)
        {}

    // Initialize with DEM dimensions and cell sizes
    void initialize(size_t num_cols, double cell_size_x = 1.0, double cell_size_y = 1.0) {
        cols_ = num_cols;
        cell_size_x_ = cell_size_x;
        cell_size_y_ = cell_size_y;
        current_row_ = 0;
        finalized_row_ = 0;
        active_triangle_count_ = 0;

        all_points_.clear();
        active_triangles_.clear();
        finalized_triangles_.clear();
        free_triangle_slots_.clear();

        // Quantized grid: direct array lookup for O(1) neighbor access
        active_grid_.assign(max_active_rows_ * cols_, -1);

        // Flat edge arrays: 2 triangle indices per edge slot (manifold = max 2)
        // Vertical edges: between (r,c) and (r+1,c)
        vert_edges_.assign(max_active_rows_ * cols_ * 2, INVALID);
        // Horizontal edges: between (r,c) and (r,c+1)
        horiz_edges_.assign(max_active_rows_ * (cols_ - 1) * 2, INVALID);
        // Diagonal edges: between (r,c) and (r+1,c+1)
        diag_edges_.assign(max_active_rows_ * (cols_ - 1) * 2, INVALID);

        // Reserve space to avoid reallocations
        all_points_.reserve(cols_ * max_active_rows_ * 2);
        active_triangles_.reserve(cols_ * max_active_rows_ * 2);
        finalized_triangles_.reserve(cols_ * max_active_rows_ * 2);
    }

    // Process a new row of height data (column-major: heights[col] for this row)
    // Call this repeatedly for each row of the DEM.
    void addRow(const std::span<const double>& heights) {
        if (heights.size() != cols_) {
            throw std::invalid_argument("Row size mismatch");
        }

        // Create points for this row
        std::vector<size_t> new_point_indices;
        new_point_indices.reserve(cols_);

        for (size_t column = 0; column < cols_; ++column) {
            const size_t idx = all_points_.size();
            all_points_.emplace_back(
                column * cell_size_x_,       // x
                current_row_ * cell_size_y_, // y
                heights[column],             // z
                current_row_, column, idx
            );
            new_point_indices.push_back(idx);

            // Quantized insert: direct array indexing, no hash computation
            active_grid_[gridIndex(current_row_, column)] =
                static_cast<int64_t>(idx);
        }

        // Triangulate with previous row if available
        if (!prev_row_indices_.empty()) {
            triangulateStrip(prev_row_indices_, new_point_indices);
        }

        // Update row tracking
        prev_row_indices_ = std::move(new_point_indices);

        // Simplify active region if window is full
        if (current_row_ >= finalized_row_ + max_active_rows_) {
            simplifyAndFinalize();
        }

        ++current_row_;
    }

    // Finalize: process remaining active geometry and return results
    void finalize(std::vector<Point>& out_points,
                  std::vector<Triangle>& out_triangles) {
        // Simplify remaining active triangles
        if (!active_triangles_.empty()) {
            simplifyActiveRegion(finalized_row_, current_row_);
        }

        // Move all remaining to finalized
        finalized_triangles_.insert(finalized_triangles_.end(),
                                    active_triangles_.begin(),
                                    active_triangles_.end());
        active_triangles_.clear();

        // Compact points: remove unused (simplified away) points
        compactAndOutput(out_points, out_triangles);
    }

    // Get current memory footprint estimate (points + triangles)
    size_t memoryEstimate() const {
        return all_points_.capacity() * sizeof(Point) +
               active_triangles_.capacity() * sizeof(Triangle) +
               finalized_triangles_.capacity() * sizeof(Triangle) +
               active_grid_.size() * sizeof(int64_t) +
               vert_edges_.size() * sizeof(size_t) +
               horiz_edges_.size() * sizeof(size_t) +
               diag_edges_.size() * sizeof(size_t);
    }

private:
    // -------------------------------------------------------------------------
    // Quantized Grid: O(1) direct lookup via (row % max_active_rows, col)
    // -------------------------------------------------------------------------

    size_t gridIndex(size_t row, size_t col) const {
        return static_cast<size_t>((row % max_active_rows_) * cols_ + col);
    }

    int64_t getGridVertex(size_t row, size_t col) const {
        if (row < finalized_row_ || row >= current_row_) return -1;
        if (col < 0 || col >= cols_) return -1;
        return active_grid_[gridIndex(row, col)];
    }

    void getVertexNeighbors(size_t v, std::vector<size_t>& out) const {
        out.clear();
        const Point& p = all_points_[v];
        for (int dr = -1; dr <= 1; ++dr) {
            for (int dc = -1; dc <= 1; ++dc) {
                if (dr == 0 && dc == 0) continue;
                int64_t vi = getGridVertex(p.row + dr, p.col + dc);
                if (vi >= 0) out.push_back(static_cast<size_t>(vi));
            }
        }
    }

    // -------------------------------------------------------------------------
    // Edge classification & slot access
    // Every edge in the grid falls into one of three categories:
    //   0 = vertical:   (r,c) -- (r+1,c)
    //   1 = horizontal: (r,c) -- (r,c+1)
    //   2 = diagonal:   (r,c) -- (r+1,c+1)
    // -------------------------------------------------------------------------

    struct EdgeLoc {
        uint8_t type; // 0=vert, 1=horiz, 2=diag
        size_t row;
        size_t col;
    };

    EdgeLoc classifyEdge(size_t va, size_t vb) const {
        const Point& a = all_points_[va];
        const Point& b = all_points_[vb];
        const int dr = static_cast<int>(b.row) - static_cast<int>(a.row);
        const int dc = static_cast<int>(b.col) - static_cast<int>(a.col);

        if (dr == 1) {
            if (dc == 0) return {0, a.row, a.col};
            return {2, a.row, a.col};           // dc == 1
        }
        if (dr == -1) {
            if (dc == 0) return {0, b.row, b.col};
            return {2, b.row, b.col};           // dc == -1
        }
        // dr == 0
        if (dc == 1) return {1, a.row, a.col};
        return {1, b.row, b.col};               // dc == -1
    }

    size_t* edgeSlot(const EdgeLoc& loc) {
        int mr = loc.row % static_cast<int>(max_active_rows_);
        if (mr < 0) mr += static_cast<int>(max_active_rows_);
        size_t base = static_cast<size_t>(mr);

        switch (loc.type) {
            case 0:  return &vert_edges_[(base * cols_ + loc.col) * 2];
            case 1:  return &horiz_edges_[(base * (cols_ - 1) + loc.col) * 2];
            default: return &diag_edges_[(base * (cols_ - 1) + loc.col) * 2];
        }
    }

    const size_t* edgeSlot(const EdgeLoc& loc) const {
        int mr = loc.row % static_cast<int>(max_active_rows_);
        if (mr < 0) mr += static_cast<int>(max_active_rows_);
        size_t base = static_cast<size_t>(mr);

        switch (loc.type) {
            case 0:  return &vert_edges_[(base * cols_ + loc.col) * 2];
            case 1:  return &horiz_edges_[(base * (cols_ - 1) + loc.col) * 2];
            default: return &diag_edges_[(base * (cols_ - 1) + loc.col) * 2];
        }
    }

    // Add triangle to edge slot (max 2 triangles per edge in manifold mesh)
    void addTriToEdge(size_t va, size_t vb, size_t tri) {
        size_t* slot = edgeSlot(classifyEdge(va, vb));
        if (slot[0] == INVALID) slot[0] = tri;
        else                    slot[1] = tri;
    }

    // Remove triangle from edge slot
    void removeTriFromEdge(size_t va, size_t vb, size_t tri) {
        size_t* slot = edgeSlot(classifyEdge(va, vb));
        if (slot[0] == tri) {
            slot[0] = slot[1];
            slot[1] = INVALID;
        } else if (slot[1] == tri) {
            slot[1] = INVALID;
        }
    }

    // Check if edge has another active triangle besides 'self'
    bool edgeHasOther(const EdgeLoc& loc, size_t self) const {
        const size_t* slot = edgeSlot(loc);
        size_t t0 = slot[0], t1 = slot[1];
        if (t0 != INVALID && t0 != self && active_triangles_[t0].active) return true;
        if (t1 != INVALID && t1 != self && active_triangles_[t1].active) return true;
        return false;
    }

    // Get the other active triangle on this edge (INVALID if none)
    size_t edgeOther(const EdgeLoc& loc, size_t self) const {
        const size_t* slot = edgeSlot(loc);
        size_t t0 = slot[0], t1 = slot[1];
        if (t0 != INVALID && t0 != self && active_triangles_[t0].active) return t0;
        if (t1 != INVALID && t1 != self && active_triangles_[t1].active) return t1;
        return INVALID;
    }

    // -------------------------------------------------------------------------
    // Incremental Triangle Allocation/Deallocation with free-list reuse.
    // -------------------------------------------------------------------------
    size_t allocateTriangle(size_t a, size_t b, size_t c) {
        size_t idx;
        if (!free_triangle_slots_.empty()) {
            idx = free_triangle_slots_.back();
            free_triangle_slots_.pop_back();
            active_triangles_[idx] = Triangle(a, b, c);
            active_triangles_[idx].active = true;
        } else {
            idx = active_triangles_.size();
            active_triangles_.emplace_back(a, b, c);
        }
        ++active_triangle_count_;
        return idx;
    }

    void deallocateTriangle(size_t idx) {
        if (!active_triangles_[idx].active) return;

        const auto& tri = active_triangles_[idx];
        removeTriFromEdge(tri.v0, tri.v1, idx);
        removeTriFromEdge(tri.v1, tri.v2, idx);
        removeTriFromEdge(tri.v2, tri.v0, idx);

        active_triangles_[idx].active = false;
        free_triangle_slots_.push_back(idx);
        --active_triangle_count_;
    }

    // -------------------------------------------------------------------------
    // Triangulation
    // -------------------------------------------------------------------------
    //
    // Triangulate between two rows using standard strip pattern
    // Creates triangles in consistent winding order
    void triangulateStrip(const std::span<const size_t>& top_row,
                          const std::span<const size_t>& bottom_row) {
        for (size_t c = 0; c < cols_ - 1; ++c) {
            const size_t tl = top_row[c];
            const size_t bl = bottom_row[c];
            const size_t br = bottom_row[c+1];
            const size_t tr = top_row[c+1];

            size_t t1 = allocateTriangle(tl, bl, br);
            size_t t2 = allocateTriangle(tl, br, tr);

            // Wire into flat edge arrays (incremental, no rebuilds needed)
            addTriToEdge(tl, bl, t1); // vert
            addTriToEdge(bl, br, t1); // horiz
            addTriToEdge(br, tl, t1); // diag

            addTriToEdge(tl, br, t2); // diag (shared with t1)
            addTriToEdge(br, tr, t2); // vert
            addTriToEdge(tr, tl, t2); // horiz
        }
    }

    // -------------------------------------------------------------------------
    // Simplification
    // -------------------------------------------------------------------------

    void simplifyAndFinalize() {
        size_t finalize_until_row = finalized_row_ + 1;

        simplifyActiveRegion(finalized_row_, finalize_until_row);

        // Move finalized triangles out and deallocate.
        for (size_t i = 0; i < active_triangles_.size(); ++i) {
            const auto& tri = active_triangles_[i];
            if (!tri.active) continue;

            const auto min_row = std::min({
                all_points_[tri.v0].row,
                all_points_[tri.v1].row,
                all_points_[tri.v2].row
            });

            if (min_row < finalize_until_row) {
                finalized_triangles_.push_back(tri);
                deallocateTriangle(i);  // Updates edge slots incrementally
            }
        }

        // Clear finalized row from vertex grid.
        for (size_t column = 0; column < cols_; ++column) {
            active_grid_[gridIndex(finalized_row_, column)] = -1;
        }

        ++finalized_row_;
    }

    // Quadric Error Metric (QEM) based simplification
    // This is a lightweight version suitable for incremental processing
   void simplifyActiveRegion(size_t start_row, size_t end_row) {
        if (active_triangle_count_ < 10) return;

        // Compute errors using fast edge-map neighbor lookups
        for (size_t i = 0; i < active_triangles_.size(); ++i) {
            if (active_triangles_[i].active) {
                active_triangles_[i].error = computeTriangleError(i);
            }
        }

        const size_t target_count = std::max(static_cast<size_t>(
            active_triangle_count_ * (1.0 - target_reduction_)
        ), size_t(cols_ * 2));

        // Priority queue over active triangles only
        using QueueItem = std::pair<double, size_t>;
        std::priority_queue<QueueItem, std::vector<QueueItem>, std::greater<QueueItem>> pq;

        for (size_t i = 0; i < active_triangles_.size(); ++i) {
            if (active_triangles_[i].active) {
                pq.push({active_triangles_[i].error, i});
            }
        }

        while (!pq.empty() && active_triangle_count_ > target_count) {
            const auto [err, idx] = pq.top();
            pq.pop();

            if (!active_triangles_[idx].active) continue;

            const auto& tri = active_triangles_[idx];
            const auto max_row = std::max({
                all_points_[tri.v0].row,
                all_points_[tri.v1].row,
                all_points_[tri.v2].row
            });

            if (max_row >= end_row) continue;
            if (!canRemoveTriangle(idx)) continue;

            if (err < error_threshold_) {
                deallocateTriangle(idx);  // Incremental edge map update
            }
        }
    }

    // Fast error computation using spatial hash for neighborhood queries
    double computeTriangleError(size_t tri_idx) const {
        const auto& tri = active_triangles_[tri_idx];
        const Point& p0 = all_points_[tri.v0];
        const Point& p1 = all_points_[tri.v1];
        const Point& p2 = all_points_[tri.v2];

        // Normal
        const double ax = p1.x - p0.x, ay = p1.y - p0.y, az = p1.z - p0.z;
        const double bx = p2.x - p0.x, by = p2.y - p0.y, bz = p2.z - p0.z;

        double nx = ay * bz - az * by;
        double ny = az * bx - ax * bz;
        double nz = ax * by - ay * bx;
        const double len = std::sqrt(nx*nx + ny*ny + nz*nz);

        if (len < 1e-10) return std::numeric_limits<double>::max();

        nx /= len; ny /= len; nz /= len;
        const double area = 0.5 * len;

        // Fast dihedral computation via edge map (O(1) per edge)
        double max_dihedral = 0.0;

        auto checkNeighbor = [&](size_t va, size_t vb) {
            size_t ot = edgeOther(classifyEdge(va, vb), tri_idx);
            if (ot == INVALID) return;

            const auto& other = active_triangles_[ot];
            const Point& q0 = all_points_[other.v0];
            const Point& q1 = all_points_[other.v1];
            const Point& q2 = all_points_[other.v2];

            double oax = q1.x - q0.x, oay = q1.y - q0.y, oaz = q1.z - q0.z;
            double obx = q2.x - q0.x, oby = q2.y - q0.y, obz = q2.z - q0.z;

            double onx = oay * obz - oaz * oby;
            double ony = oaz * obx - oax * obz;
            double onz = oax * oby - oay * obx;
            double olen = std::sqrt(onx*onx + ony*ony + onz*onz);

            if (olen > 1e-10) {
                onx /= olen; ony /= olen; onz /= olen;
                double dot = std::abs(nx * onx + ny * ony + nz * onz);
                max_dihedral = std::max(max_dihedral, std::acos(std::clamp(dot, -1.0, 1.0)));
            }
        };

        checkNeighbor(tri.v0, tri.v1);
        checkNeighbor(tri.v1, tri.v2);
        checkNeighbor(tri.v2, tri.v0);

        // Height variation
        const double height_var = std::max({
            std::abs(p0.z - p1.z),
            std::abs(p1.z - p2.z),
            std::abs(p2.z - p0.z)
        });

        // Error: prefer removing flat, small triangles in smooth regions
        return area * (1.0 + max_dihedral * 2.0) * (1.0 + height_var);
    }

    // Fast manifold check — zero hash lookups, pure arithmetic + array access.
    bool canRemoveTriangle(size_t idx) const {
        const auto& tri = active_triangles_[idx];
        return edgeHasOther(classifyEdge(tri.v0, tri.v1), idx) &&
               edgeHasOther(classifyEdge(tri.v1, tri.v2), idx) &&
               edgeHasOther(classifyEdge(tri.v2, tri.v0), idx);
    }

    // Compact output: remap point indices to remove unused points
    void compactAndOutput(std::vector<Point>& out_points,
                          std::vector<Triangle>& out_triangles) {
        std::vector<bool> used(all_points_.size(), false);

        for (const auto& tri : finalized_triangles_) {
            used[tri.v0] = true;
            used[tri.v1] = true;
            used[tri.v2] = true;
        }

        std::vector<size_t> remap(all_points_.size(), static_cast<size_t>(-1));
        size_t new_idx = 0;

        for (size_t i = 0; i < all_points_.size(); ++i) {
            if (used[i]) remap[i] = new_idx++;
        }

        out_points.clear();
        out_points.reserve(new_idx);

        for (size_t i = 0; i < all_points_.size(); ++i) {
            if (used[i]) {
                Point p = all_points_[i];
                p.index = remap[i];
                out_points.push_back(p);
            }
        }

        out_triangles.clear();
        out_triangles.reserve(finalized_triangles_.size());

        for (const auto& tri : finalized_triangles_) {
            out_triangles.emplace_back(remap[tri.v0], remap[tri.v1], remap[tri.v2]);
        }
    }
    // Configuration
    size_t max_active_rows_;
    double target_reduction_;
    double error_threshold_;

    // DEM state
    size_t cols_;
    size_t current_row_;
    size_t finalized_row_;
    double cell_size_x_, cell_size_y_;

    // Data
    std::vector<Point> all_points_;
    std::vector<Triangle> active_triangles_;
    std::vector<Triangle> finalized_triangles_;
    std::vector<size_t> prev_row_indices_;

    // Quantized grid: direct (row, col) → vertex index mapping
    std::vector<int64_t> active_grid_;

    // Flat edge arrays — 2 entries per slot (max 2 triangles per edge)
    std::vector<size_t> vert_edges_;   // vertical:   (r,c) -- (r+1,c)
    std::vector<size_t> horiz_edges_;  // horizontal: (r,c) -- (r,c+1)
    std::vector<size_t> diag_edges_;   // diagonal:   (r,c) -- (r+1,c+1)

    // Free-list for stable triangle indices
    std::vector<size_t> free_triangle_slots_;
    size_t active_triangle_count_;

    static constexpr size_t INVALID = static_cast<size_t>(-1);
};

Triangulator::Kimi::DEMTriangulationResult Triangulator::Kimi::triangulateDEM(
    int rows, size_t cols,
    const double* heights,
    double cell_size_x,
    double cell_size_y,
    size_t max_active_rows,
    double simplification)
{
    IncrementalDEMTriangulator triangulator(max_active_rows, simplification);
    triangulator.initialize(cols, cell_size_x, cell_size_y);

    std::vector<double> row(cols);

    for (int r = 0; r < rows; ++r) {
        // Extract row from column-major array
        for (size_t c = 0; c < cols; ++c) {
            row[c] = heights[r * cols + c];
        }
        triangulator.addRow(row);
    }

    DEMTriangulationResult result;
    triangulator.finalize(result.points, result.triangles);
    result.peak_memory_bytes = triangulator.memoryEstimate();

    return result;
}

bool Triangulator::Kimi::writePLY(const std::string& filename,
                                  const DEMTriangulationResult& result) {
    std::ofstream file(filename);
    if (!file.is_open()) {
        return false;
    }

    const size_t numPoints = result.points.size();
    const size_t numTriangles = result.triangles.size();

    // PLY header (ASCII format)
    file << "ply\n";
    file << "format ascii 1.0\n";
    file << "element vertex " << numPoints << "\n";
    file << "property float x\n";
    file << "property float y\n";
    file << "property float z\n";
    file << "element face " << numTriangles << "\n";
    file << "property list uchar int vertex_indices\n";
    file << "end_header\n";

    // Write vertices
    for (const auto& p : result.points) {
        // Use sufficient precision to reconstruct accurately
        file << std::fixed << std::setprecision(6)
             << p.x << " " << p.y << " " << p.z << "\n";
    }

    // Write faces (triangles)
    // PLY uses uchar count followed by vertex indices
    for (const auto& tri : result.triangles) {
        file << "3 " << tri.v0 << " " << tri.v1 << " " << tri.v2 << "\n";
    }

    file.close();
    return file.good();
}

#ifdef KIMI_MAIN

#include <iostream>
#include <random>

int main() {
    // Create a sample DEM: 512x512 with some noise and a hill
    const int ROWS = 512;
    const int COLS = 512;

    std::vector<double> dem(ROWS * COLS);
    std::mt19937 rng(42);
    std::uniform_real_distribution<double> noise(-2.0, 2.0);

    for (int r = 0; r < ROWS; ++r) {
        for (int c = 0; c < COLS; ++c) {
            double x = (c - COLS/2.0) / 50.0;
            double y = (r - ROWS/2.0) / 50.0;
            double hill = 100.0 * std::exp(-(x*x + y*y) / 2.0);
            dem[r * COLS + c] = hill + noise(rng);
        }
    }

    // Triangulate with incremental simplification
    // Using a small window to demonstrate memory bounding
    const auto result = Triangulator::Kimi::triangulateDEM(
        ROWS, COLS, dem.data(),
        1.0, 1.0,           // cell sizes
        32,                 // max active rows (small for demo)
        0.7                 // 70% triangle reduction target
    );

    size_t original_tris = (ROWS - 1) * (COLS - 1) * 2;

    std::cout << "DEM size: " << ROWS << " x " << COLS << "\n";
    std::cout << "Original triangles: " << original_tris << "\n";
    std::cout << "Output points: " << result.points.size() << "\n";
    std::cout << "Output triangles: " << result.triangles.size() << "\n";
    std::cout << "Reduction ratio: "
              << (1.0 - double(result.triangles.size()) / original_tris) * 100.0
              << "%\n";
    std::cout << "Peak memory estimate: " << result.peak_memory_bytes / 1024 / 1024
              << " MB\n";

    // Verify winding order of first triangle
    if (!result.triangles.empty()) {
        const auto& t = result.triangles[0];
        const auto& p0 = result.points[t.v0];
        const auto& p1 = result.points[t.v1];
        const auto& p2 = result.points[t.v2];

        double cross = (p1.x - p0.x) * (p2.y - p0.y) -
                       (p2.x - p0.x) * (p1.y - p0.y);
        std::cout << "First triangle winding (z-component): " << cross << "\n";
    }

    Triangulator::Kimi::writePLY("mesh_example.ply", result);

    return 0;
}

#endif
