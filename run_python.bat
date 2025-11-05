@echo off
REM Try to run the TO DO LIST app using 'python' on PATH. If this fails, use run.bat instead.
python "%~dp0main.py"
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to run with `python`. Try `run.bat` which uses the Windows launcher: `py -3 main.py`.
)
exit /b %errorlevel%
