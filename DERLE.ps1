$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    & .\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw 'Derleme bagimliliklari kurulamadi.' }
    & .\.venv\Scripts\python.exe -m tools.BuildDesktop
    if ($LASTEXITCODE -ne 0) { throw 'EXE derlemesi basarisiz.' }
} finally {
    Pop-Location
}
