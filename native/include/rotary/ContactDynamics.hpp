#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>
namespace rotary {
struct ContactHistory {
    std::array<double, 5> value{};
};
struct MotionContext {
    std::unordered_map<std::int64_t, ContactHistory> history;
    std::string error;
};
std::array<double, 4> wall_distance(double x, double y, double z, double R, double L, double h, int heads);
void integrate_contacts(MotionContext &context, double *particles, std::size_t count, double radius,
                        const double *geometry, int steps, double dt, double omega, int iterations,
                        int position_iterations, double gravity, std::int64_t first_iteration, bool rigid,
                        double *metrics);
void initialize_lattice(double *particles, std::size_t count, double radius, const double *geometry);
double liquid_plane(const double *particles, std::size_t count, double radius, const double *geometry,
                    double volume);
} // namespace rotary
