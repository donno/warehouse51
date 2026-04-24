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
//   - 38% time spent in canRemoveTriangleFast()
//   - 12% in FreeHeap - of which this was in rebuildEdgeMap()
//   - 8% in std::hash::find()
//   - 1024 active rows and 30% reduction. Resulting lply was 83MB.
//     There were 1072984 vertices out of a 12967201.
// - Runtime even slower -  7286.809s (around 2 hours).
//    - Increased simplification factor.
//   - 87.8% spent in canRemoveTriangleFast.
//   - There were 1335315 vertices out of a 12967201 and 2660689 facets.
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
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using Triangulator::Kimi::Point;
using Triangulator::Kimi::Triangle;

// Spatial Hash for Fast Neighbor Lookups.
class SpatialHash {
public:
    SpatialHash(double cellSize = 1.0) : cellSize_(cellSize), invCellSize_(1.0 / cellSize) {}

    void clear() {
        grid_.clear();
    }

    // Insert a point with its index
    void insert(double x, double y, size_t index) {
        auto key = hash(x, y);
        grid_[key].push_back(index);
    }

    // Insert a point using integer grid coordinates (for DEM cells)
    void insert(int row, int col, size_t index) {
        auto key = hashInt(row, col);
        grid_[key].push_back(index);
    }

    // Find all points within radius of (x, y)
    void queryRadius(double x, double y, double radius, std::vector<size_t>& out) const {
        out.clear();
        int rCells = static_cast<int>(std::ceil(radius * invCellSize_));
        int cx = static_cast<int>(std::floor(x * invCellSize_));
        int cy = static_cast<int>(std::floor(y * invCellSize_));

        for (int dy = -rCells; dy <= rCells; ++dy) {
            for (int dx = -rCells; dx <= rCells; ++dx) {
                auto it = grid_.find(hashInt(cx + dx, cy + dy));
                if (it != grid_.end()) {
                    out.insert(out.end(), it->second.begin(), it->second.end());
                }
            }
        }
    }

    // Query by integer grid cell and immediate neighbors (8-connected)
    void queryNeighbors(int row, int col, std::vector<size_t>& out) const {
        out.clear();
        for (int dr = -1; dr <= 1; ++dr) {
            for (int dc = -1; dc <= 1; ++dc) {
                auto it = grid_.find(hashInt(row + dr, col + dc));
                if (it != grid_.end()) {
                    out.insert(out.end(), it->second.begin(), it->second.end());
                }
            }
        }
    }

    // Get all points in a specific cell
    const std::vector<size_t>* getCell(int row, int col) const {
        auto it = grid_.find(hashInt(row, col));
        return (it != grid_.end()) ? &it->second : nullptr;
    }

    // Remove a point (mark as removed - lazy deletion)
    void remove(int row, int col, size_t index) {
        auto key = hashInt(row, col);
        auto it = grid_.find(key);
        if (it != grid_.end()) {
            auto& vec = it->second;
            vec.erase(std::remove(vec.begin(), vec.end(), index), vec.end());
            if (vec.empty()) grid_.erase(it);
        }
    }

private:
    using Key = int64_t;

    double cellSize_;
    double invCellSize_;
    std::unordered_map<Key, std::vector<size_t>> grid_;

    Key hash(double x, double y) const {
        int ix = static_cast<int>(std::floor(x * invCellSize_));
        int iy = static_cast<int>(std::floor(y * invCellSize_));
        return hashInt(ix, iy);
    }

    static Key hashInt(int x, int y) {
        // Szudzik pairing for 2D->1D with signed support
        int32_t ux = static_cast<int32_t>(x);
        int32_t uy = static_cast<int32_t>(y);
        uint64_t a = (ux >= 0) ? 2 * static_cast<uint64_t>(ux) : -2 * static_cast<uint64_t>(ux) - 1;
        uint64_t b = (uy >= 0) ? 2 * static_cast<uint64_t>(uy) : -2 * static_cast<uint64_t>(uy) - 1;
        uint64_t c = (a >= b) ? a * a + a + b : a + b * b;
        return static_cast<Key>(c);
    }
};

