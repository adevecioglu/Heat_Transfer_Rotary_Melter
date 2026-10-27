#include "rotary/ContactDynamics.hpp"
#include <Eigen/Geometry>
#include <algorithm>
#include <boost/math/tools/toms748_solve.hpp>
#include <cmath>
#include <numbers>
#include <stdexcept>
namespace rotary {
namespace {
using Vec = Eigen::Vector3d;
constexpr double pi = std::numbers::pi;
Vec position(const double *p, std::size_t i) {
    return Eigen::Map<const Vec>(p + 12 * i);
}
Vec velocity(const double *p, std::size_t i) {
    return Eigen::Map<const Vec>(p + 12 * i + 3);
}
Vec spin(const double *p, std::size_t i) {
    return Eigen::Map<const Vec>(p + 12 * i + 6);
}
void add(double *p, std::size_t i, int offset, const Vec &v) {
    Eigen::Map<Vec>(p + 12 * i + offset) += v;
}
double square(double x) {
    return x * x;
}
struct Pair {
    int i, j;
};
std::vector<Pair> candidates(const double *p, std::size_t count, double r, const double *g) {
    const double cell = 2.25 * r;
    const int nx = int(std::ceil(2 * g[0] / cell)) + 5, ny = nx,
              nz = int(std::ceil((g[1] + 2 * g[2]) / cell)) + 7;
    const std::size_t size = std::size_t(nx) * ny * nz;
    if (size > 100000000)
        throw std::invalid_argument("Contact bin budget exceeded; revise particle size");
    std::vector<int> bins(size, -1), next(count);
    std::vector<std::array<int, 3>> coords(count);
    for (std::size_t i = 0; i < count; ++i) {
        auto &c = coords[i];
        c = {std::clamp(int(std::floor((p[12 * i] + g[0]) / cell)) + 2, 1, nx - 2),
             std::clamp(int(std::floor((p[12 * i + 1] + g[0]) / cell)) + 2, 1, ny - 2),
             std::clamp(int(std::floor((p[12 * i + 2] + g[2]) / cell)) + 2, 1, nz - 2)};
        const auto k = c[0] + nx * (c[1] + ny * c[2]);
        next[i] = bins[k];
        bins[k] = int(i);
    }
    std::vector<Pair> pairs;
    pairs.reserve(count * 12);
    // Contact updates sharing a particle are dependent: preserve traversal.
    for (std::size_t i = 0; i < count; ++i)
        for (int dz = -1; dz <= 1; ++dz)
            for (int dy = -1; dy <= 1; ++dy)
                for (int dx = -1; dx <= 1; ++dx) {
                    const auto &c = coords[i];
                    int j = bins[c[0] + dx + nx * (c[1] + dy + ny * (c[2] + dz))];
                    while (j >= 0) {
                        if (j > int(i) && (position(p, i) - position(p, j)).squaredNorm() < cell * cell)
                            pairs.push_back({int(i), j});
                        j = next[j];
                    }
                }
    return pairs;
}
Vec relative(const double *p, int i, int j, const Vec &n, double r, double omega) {
    Vec v = velocity(p, i), w = spin(p, i);
    if (j >= 0) {
        v -= velocity(p, j);
        w += spin(p, j);
    } else {
        v[0] += omega * (p[12 * i + 1] - r * n[1]);
        v[1] -= omega * (p[12 * i] - r * n[0]);
    }
    return v - r * w.cross(n);
}
void impulse(double *p, int i, int j, const Vec &n, const Vec &value, double r) {
    add(p, i, 3, value);
    const Vec angular = (-2.5 / r) * n.cross(value);
    add(p, i, 6, angular);
    if (j >= 0) {
        add(p, j, 3, -value);
        add(p, j, 6, angular);
    }
}
struct Constraint {
    int i, j;
    Vec n;
    double target, mu;
    std::int64_t key;
    double normal = 0;
    Vec tangent = Vec::Zero();
};
void rigid_step(MotionContext &context, double *p, std::size_t count, double r, const double *g, double dt,
                double omega, int iterations, int position_iterations, double gravity, std::int64_t stamp,
                double *metrics) {
    const double buoy = g[12] * g[15], drag = g[13] * g[12];
    for (std::size_t i = 0; i < count; ++i) {
        add(p, i, 3,
            dt * Vec(drag * (-omega * g[14] * p[12 * i + 1] - p[12 * i + 3]),
                     -gravity * g[5] * (1 - buoy) + drag * (omega * g[14] * p[12 * i] - p[12 * i + 4]),
                     -gravity * g[4] * (1 - buoy) - drag * p[12 * i + 5]));
    }
    const auto pairs = candidates(p, count, r, g);
    std::vector<Constraint> constraints;
    constraints.reserve(pairs.size() + count);
    metrics[0] = metrics[1] = 0;
    auto append = [&](int i, int j, const Vec &n, double separation, double mu, std::int64_t key) {
        const double vn = relative(p, i, j, n, r, omega).dot(n);
        if (separation > std::max(.02 * r, -vn * dt))
            return;
        double target = .2 * std::max(-separation - .0002 * r, 0.) / dt - std::max(separation, 0.) / dt;
        if (separation < .002 * r && vn < -.15)
            target = std::max(target, -g[9] * vn);
        constraints.push_back({i, j, n, target, mu, key});
        ++metrics[j >= 0 ? 0 : 1];
    };
    for (const auto &pair : pairs) {
        const Vec delta = position(p, pair.i) - position(p, pair.j);
        const double d = delta.norm();
        if (d > 1e-20)
            append(pair.i, pair.j, delta / d, d - 2 * r, g[8], std::int64_t(pair.i) * count + pair.j);
    }
    for (std::size_t i = 0; i < count; ++i) {
        const auto w = wall_distance(p[12 * i], p[12 * i + 1], p[12 * i + 2], g[0], g[1], g[2], int(g[3]));
        append(int(i), -1, -Vec(w[1], w[2], w[3]), w[0] - r, g[7], std::int64_t(count) * count + i);
    }
    for (auto &c : constraints) {
        const auto it = context.history.find(c.key);
        if (it == context.history.end())
            continue;
        const auto &old = it->second.value;
        if (old[4] != stamp - 1)
            continue;
        const Vec tangent(old[1], old[2], old[3]);
        c.normal = old[0];
        c.tangent = tangent - tangent.dot(c.n) * c.n;
        impulse(p, c.i, c.j, c.n, c.normal * c.n + c.tangent, r);
    }
    for (int sweep = 0; sweep < iterations; ++sweep)
        for (std::size_t it = 0; it < constraints.size(); ++it) {
            auto &c = constraints[sweep % 2 == 0 ? it : constraints.size() - 1 - it];
            const Vec v = relative(p, c.i, c.j, c.n, r, omega);
            const double vn = v.dot(c.n), old = c.normal;
            c.normal = std::max(0., old + (c.target - vn) / (c.j >= 0 ? 2. : 1.));
            Vec tangent = c.tangent - (v - vn * c.n) / (c.j >= 0 ? 7. : 3.5);
            const double magnitude = tangent.norm(), limit = c.mu * c.normal;
            if (magnitude > limit && magnitude > 0)
                tangent *= limit / magnitude;
            impulse(p, c.i, c.j, c.n, (c.normal - old) * c.n + tangent - c.tangent, r);
            c.tangent = tangent;
        }
    for (const auto &c : constraints)
        context.history[c.key] = {{c.normal, c.tangent[0], c.tangent[1], c.tangent[2], double(stamp)}};
    if (stamp % 25 == 0)
        std::erase_if(context.history, [&](const auto &item) { return item.second.value[4] < stamp - 1; });
    for (std::size_t i = 0; i < count; ++i) {
        add(p, i, 0, dt * velocity(p, i));
        add(p, i, 9, dt * spin(p, i));
    }
    for (int sweep = 0; sweep < position_iterations; ++sweep) {
        for (const auto &pair : pairs) {
            const Vec delta = position(p, pair.i) - position(p, pair.j);
            const double d = delta.norm(), over = 2 * r - d;
            if (over > .0002 * r && d > 1e-20) {
                const Vec correction = .4 * (over - .0002 * r) / d * delta;
                add(p, pair.i, 0, correction);
                add(p, pair.j, 0, -correction);
            }
        }
        for (std::size_t i = 0; i < count; ++i) {
            const auto w =
                wall_distance(p[12 * i], p[12 * i + 1], p[12 * i + 2], g[0], g[1], g[2], int(g[3]));
            const double over = r - w[0];
            if (over > .0002 * r)
                add(p, i, 0, -.8 * (over - .0002 * r) * Vec(w[1], w[2], w[3]));
        }
    }
    for (const auto &pair : pairs)
        metrics[2] = std::max(metrics[2], (2 * r - (position(p, pair.i) - position(p, pair.j)).norm()) / r);
    for (std::size_t i = 0; i < count; ++i) {
        const auto w = wall_distance(p[12 * i], p[12 * i + 1], p[12 * i + 2], g[0], g[1], g[2], int(g[3]));
        metrics[2] = std::max(metrics[2], (r - w[0]) / r);
        if (w[0] < -r)
            ++metrics[3];
    }
}
void compliant_step(MotionContext &context, double *p, std::size_t count, double r, const double *g,
                    double dt, double omega, double gravity, std::int64_t stamp, double *metrics) {
    const auto pairs = candidates(p, count, r, g);
    std::vector<Vec> force(count, Vec::Zero()), torque(count, Vec::Zero());
    const double loge = std::log(std::clamp(g[9], .01, .99)), zeta = -loge / std::sqrt(pi * pi + loge * loge);
    const double gamma = 2 * zeta * std::sqrt(g[6]), gp = gamma / std::sqrt(2.), kt = g[10] * g[6];
    std::fill(metrics, metrics + 3, 0.);
    for (std::size_t i = 0; i < count; ++i)
        force[i] = Vec(g[12] * g[13] * (-omega * g[14] * p[12 * i + 1] - p[12 * i + 3]),
                       -gravity * g[5] * (1 - g[12] * g[15]) +
                           g[12] * g[13] * (omega * g[14] * p[12 * i] - p[12 * i + 4]),
                       -gravity * g[4] * (1 - g[12] * g[15]) - g[12] * g[13] * p[12 * i + 5]);
    auto friction = [&](std::int64_t key, const Vec &n, const Vec &tangent, double damping, double limit) {
        Vec displacement = Vec::Zero();
        const auto it = context.history.find(key);
        if (it != context.history.end() && it->second.value[3] >= stamp - 1) {
            const auto &h = it->second.value;
            displacement = Vec(h[0], h[1], h[2]);
        }
        displacement -= displacement.dot(n) * n;
        displacement += tangent * dt;
        Vec value = -kt * displacement - damping * tangent;
        const double magnitude = value.norm();
        if (magnitude > limit && magnitude > 0) {
            value *= limit / magnitude;
            if (kt > 0)
                displacement = -(value + damping * tangent) / kt;
        }
        context.history[key] = {{displacement[0], displacement[1], displacement[2], double(stamp), 0}};
        return value;
    };
    for (const auto &pair : pairs) {
        const int i = pair.i, j = pair.j;
        const Vec delta = position(p, i) - position(p, j);
        const double d2 = delta.squaredNorm();
        if (d2 <= 1e-24 || d2 >= 4 * r * r)
            continue;
        const double d = std::sqrt(d2), over = 2 * r - d;
        const Vec n = delta / d;
        const Vec v = velocity(p, i) - velocity(p, j) - r * (spin(p, i) + spin(p, j)).cross(n);
        const double vn = v.dot(n), fn = std::max(0., g[6] * over - gp * vn);
        const Vec ft = friction(std::int64_t(i) * count + j, n, v - vn * n, gp, g[8] * fn), f = fn * n + ft;
        force[i] += f;
        force[j] -= f;
        const Vec t = (-2.5 / r) * n.cross(ft);
        torque[i] += t;
        torque[j] += t;
        ++metrics[0];
        metrics[2] = std::max(metrics[2], over / r);
    }
    for (std::size_t i = 0; i < count; ++i) {
        const auto w = wall_distance(p[12 * i], p[12 * i + 1], p[12 * i + 2], g[0], g[1], g[2], int(g[3]));
        const Vec n(w[1], w[2], w[3]);
        const double over = r - w[0];
        if (over > 0) {
            Vec v = velocity(p, i) + r * spin(p, i).cross(n);
            v[0] += omega * (p[12 * i + 1] + w[0] * n[1]);
            v[1] -= omega * (p[12 * i] + w[0] * n[0]);
            const double vn = v.dot(n), fn = std::max(0., g[6] * over + gamma * vn);
            const Vec ft = friction(-std::int64_t(i) - 1, n, v - vn * n, gamma, g[7] * fn);
            force[i] += -fn * n + ft;
            torque[i] += (2.5 / r) * n.cross(ft);
            const double magnitude = spin(p, i).norm();
            if (magnitude > 0)
                torque[i] -= std::min(g[11] * fn * 2.5 / r / magnitude, 1 / dt) * spin(p, i);
            ++metrics[1];
            metrics[2] = std::max(metrics[2], over / r);
        }
        add(p, i, 3, dt * force[i]);
        add(p, i, 6, dt * torque[i]);
        add(p, i, 0, dt * velocity(p, i));
        add(p, i, 9, dt * spin(p, i));
        if (wall_distance(p[12 * i], p[12 * i + 1], p[12 * i + 2], g[0], g[1], g[2], int(g[3]))[0] < -r)
            ++metrics[3];
    }
    if ((stamp + 1) % 25 == 0)
        std::erase_if(context.history, [&](const auto &item) { return item.second.value[3] < stamp; });
}
} // namespace

std::array<double, 4> wall_distance(double x, double y, double z, double R, double L, double h, int heads) {
    const double rho = std::hypot(x, y), rs = h > 0 ? (R * R + h * h) / (2 * h) : R;
    double bz = std::clamp(z, 0., L), br = R, best = square(rho - br) + square(z - bz);
    auto consider = [&](double rr, double zz) {
        const double q = square(rho - rr) + square(z - zz);
        if (q < best) {
            best = q;
            br = rr;
            bz = zz;
        }
    };
    if (heads > 0) {
        const double center = rs - h, dz = z - center, d = std::hypot(rho, dz);
        double zz = center + rs * dz / std::max(d, 1e-30), rr;
        if (zz <= 0)
            rr = rs * rho / std::max(d, 1e-30);
        else {
            zz = 0;
            rr = R;
        }
        consider(rr, zz);
    } else
        consider(std::min(R, rho), 0);
    if (heads == 2) {
        const double center = L - rs + h, dz = z - center, d = std::hypot(rho, dz);
        double zz = center + rs * dz / std::max(d, 1e-30), rr;
        if (zz >= L)
            rr = rs * rho / std::max(d, 1e-30);
        else {
            zz = L;
            rr = R;
        }
        consider(rr, zz);
    } else
        consider(std::min(R, rho), L);
    const double lower = heads ? -h : 0, upper = heads == 2 ? L + h : L;
    double radial = R;
    if (z < 0 && heads > 0)
        radial = std::sqrt(std::max(0., rs * rs - square(z - (rs - h))));
    if (z > L && heads == 2)
        radial = std::sqrt(std::max(0., rs * rs - square(z - (L - rs + h))));
    const bool inside = lower <= z && z <= upper && rho <= radial;
    const double d = std::sqrt(best), fac = inside ? 1. : -1.;
    if (d < 1e-20)
        return {0, x / std::max(rho, 1e-30), y / std::max(rho, 1e-30), 0};
    return {fac * d, rho < 1e-15 ? 0 : fac * (br - rho) / d * x / std::max(rho, 1e-30),
            rho < 1e-15 ? 0 : fac * (br - rho) / d * y / std::max(rho, 1e-30), fac * (bz - z) / d};
}
void initialize_lattice(double *p, std::size_t count, double r, const double *g) {
    const double a = 2 * std::sqrt(2.) * r * 1.025, R = g[0], L = g[1], h = g[2], lo = g[3] > 0 ? -h : 0,
                 hi = g[3] == 2 ? L + h : L;
    const std::array<Vec, 4> basis = {Vec(0, 0, 0), Vec(0, .5, .5), Vec(.5, 0, .5), Vec(.5, .5, 0)};
    const long double nx = std::ceil(2 * R / a) + 5, nz = std::ceil((hi - lo) / a) + 5;
    if (4 * nx * nx * nz > 10000000)
        throw std::invalid_argument(
            "FCC candidate allocation budget exceeded; revise particle size/phase initialization");
    std::vector<std::pair<double, Vec>> points;
    for (int iz = int(std::floor(lo / a)) - 1; iz <= int(std::ceil(hi / a)); ++iz)
        for (int iy = int(std::floor(-R / a)) - 1; iy <= int(std::ceil(R / a)); ++iy)
            for (int ix = int(std::floor(-R / a)) - 1; ix <= int(std::ceil(R / a)); ++ix)
                for (const Vec &b : basis) {
                    const Vec q = a * (Vec(ix, iy, iz) + b);
                    if (wall_distance(q[0], q[1], q[2], R, L, h, int(g[3]))[0] > r * 1.005)
                        points.emplace_back(q[1] * g[5] + q[2] * g[4], q);
                }
    if (points.size() < count)
        throw std::invalid_argument(
            "Physical spheres cannot be packed into the assumed vessel; revise charge/packing/geometry");
    // Explicit tie ordering; V11's quicksort did not specify ties.
    std::stable_sort(points.begin(), points.end(),
                     [](const auto &x, const auto &y) { return x.first < y.first; });
    std::fill(p, p + 12 * count, 0.);
    for (std::size_t i = 0; i < count; ++i)
        add(p, i, 0, points[i].second);
}
double liquid_plane(const double *p, std::size_t count, double r, const double *g, double volume) {
    const double R = g[0], L = g[1], h = g[2], st = g[4], ct = g[5], lo = -h - R, hi = L + h + R;
    if (volume <= 0)
        return lo;
    auto void_volume = [&](double H) {
        const double rs = h > 0 ? (R * R + h * h) / (2 * h) : R, lower = g[3] > 0 ? -h : 0,
                     upper = g[3] == 2 ? L + h : L, dz = (upper - lower) / 600;
        double total = 0;
        for (int j = 0; j < 600; ++j) {
            const double z = lower + (j + .5) * dz;
            double radius = R;
            if (z < 0)
                radius = std::sqrt(std::max(0., rs * rs - square(z - (rs - h))));
            if (z > L)
                radius = std::sqrt(std::max(0., rs * rs - square(z - (L - rs + h))));
            const double u = (H - z * st) / std::max(1e-30, radius * ct);
            const double f = ct < 1e-12 ? (H >= z * st ? 1. : 0.)
                             : u <= -1  ? 0.
                             : u >= 1   ? 1.
                                        : .5 + (std::asin(u) + u * std::sqrt(1 - u * u)) / pi;
            total += pi * radius * radius * dz * f;
        }
        for (std::size_t i = 0; i < count; ++i) {
            const double cap = std::clamp(H - (p[12 * i + 1] * ct + p[12 * i + 2] * st) + r, 0., 2 * r);
            total -= pi * cap * cap * (r - cap / 3);
        }
        return std::max(0., total) - volume;
    };
    if (void_volume(hi) < 0)
        throw std::invalid_argument("Liquid volume exceeds available void space");
    boost::uintmax_t evaluations = 80;
    const auto bracket = boost::math::tools::toms748_solve(
        void_volume, lo, hi, boost::math::tools::eps_tolerance<double>(38), evaluations);
    return (bracket.first + bracket.second) / 2;
}
void integrate_contacts(MotionContext &context, double *p, std::size_t count, double r, const double *g,
                        int steps, double dt, double omega, int iterations, int position_iterations,
                        double gravity, std::int64_t first_iteration, bool rigid, double *metrics) {
    std::fill(metrics, metrics + 4, 0.);
    for (int step = 0; step < steps; ++step) {
        if (rigid)
            rigid_step(context, p, count, r, g, dt, omega, iterations, position_iterations, gravity,
                       first_iteration + step, metrics);
        else
            compliant_step(context, p, count, r, g, dt, omega, gravity, first_iteration + step, metrics);
    }
    for (std::size_t i = 0; i < 12 * count; ++i)
        if (!std::isfinite(p[i]))
            throw std::runtime_error("Non-finite contact state rejected");
}
} // namespace rotary
