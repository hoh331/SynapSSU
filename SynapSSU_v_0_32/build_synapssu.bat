@echo off
REM ======================================================================
REM  SynapSSU v0.3.1 - Nuitka standalone (folder) build (Windows + MSVC)
REM  Uses the proven MeaSSUre IV v2 toolchain (.venv_nuitka + MSVC).
REM
REM  - --standalone (no --onefile): produces a build_output\SynapSSU_v0_3.dist
REM    folder. Distribute the WHOLE folder. The exe runs directly without
REM    self-extracting to %TEMP%, which avoids the SmartScreen / antivirus
REM    blocking commonly triggered by onefile builds.
REM  - Settings persist next to the .exe inside the .dist folder
REM    (get_settings_path falls back to sys.argv[0] when frozen).
REM  - tkinter removed: no tk-inter plugin needed.
REM  - console=force keeps the diagnostic console (print logs) like MeaSSUre.
REM  - First build: ~5-15 min (C compile). Rebuilds reuse cache (~2-3 min).
REM ======================================================================
setlocal
cd /d "%~dp0"

set "PYTHON=C:\Users\hoh33\Python Project\.venv_nuitka\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo ERROR: Nuitka venv python not found at:
    echo   %PYTHON%
    pause
    exit /b 1
)

echo Building SynapSSU v0.3.1 with Nuitka...
echo Python: %PYTHON%
echo.

"%PYTHON%" -m nuitka ^
    --standalone ^
    --windows-console-mode=force ^
    --enable-plugin=pyqt5 ^
    --include-package=pyqtgraph ^
    --include-package=pyvisa ^
    --include-package=pyvisa_py ^
    --include-data-files=icon.ico=icon.ico ^
    --windows-icon-from-ico=icon.ico ^
    --product-name="SynapSSU" ^
    --product-version=0.3.2.0 ^
    --file-version=0.3.2.0 ^
    --company-name="Soongsil University" ^
    --copyright="(C) 2026 Prof. Hongseok Oh" ^
    --assume-yes-for-downloads ^
    --output-filename=SynapSSU_v0_3_2.exe ^
    --output-dir=build_output ^
    SynapSSU_v0_3.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo BUILD FAILED with exit code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ======================================================================
echo  BUILD SUCCESS
echo  Distribute this whole folder:
echo    %~dp0build_output\SynapSSU_v0_3.dist\
echo  (run SynapSSU_v0_3_2.exe inside it)
echo ======================================================================
endlocal
