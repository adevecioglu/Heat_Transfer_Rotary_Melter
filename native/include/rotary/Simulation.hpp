#pragma once
#include "Geometry.hpp"
#include <functional>
#include <string>

namespace rotary {
struct SimulationOptions {
    std::string integrator = "midpoint";
    std::string water_model = "constant";
    double relative_tolerance = 1e-7, absolute_tolerance = 1e-8;
    double wall_time_limit = 900;
    int threads = 1;
    bool no_history = false, parallel_kernel = false;
    static SimulationOptions from_json(const Json &data);
};
using Progress = std::function<void(const Json &)>;
using Cancel = std::function<bool()>;

Json simulate(Configuration configuration, const SimulationOptions &options = {}, Progress progress = {},
              Cancel cancelled = {});
Json analyse(const Json &request, Progress progress = {}, Cancel cancelled = {});
Json backend_info();
Json execute(const Json &request, Progress progress = {}, Cancel cancelled = {});
} // namespace rotary
