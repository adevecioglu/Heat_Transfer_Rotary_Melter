#pragma once
#ifdef _WIN32
#ifdef ROTARY_NATIVE_BUILD
#define ROTARY_API __declspec(dllexport)
#else
#define ROTARY_API __declspec(dllimport)
#endif
#else
#define ROTARY_API __attribute__((visibility("default")))
#endif
#ifdef __cplusplus
extern "C" {
#endif
typedef void (*rotary_progress_callback)(const char *event_json, void *context);
typedef int (*rotary_cancel_callback)(void *context);
ROTARY_API const char *rotary_execute_json(const char *request_json, rotary_progress_callback progress,
                                           rotary_cancel_callback cancel, void *context);
ROTARY_API void rotary_free_json(const char *response_json);
ROTARY_API unsigned rotary_abi_version(void);
/* Each context belongs to one caller/thread; particle rows contain 12 doubles
   (position, velocity, spin, orientation). Arrays remain caller-owned. */
ROTARY_API void *rotary_motion_create(void);
ROTARY_API void rotary_motion_destroy(void *context);
ROTARY_API const char *rotary_motion_error(void *context);
ROTARY_API unsigned long long rotary_motion_history_size(void *context);
ROTARY_API int rotary_motion_lattice(void *context, double *particles, unsigned long long count,
                                     double radius, const double *geometry);
ROTARY_API int rotary_motion_advance(void *context, double *particles, unsigned long long count,
                                     double radius, const double *geometry, int steps, double dt,
                                     double omega, int iterations, int position_iterations, double gravity,
                                     long long first_iteration, int rigid, double *metrics);
ROTARY_API int rotary_motion_liquid_plane(void *context, const double *particles, unsigned long long count,
                                          double radius, const double *geometry, double volume,
                                          double *result);
#ifdef __cplusplus
}
#endif
