# Rotary Melter workspace

- The canonical project root is `C:\Projects\Heat_Transfer_Rotary_Melter`.
- Keep development, generated outputs and temporary project work inside this root.
- Use `.venv\Scripts\python.exe` for every Python command. Activate with `. .\AKTIF_ET.ps1`.
- Install dependencies with `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- Use `rotary_melter/` for Python application code; keep root `app.py` as a launcher.
- The production thermal model runs in JavaScript under `rotary_melter/web/calculations/`; the independent SciPy model is `rotary_melter/Calculation.py`. Do not substitute the earlier Mixing Vessel model.
- Keep calculations, interface, reporting, workspace persistence and dynamics in files named for their responsibilities. `docs/KOD_YAPISI.md` explains the layout.
- Run checks using `.venv\Scripts\python.exe -m tools.RunChecks`; the desktop self-test is `app.py --self-test outputs/desktop_check.json`.
- Node.js is available in `.tools/node/node.exe`; `AKTIF_ET.ps1` adds it to PATH. `tools/SetupNode.py` downloads and verifies a project-local runtime when needed.
- Preserve original releases on disk under `releases/`; exclude releases, `.venv`, `.tools`, caches, build artifacts and outputs from Git.
- Git is `C:\Program Files\Git\cmd\git.exe`. Use noninteractive commit messages; do not leave commits waiting for an editor.
- Preserve the user's existing `%LOCALAPPDATA%\RotaryMelter\workspace.json` data and scenario compatibility. Automated checks must use isolated project-local storage.
- When calculation code changes, update equation documentation source-line references and rerun the appropriate numerical checks.
