@echo off
rem Builds FluxwormPredictionViewer.exe into core\dist\ using the
rem project's .venv (run launcher.py once first so the venv exists).
setlocal
set ROOT=%~dp0..
set PY=%ROOT%\.venv\Scripts\python.exe
if not exist "%PY%" (
    echo .venv not found - run launcher.py once first.
    pause
    exit /b 1
)
"%PY%" -m pip install -q pyinstaller
"%PY%" -m PyInstaller --noconfirm --onefile --windowed ^
    --name FluxwormPredictionViewer ^
    --distpath "%ROOT%\dist" --workpath "%ROOT%\build" --specpath "%ROOT%\build" ^
    --add-data "%ROOT%\results\survival_curves_illustrative.csv;results" ^
    --add-data "%ROOT%\results\growth_comparison.csv;results" ^
    --exclude-module pandas --exclude-module scipy --exclude-module cobra ^
    --exclude-module statsmodels --exclude-module pytest ^
    "%~dp0prediction_viewer.py"
echo.
echo Built: %ROOT%\dist\FluxwormPredictionViewer.exe
