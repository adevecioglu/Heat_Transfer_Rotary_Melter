# C++ workstation development

Run from `C:\Projects\Heat_Transfer_Rotary_Melter` using its own virtual environment.
The earlier `Heat_Transfer` project is separate.

## Build and run

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-native.txt
.venv\Scripts\python.exe -m tools.BuildCpp
.venv\Scripts\python.exe app.py
```

`BuildCpp` verifies pinned archives, installs project-local headers and portable
GCC on Windows, configures CMake/Ninja, builds the shared C ABI and native CLI,
and collects runtime dependencies. `outputs/native/build_manifest.json` records
the compiler, runtime files and compiled-source fingerprint. Downloaded tools
are excluded from Git; the dependency lock and license notices are tracked.

Close desktop/preview/numerical processes before replacing their loaded DLL on
Windows. The dashboard checks its embedded C++ sources against the compiled
fingerprint and requests a rebuild when they differ.

## Responsibilities

| Source | Responsibility |
| --- | --- |
| `native/include/rotary/Configuration.hpp`, `src/Configuration.cpp` | Typed fields, migration and validation |
| `native/src/Geometry.cpp` | Fill/wet tables, capacities, radial grid and hydraulics |
| `native/src/Thermodynamics.cpp` | Enthalpy, IF97 and exterior surface balance |
| `native/src/Calculation.cpp` | Conservative ODE and Boost integrators |
| `native/src/Analysis.cpp` | Parallel cases, convergence, sensitivity and sizing |
| `native/src/ContactDynamics.cpp` | Lattice, walls, rigid/compliant contacts and liquid plane |
| `native/src/Api.cpp`, `MotionApi.cpp` | Exception-safe C ABI and explicit ownership |
| `rotary_melter/NativeEngine.py` | JSON transport, job lifecycle and provenance |
| `rotary_melter/dynamics/NativeContactEngine.py` | Contiguous array transport and context ownership |
| `web/interface/NativeDashboard.js`, `NativeMethods.js` | Controls, analyses, history and actual method explanations |

Python remains the desktop/file host and JavaScript/WebView2 the view. Numerical
calculation and independent-case scheduling run in C++. Retained V11 JavaScript,
Numba and SciPy implementations provide regression references. The native CLI
runs without Python.

## Readability, writeability and traceability

C++ uses `.clang-format` and separate responsibility files. Each job owns an input
and options snapshot; form edits invalidate its current-result status. Requested
inputs are preserved separately from derived mass/properties. Run ID, UTC,
input/request/DLL SHA-256, source fingerprint and library versions accompany
results. JSON is the complete record; Markdown explains stages and measured
outputs; CSV supports comparison. Tests use isolated storage and preserve the
user's revision-checked scenario library.

Independent analyses use bounded `BS_thread_pool` workers with serial inner
cases. An optional OpenMP kernel handles at least 4096 independent surface cells;
shared reductions remain in fixed order. Time steps, sizing bounds and contacts
sharing particles remain sequential. More threads are not a speed guarantee.

## Checks and equations

```powershell
.venv\Scripts\python.exe -m unittest -v tests.test_cpp_engine tests.test_cpp_contacts
.venv\Scripts\python.exe -m tools.RunChecks --desktop
.venv\Scripts\python.exe -m tools.ValidateCpp --full
.venv\Scripts\python.exe -m tools.ValidateFullMotion
.venv\Scripts\python.exe -m tools.DocumentCppEquations
.venv\Scripts\python.exe -m tools.DocumentCppEquations --check
```

The full motion check uses all 45,120 default spheres, .4 s settling and 2 s
rotation, and can take many minutes. Progress and its run directory are printed.
Create that directory's `CANCEL` file to stop between native batches. Failed or
cancelled runs never publish a reusable cache. Other logs stay in `outputs/`.

The catalogue generator resolves unique anchors and current source hashes.
For strict mathematics validation and standalone offline HTML with embedded fonts:

```powershell
.tools\node\npm.cmd install --prefix .tools\formatters --no-audit --no-fund katex@0.16.22 markdown-it@14.1.0 prettier@3.6.2
.tools\node\node.exe tools\VerifyMarkdown.cjs
```

Preview with **Ctrl+Shift+V**, or **Ctrl+K, V** beside the VS Code editor.

## Visual QA and EXE

```powershell
.venv\Scripts\python.exe -m tools.PreviewDashboard
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.venv\Scripts\python.exe -m tools.BuildDesktop
releases\current\Rotary_Melter_Cpp.exe --self-test outputs\packaged_check.json
```

The development preview binds only `127.0.0.1:8765`, runs real C++ calculations
and stores isolated scenarios/runs under `outputs/dashboard_preview/`. Native
Save As remains a desktop-only operation. Packaging includes the native library,
runtimes, catalogue, licenses, inputs and motion reference. Old releases remain
intact. Packaged results persist beside the EXE under `outputs/`, outside the
temporary extraction directory.

Conservation, reference agreement, convergence and containment are separate
numerical checks. They do not calibrate material/contact/RPM parameters or
validate real equipment melt time. See [the formula catalogue](CPP_CALCULATION_EQUATIONS.md)
for assumptions and literature.

## Optional NVIDIA analysis

`KURULUM_GPU.cmd` installs pinned CuPy 13.6 / CUDA 12.9 runtime and NVRTC wheels
inside this project environment. It does not install or replace the GPU driver.
`native/cuda/FieldAnalysis.cu` compiles at runtime; system nvcc is not required.

```powershell
.venv\Scripts\python.exe app.py --gpu-info outputs/gpu_info.json
.venv\Scripts\python.exe -m tools.BuildDesktop --with-gpu
releases\current\Rotary_Melter_Cpp_GPU.exe --self-test outputs/gpu_desktop.json --require-gpu
```

The GPU action checks independent saved exterior-field fluxes in float64; the
dependent thermal integration and contact constraints remain C++ CPU operations.
CPU/GPU differences, recorded-flux closure, device and total JIT/transfer time
are written to each run's GPU_REPORT.md and gpu_audit.json. Small audits are
slower than vectorized CPU evaluation. The full packaged desktop test passed
on the RTX 4070; [packaging evidence](../validation/desktop_packaging.json)
records executable hashes. Run reports contain a native source snapshot and
portable equation links. Existing V11 releases and recordings remain on disk.
