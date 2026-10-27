@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
if exist ".venv\Scripts\python.exe" goto install
where py >nul 2>&1
if not errorlevel 1 (
  py -3.12 -m venv .venv 2>nul
  if exist ".venv\Scripts\python.exe" goto install
  py -3.11 -m venv .venv 2>nul
  if exist ".venv\Scripts\python.exe" goto install
  py -3.10 -m venv .venv 2>nul
  if exist ".venv\Scripts\python.exe" goto install
)
set "LOCAL_PYTHON=C:\Program Files\ANSYS Inc\ANSYS Student\v261\commonfiles\CPython\3_10\winx64\Release\python\python.exe"
if exist "%LOCAL_PYTHON%" (
  "%LOCAL_PYTHON%" -m venv .venv
) else (
  echo Python 3.10, 3.11 veya 3.12 kurulumu gerekli.
  pause
  exit /b 1
)
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m tools.SetupNode
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements-native.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m tools.BuildCpp
if errorlevel 1 goto failed
".venv\Scripts\python.exe" app.py --build
if errorlevel 1 goto failed
echo Kurulum tamamlandi. BASLAT.cmd ile uygulamayi acabilirsiniz.
pause
exit /b 0
:failed
echo Kurulum tamamlanamadi. Yukaridaki hata mesajini kontrol edin.
pause
exit /b 1
