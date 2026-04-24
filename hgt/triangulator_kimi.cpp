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
        edge_to_triangles_.clear();
        free_triangle_slots_.clear();

        // Quantized grid: direct array lookup for O(1) neighbor access
        active_grid_.assign(max_active_rows_ * cols_, -1);

        // Reserve space to avoid reallocations
        all_points_.reserve(cols_ * max_active_rows_ * 2);
        active_triangles_.reserve(cols_ * max_active_rows_ * 2);
        finalized_triangles_.reserve(cols_ * max_active_rows_ * 2);
        edge_to_triangles_.reserve(cols_ * max_active_rows_ * 2);
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
               finalized_triangles_.capacity() * sizeof(Triangle);
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
    // Incremental Triangle Allocation/Deallocation
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

        // Incremental edge map update: add immediately on allocation
        addEdge(a, b, idx);
        addEdge(b, c, idx);
        addEdge(c, a, idx);
        ++active_triangle_count_;
        return idx;
    }

    void deallocateTriangle(size_t idx) {
        if (!active_triangles_[idx].active) return;

        const auto& tri = active_triangles_[idx];

        // Incremental edge map update: remove immediately on deallocation
        removeEdgeTri(tri.v0, tri.v1, idx);
        removeEdgeTri(tri.v1, tri.v2, idx);
        removeEdgeTri(tri.v2, tri.v0, idx);

        active_triangles_[idx].active = false;
        free_triangle_slots_.push_back(idx);
        --active_triangle_count_;
    }


    // -------------------------------------------------------------------------
    // Edge Map: O(1) average lookups, incrementally maintained
    // -------------------------------------------------------------------------

    void addEdge(size_t a, size_t b, size_t tri_idx) {
        edge_to_triangles_[Edge(a, b)].push_back(tri_idx);
    }

    void removeEdgeTri(size_t a, size_t b, size_t tri_idx) {
        auto it = edge_to_triangles_.find(Edge(a, b));
        if (it == edge_to_triangles_.end()) return;

        auto& vec = it->second;
        // O(1) swap-pop removal; edges typically have low valence (1-2)
        for (size_t i = 0; i < vec.size(); ++i) {
            if (vec[i] == tri_idx) {
                vec[i] = vec.back();
                vec.pop_back();
                break;
            }
        }
        if (vec.empty()) edge_to_triangles_.erase(it);
    }

    const std::vector<size_t>* getEdgeTris(size_t a, size_t b) const {
        auto it = edge_to_triangles_.find(Edge(a, b));
        return (it != edge_to_triangles_.end()) ? &it->second : nullptr;
    }

    // Triangulate between two rows using standard strip pattern
    // Creates triangles in consistent winding order
    void triangulateStrip(const std::span<const size_t>& top_row,
                          const std::span<const size_t>& bottom_row) {
        for (size_t c = 0; c < cols_ - 1; ++c) {
            const size_t tl = top_row[c];
            const size_t bl = bottom_row[c];
            const size_t br = bottom_row[c+1];
            const size_t tr = top_row[c+1];

            const size_t t1_idx = active_triangles_.size();
            active_triangles_.emplace_back(tl, bl, br);

            const size_t t2_idx = active_triangles_.size();
            active_triangles_.emplace_back(tl, br, tr);

            // Build edge-to-triangle map using spatial hash for fast lookups
            addEdgeToMap(tl, bl, t1_idx);
            addEdgeToMap(bl, br, t1_idx);
            addEdgeToMap(br, tl, t1_idx);

            addEdgeToMap(tl, br, t2_idx);
            addEdgeToMap(br, tr, t2_idx);
            addEdgeToMap(tr, tl, t2_idx);
        }
    }

    void addEdgeToMap(size_t a, size_t b, size_t tri_idx) {
        Edge edge(a, b);
        edge_to_triangles_[edge].push_back(tri_idx);
    }

    const std::vector<size_t>* getTrianglesForEdge(size_t a, size_t b) const {
        auto it = edge_to_triangles_.find(Edge(a, b));
        return (it != edge_to_triangles_.end()) ? &it->second : nullptr;
    }

    void simplifyAndFinalize() {
        size_t finalize_until_row = finalized_row_ + 1;

        simplifyActiveRegion(finalized_row_, finalize_until_row);

        // Move finalized triangles out and deallocate (updates edge map incrementally)
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
                deallocateTriangle(i);
            }
        }

        // Clear finalized row from quantized grid
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
        // NO rebuildEdgeMap() needed — indices remain stable via free-list reuse
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

        auto checkEdge = [&](size_t a, size_t b) {
            const auto tris = getEdgeTris(a, b);
            if (!tris) return;
            for (size_t ot : *tris) {
                if (ot == tri_idx || !active_triangles_[ot].active) continue;

                const auto& other = active_triangles_[ot];
                const Point& op0 = all_points_[other.v0];
                const Point& op1 = all_points_[other.v1];
                const Point& op2 = all_points_[other.v2];

                const double oax = op1.x - op0.x;
                const double oay = op1.y - op0.y;
                const double oaz = op1.z - op0.z;
                const double obx = op2.x - op0.x;
                const double oby = op2.y - op0.y;
                const double obz = op2.z - op0.z;

                double onx = oay * obz - oaz * oby;
                double ony = oaz * obx - oax * obz;
                double onz = oax * oby - oay * obx;
                const double olen = std::sqrt(onx*onx + ony*ony + onz*onz);

                if (olen > 1e-10) {
                    onx /= olen; ony /= olen; onz /= olen;
                    const double dot = std::abs(nx * onx + ny * ony + nz * onz);
                    max_dihedral = std::max(max_dihedral, std::acos(std::clamp(dot, -1.0, 1.0)));
                }
            }
        };

        checkEdge(tri.v0, tri.v1);
        checkEdge(tri.v1, tri.v2);
        checkEdge(tri.v2, tri.v0);

        // Height variation
        const double height_var = std::max({
            std::abs(p0.z - p1.z),
            std::abs(p1.z - p2.z),
            std::abs(p2.z - p0.z)
        });

        // Error: prefer removing flat, small triangles in smooth regions
        return area * (1.0 + max_dihedral * 2.0) * (1.0 + height_var);
    }

    // Fast manifold preservation check using spatial hash
    bool canRemoveTriangle(size_t idx) const {
        const auto& tri = active_triangles_[idx];

        auto hasActiveNeighbor = [&](size_t a, size_t b) -> bool {
            const auto tris = getEdgeTris(a, b);
            if (!tris) return false;
            for (size_t t : *tris) {
                if (t != idx && active_triangles_[t].active) return true;
            }
            return false;
        };

        return hasActiveNeighbor(tri.v0, tri.v1) &&
               hasActiveNeighbor(tri.v1, tri.v2) &&
               hasActiveNeighbor(tri.v2, tri.v0);
    }

    void rebuildEdgeMap() {
        edge_to_triangles_.clear();
        for (size_t i = 0; i < active_triangles_.size(); ++i) {
            const auto& tri = active_triangles_[i];
            addEdgeToMap(tri.v0, tri.v1, i);
            addEdgeToMap(tri.v1, tri.v2, i);
            addEdgeToMap(tri.v2, tri.v0, i);
        }
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

    // Incremental edge map: no full rebuilds needed
    std::unordered_map<Edge, std::vector<size_t>, EdgeHash> edge_to_triangles_;

    // Free-list for stable triangle indices
    std::vector<size_t> free_triangle_slots_;
    size_t active_triangle_count_;
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
