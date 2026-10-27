#include "rotary/Api.h"
#include "rotary/ContactDynamics.hpp"
#include <cmath>
#include <exception>
#include <stdexcept>
namespace {
template <class F> int guarded(void *handle, F work) {
    if (!handle)
        return 0;
    auto &context = *static_cast<rotary::MotionContext *>(handle);
    try {
        context.error.clear();
        work(context);
        return 1;
    } catch (const std::exception &error) {
        context.error = error.what();
        return 0;
    } catch (...) {
        context.error = "Unknown native contact failure";
        return 0;
    }
}
void validate(const double *p, unsigned long long n, double r, const double *g) {
    if (!p || !g || !n || n > 2000000 || !std::isfinite(r) || r <= 0)
        throw std::invalid_argument("Invalid contact array/count/radius");
    for (int i = 0; i < 16; ++i)
        if (!std::isfinite(g[i]))
            throw std::invalid_argument("Non-finite contact geometry");
    if (g[0] <= r || g[1] <= 0 || g[2] < 0 || g[3] < 0 || g[3] > 2)
        throw std::invalid_argument("Invalid vessel dimensions");
    for (unsigned long long i = 0; i < 12 * n; ++i)
        if (!std::isfinite(p[i]))
            throw std::invalid_argument("Non-finite initial particle state");
}
} // namespace
extern "C" {
void *rotary_motion_create() {
    try {
        return new rotary::MotionContext;
    } catch (...) {
        return nullptr;
    }
}
void rotary_motion_destroy(void *context) {
    delete static_cast<rotary::MotionContext *>(context);
}
const char *rotary_motion_error(void *context) {
    return context ? static_cast<rotary::MotionContext *>(context)->error.c_str() : "No motion context";
}
unsigned long long rotary_motion_history_size(void *context) {
    return context ? static_cast<rotary::MotionContext *>(context)->history.size() : 0;
}
int rotary_motion_lattice(void *context, double *p, unsigned long long n, double r, const double *g) {
    return guarded(context, [&](auto &) {
        validate(p, n, r, g);
        rotary::initialize_lattice(p, n, r, g);
    });
}
int rotary_motion_advance(void *context, double *p, unsigned long long n, double r, const double *g,
                          int steps, double dt, double omega, int iterations, int position_iterations,
                          double gravity, long long first_iteration, int rigid, double *metrics) {
    return guarded(context, [&](auto &state) {
        validate(p, n, r, g);
        if (!metrics || steps < 0 || steps > 100000 || iterations < 1 || iterations > 2048 ||
            position_iterations < 1 || position_iterations > 512 || !std::isfinite(dt) || dt <= 0 ||
            !std::isfinite(omega) || !std::isfinite(gravity))
            throw std::invalid_argument("Invalid contact step/options");
        rotary::integrate_contacts(state, p, n, r, g, steps, dt, omega, iterations, position_iterations,
                                   gravity, first_iteration, rigid != 0, metrics);
    });
}
int rotary_motion_liquid_plane(void *context, const double *p, unsigned long long n, double r,
                               const double *g, double volume, double *result) {
    return guarded(context, [&](auto &) {
        validate(p, n, r, g);
        if (!result || !std::isfinite(volume) || volume < 0)
            throw std::invalid_argument("Invalid liquid volume");
        *result = rotary::liquid_plane(p, n, r, g, volume);
    });
}
}