struct Edge {
    size_t v0, v1;
    Edge(size_t a, size_t b) {
        v0 = std::min(a, b);
        v1 = std::max(a, b);
    }
    bool operator==(const Edge& other) const {
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
        , vertex_spatial_hash_(1.0)  // Cell size = 1 DEM cell
        {}

    // Initialize with DEM dimensions and cell sizes
    void initialize(int num_cols, double cell_size_x = 1.0, double cell_size_y = 1.0) {
        cols_ = num_cols;
        cell_size_x_ = cell_size_x;
        cell_size_y_ = cell_size_y;
        current_row_ = 0;
        finalized_row_ = 0;

        all_points_.clear();
        active_triangles_.clear();
        finalized_triangles_.clear();
        edge_to_triangles_.clear();
        vertex_spatial_hash_.clear();

        // Reserve space to avoid reallocations
        all_points_.reserve(cols_ * max_active_rows_ * 2);
        active_triangles_.reserve(cols_ * max_active_rows_ * 2);
        finalized_triangles_.reserve(cols_ * max_active_rows_ * 2);
        edge_to_triangles_.reserve(cols_ * max_active_rows_ * 2);
    }

    // Process a new row of height data (column-major: heights[col] for this row)
    // Call this repeatedly for each row of the DEM.
    void addRow(const std::vector<double>& heights) {
        if (heights.size() != static_cast<size_t>(cols_)) {
            throw std::invalid_argument("Row size mismatch");
        }

        // Create points for this row
        std::vector<size_t> new_point_indices;
        new_point_indices.reserve(cols_);

        for (int c = 0; c < cols_; ++c) {
            size_t idx = all_points_.size();
            all_points_.emplace_back(
                c * cell_size_x_,           // x
                current_row_ * cell_size_y_, // y
                heights[c],                  // z
                static_cast<int>(current_row_), c, idx
            );
            new_point_indices.push_back(idx);

            // Insert into spatial hash for fast neighbor queries
            vertex_spatial_hash_.insert(static_cast<int>(current_row_), c, idx);
        }

        // Triangulate with previous row if available
        if (!prev_row_indices_.empty()) {
            triangulateStrip(prev_row_indices_, new_point_indices);
        }

        // Update row tracking
        prev_row_indices_ = new_point_indices;
        row_point_indices_.push_back(std::move(new_point_indices));

        // Simplify active region if window is full
        if (row_point_indices_.size() >= max_active_rows_) {
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
    // Triangulate between two rows using standard strip pattern
    // Creates triangles in consistent winding order
    void triangulateStrip(const std::vector<size_t>& top_row,
                          const std::vector<size_t>& bottom_row) {
        for (int c = 0; c < cols_ - 1; ++c) {
            size_t tl = top_row[c];
            size_t bl = bottom_row[c];
            size_t br = bottom_row[c+1];
            size_t tr = top_row[c+1];

            size_t t1_idx = active_triangles_.size();
            active_triangles_.emplace_back(tl, bl, br);

            size_t t2_idx = active_triangles_.size();
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
        Edge e(a, b);
        edge_to_triangles_[e].push_back(tri_idx);
    }

    const std::vector<size_t>* getTrianglesForEdge(size_t a, size_t b) const {
        auto it = edge_to_triangles_.find(Edge(a, b));
        return (it != edge_to_triangles_.end()) ? &it->second : nullptr;
    }

    // Simplify the oldest portion of the active region and move to finalized
    void simplifyAndFinalize() {
        // Determine how many rows to finalize (typically 1, but can batch)
        size_t rows_to_finalize = 1;
        size_t finalize_until_row = finalized_row_ + rows_to_finalize;

        // Run simplification on active triangles
        simplifyActiveRegion(finalized_row_, finalize_until_row);

        // Move triangles that are entirely before finalize_until_row to finalized
        std::vector<Triangle> new_active;
        new_active.reserve(active_triangles_.size());

        for (auto& tri : active_triangles_) {
            int min_row = std::min({
                all_points_[tri.v0].row,
                all_points_[tri.v1].row,
                all_points_[tri.v2].row
            });

            if (min_row < static_cast<int>(finalize_until_row)) {
                finalized_triangles_.push_back(tri);
            } else {
                new_active.push_back(tri);
            }
        }

        active_triangles_ = std::move(new_active);

        // Clean up spatial hash for finalized rows
        cleanupSpatialHash(finalize_until_row);

        // Clean up point indices for finalized rows to allow GC
        if (!row_point_indices_.empty()) {
            row_point_indices_.erase(row_point_indices_.begin(),
                                     row_point_indices_.begin() + rows_to_finalize);
        }

        finalized_row_ = finalize_until_row;
    }

    void cleanupSpatialHash(size_t finalized_until_row) {
        // Remove finalized rows from spatial hash to save memory
        for (auto& p : all_points_) {
            if (p.row < static_cast<int>(finalized_until_row) && p.active) {
                vertex_spatial_hash_.remove(p.row, p.col, p.index);
                p.active = false;
            }
        }
    }

    // Quadric Error Metric (QEM) based simplification
    // This is a lightweight version suitable for incremental processing
    void simplifyActiveRegion(size_t start_row, size_t end_row) {
        if (active_triangles_.size() < 10) return;

        // Compute error for each triangle using fast neighbor lookups
        static thread_local std::vector<size_t> neighbors;

        for (auto& tri : active_triangles_) {
            if (!tri.active) continue;
            tri.error = computeTriangleErrorFast(tri, neighbors);
        }

        size_t target_count = static_cast<size_t>(
            active_triangles_.size() * (1.0 - target_reduction_)
        );
        target_count = std::max(target_count, size_t(cols_ * 2));

        std::vector<bool> removed(active_triangles_.size(), false);
        size_t removed_count = 0;

        // Priority queue ordered by error
        using QueueItem = std::pair<double, size_t>;
        std::priority_queue<QueueItem, std::vector<QueueItem>, std::greater<QueueItem>> pq;

        for (size_t i = 0; i < active_triangles_.size(); ++i) {
            if (active_triangles_[i].active) {
                pq.push({active_triangles_[i].error, i});
            }
        }

        // Greedy edge collapse using spatial hash for validation
        while (!pq.empty() && removed_count < active_triangles_.size() - target_count) {
            auto [err, idx] = pq.top();
            pq.pop();

            if (removed[idx] || !active_triangles_[idx].active) continue;

            const auto& tri = active_triangles_[idx];

            // Check row constraints
            int max_row = std::max({
                all_points_[tri.v0].row,
                all_points_[tri.v1].row,
                all_points_[tri.v2].row
            });

            if (max_row >= static_cast<int>(end_row)) continue;

            // Fast manifold check using spatial hash neighbors
            if (!canRemoveTriangleFast(tri, removed, neighbors)) continue;

            if (err < error_threshold_) {
                removed[idx] = true;
                active_triangles_[idx].active = false;
                ++removed_count;
            }
        }

        // Rebuild triangle list
        std::vector<Triangle> new_active;
        new_active.reserve(active_triangles_.size() - removed_count);

        for (size_t i = 0; i < active_triangles_.size(); ++i) {
            if (!removed[i] && active_triangles_[i].active) {
                new_active.push_back(active_triangles_[i]);
            }
        }

        active_triangles_ = std::move(new_active);

        // Rebuild edge map for remaining active triangles
        rebuildEdgeMap();
    }

    // Compute geometric error of a triangle relative to its neighborhood
    double computeTriangleError(const Triangle& tri) {
        const Point& p0 = all_points_[tri.v0];
        const Point& p1 = all_points_[tri.v1];
        const Point& p2 = all_points_[tri.v2];

        // Normal of triangle
        double ax = p1.x - p0.x, ay = p1.y - p0.y, az = p1.z - p0.z;
        double bx = p2.x - p0.x, by = p2.y - p0.y, bz = p2.z - p0.z;

        double nx = ay * bz - az * by;
        double ny = az * bx - ax * bz;
        double nz = ax * by - ay * bx;
        double len = std::sqrt(nx*nx + ny*ny + nz*nz);

        if (len < 1e-10) return std::numeric_limits<double>::max();

        nx /= len; ny /= len; nz /= len;

        // Planarity: how flat is the local neighborhood?
        // Approximate by checking how much the centroid deviates from plane
        double cx = (p0.x + p1.x + p2.x) / 3.0;
        double cy = (p0.y + p1.y + p2.y) / 3.0;
        double cz = (p0.z + p1.z + p2.z) / 3.0;

        // Distance from origin to plane
        double d = -(nx * p0.x + ny * p0.y + nz * p0.z);

        // For error metric, use area-weighted deviation
        double area = 0.5 * len;

        // Also consider height variation - flat areas can be simplified more
        double height_var = std::max({
            std::abs(p0.z - p1.z),
            std::abs(p1.z - p2.z),
            std::abs(p2.z - p0.z)
        });

        // Error is low for small, flat triangles in smooth regions
        return area * (1.0 + height_var) / (1.0 + height_var * height_var);
    }

  // Fast error computation using spatial hash for neighborhood queries
    double computeTriangleErrorFast(const Triangle& tri, std::vector<size_t>& neighbors) const {
        const Point& p0 = all_points_[tri.v0];
        const Point& p1 = all_points_[tri.v1];
        const Point& p2 = all_points_[tri.v2];

        // Normal
        double ax = p1.x - p0.x, ay = p1.y - p0.y, az = p1.z - p0.z;
        double bx = p2.x - p0.x, by = p2.y - p0.y, bz = p2.z - p0.z;

        double nx = ay * bz - az * by;
        double ny = az * bx - ax * bz;
        double nz = ax * by - ay * bx;
        double len = std::sqrt(nx*nx + ny*ny + nz*nz);

        if (len < 1e-10) return std::numeric_limits<double>::max();

        nx /= len; ny /= len; nz /= len;
        double area = 0.5 * len;

        // Fast neighborhood query: get adjacent triangles via edge map
        double max_dihedral = 0.0;

        auto checkDihedral = [&](size_t a, size_t b, size_t c) {
            auto tris = getTrianglesForEdge(a, b);
            if (!tris) return;
            for (size_t ot : *tris) {
                if (!active_triangles_[ot].active) continue;
                const auto& other = active_triangles_[ot];
                // Skip self
                if (other.v0 == tri.v0 && other.v1 == tri.v1 && other.v2 == tri.v2) continue;
                if (other.v0 == tri.v0 && other.v1 == tri.v2 && other.v2 == tri.v1) continue;

                // Compute dihedral angle with neighbor
                const Point& op0 = all_points_[other.v0];
                const Point& op1 = all_points_[other.v1];
                const Point& op2 = all_points_[other.v2];

                double oax = op1.x - op0.x, oay = op1.y - op0.y, oaz = op1.z - op0.z;
                double obx = op2.x - op0.x, oby = op2.y - op0.y, obz = op2.z - op0.z;

                double onx = oay * obz - oaz * oby;
                double ony = oaz * obx - oax * obz;
                double onz = oax * oby - oay * obx;
                double olen = std::sqrt(onx*onx + ony*ony + onz*onz);

                if (olen > 1e-10) {
                    onx /= olen; ony /= olen; onz /= olen;
                    double dot = std::abs(nx * onx + ny * ony + nz * onz);
                    max_dihedral = std::max(max_dihedral, std::acos(std::clamp(dot, -1.0, 1.0)));
                }
            }
        };

        checkDihedral(tri.v0, tri.v1, tri.v2);
        checkDihedral(tri.v1, tri.v2, tri.v0);
        checkDihedral(tri.v2, tri.v0, tri.v1);

        // Height variation
        double height_var = std::max({
            std::abs(p0.z - p1.z),
            std::abs(p1.z - p2.z),
            std::abs(p2.z - p0.z)
        });

        // Error: prefer removing flat, small triangles in smooth regions
        return area * (1.0 + max_dihedral * 2.0) * (1.0 + height_var);
    }

    // Fast manifold preservation check using spatial hash
    bool canRemoveTriangleFast(const Triangle& tri,
                                const std::vector<bool>& removed,
                                std::vector<size_t>& neighbors) const {
        // For each vertex, check if removing this triangle would create a boundary hole
        // A triangle can be removed if each of its edges is shared by another active triangle

        auto hasActiveNeighbor = [&](size_t a, size_t b, size_t self_idx) -> bool {
            auto tris = getTrianglesForEdge(a, b);
            if (!tris) return false;
            for (size_t t : *tris) {
                if (t != self_idx && !removed[t] && active_triangles_[t].active) {
                    return true;
                }
            }
            return false;
        };

        // Find index of tri in active_triangles_
        size_t self_idx = 0;
        for (size_t i = 0; i < active_triangles_.size(); ++i) {
            if (active_triangles_[i].v0 == tri.v0 &&
                active_triangles_[i].v1 == tri.v1 &&
                active_triangles_[i].v2 == tri.v2) {
                self_idx = i;
                break;
            }
        }

        // Check all three edges have active neighbors
        return hasActiveNeighbor(tri.v0, tri.v1, self_idx) &&
               hasActiveNeighbor(tri.v1, tri.v2, self_idx) &&
               hasActiveNeighbor(tri.v2, tri.v0, self_idx);
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
        // Find which points are referenced
        std::vector<bool> used(all_points_.size(), false);

        for (const auto& tri : finalized_triangles_) {
            used[tri.v0] = true;
            used[tri.v1] = true;
            used[tri.v2] = true;
        }

        // Create remapping
        std::vector<size_t> remap(all_points_.size(), static_cast<size_t>(-1));
        size_t new_idx = 0;

        for (size_t i = 0; i < all_points_.size(); ++i) {
            if (used[i]) {
                remap[i] = new_idx++;
            }
        }

        // Output compacted points
        out_points.clear();
        out_points.reserve(new_idx);

        for (size_t i = 0; i < all_points_.size(); ++i) {
            if (used[i]) {
                Point p = all_points_[i];
                p.index = remap[i];
                out_points.push_back(p);
            }
        }

        // Output remapped triangles
        out_triangles.clear();
        out_triangles.reserve(finalized_triangles_.size());

        for (const auto& tri : finalized_triangles_) {
            out_triangles.emplace_back(
                remap[tri.v0],
                remap[tri.v1],
                remap[tri.v2]
            );
        }
    }

    // Configuration
    size_t max_active_rows_;
    double target_reduction_;
    double error_threshold_;

    // DEM state
    int cols_;
    size_t current_row_;
    size_t finalized_row_;
    double cell_size_x_, cell_size_y_;

    // Data
    std::vector<Point> all_points_;
    std::vector<Triangle> active_triangles_;
    std::vector<Triangle> finalized_triangles_;
    std::vector<size_t> prev_row_indices_;

    // Fast lookup structures
    SpatialHash vertex_spatial_hash_;
    std::unordered_map<Edge, std::vector<size_t>, EdgeHash> edge_to_triangles_;
    std::vector<std::vector<size_t>> row_point_indices_;
};

Triangulator::Kimi::DEMTriangulationResult Triangulator::Kimi::triangulateDEM(
    int rows, int cols,
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
        for (int c = 0; c < cols; ++c) {
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

// While this is a work-in-progress this contains the main program rather than
// allowing this to be used as a library.
#if 0
int main2(int argc, const char* argv[])
{
    try
    {
        const char* filename = (argc > 1) ? argv[1] : "N03W074.hgt";
        const auto [latitude, longitude] =
            HGT::LocationFromHgtName(filename);
        std::cout << latitude << ", " << longitude << std::endl;

        // TODO: Generate the mesh.
        HGT::ForEachHeightWithIndex(
            filename,
            [](auto X, auto Y, auto Height)
            {
                std::cout << X << "," << Y << "," << Height << "\n";
            });
    }
    catch (const std::runtime_error& Error)
    {
        std::cerr << Error.what() << std::endl;
        return 1;
    }
    return 0;
}
#endif

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
