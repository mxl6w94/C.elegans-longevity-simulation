@echo off
setlocal
where python >nul 2>nul
if %errorlevel%==0 (
    python "%~dp0launcher.py" %*
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        py -3 "%~dp0launcher.py" %*
    ) else (
        echo Python was not found on PATH. Install Python 3.10+ from https://python.org and try again.
        pause
        exit /b 1
    )
)
echo.
echo ============================================
if errorlevel 1 (
    echo Launcher exited with an error - see output above.
) else (
    echo Done. See the [launcher] lines above for the results path.
)
echo ============================================
pause
