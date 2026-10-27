# Measured C++ regression and analyses

Date (UTC): 2026-10-27T03:31:50.906030+00:00

Platform: Windows-10-10.0.26200-SP0. Compiler: 16.2.0.

Wall times include per-call adapter overhead. These are single-run fixture measurements, not general performance guarantees or experimental validation.

| Fixture | Physical time (s) | Input (kWh) | Maximum scaled difference | Energy residual | JS wall (s) | C++ wall (s) | Ratio | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| cold_default | 5329.919006 | 14.53424977 | 1.22e-15 | 8.61e-15 | 7.6067 | 1.5595 | 4.878 | True |
| limited_source | 108 | 0.1425 | 9.71e-17 | 3.82e-14 | 0.32114 | 0.031569 | 10.17 | True |
| warm_start | 36 | 2.296969841 | 0 | 2.93e-15 | 0.22239 | 0.011492 | 19.35 | True |
| two_heads | 72 | 6.831979662 | 1.25e-16 | 3.18e-15 | 0.28285 | 0.022271 | 12.7 | True |
| flat_ends | 72 | 5.301105871 | 1.94e-16 | 5.76e-15 | 0.25881 | 0.021351 | 12.12 | True |
| insulated | 72 | 6.06270342 | 4.59e-14 | 8.53e-17 | 0.92417 | 0.11844 | 7.803 | True |
| reverse_rotation | 72 | 6.075373287 | 3.89e-16 | 7.66e-16 | 0.26246 | 0.022393 | 11.72 | True |

Scaled difference is `abs(C++ − V11) / max(1, abs(V11))`, so it is an absolute difference below unit scale. Target status is also checked. The requested input for every fixture is retained in the adjacent JSON.

## Analysis execution

- convergence: 5 cases; 21.8884 wall seconds; all numerical energy checks passed: True.
- sensitivity: 9 cases; 4.52755 wall seconds; all numerical energy checks passed: True.

[Formula catalogue](CPP_CALCULATION_EQUATIONS.md). Independent numerical agreement does not establish real melting performance.
