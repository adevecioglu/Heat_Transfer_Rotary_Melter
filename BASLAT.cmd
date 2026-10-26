@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
set "PATH=%~dp0.tools\node;C:\Program Files\Git\cmd;%PATH%"
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo Once KURULUM.cmd dosyasini calistirin.
  pause
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0app.py" %*
if errorlevel 1 (
  echo Uygulama acilamadi. Yukaridaki hata mesajini kontrol edin.
  pause
)
