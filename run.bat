@echo off
REM Run the TO DO LIST app using the Windows Python launcher (recommended on Windows)
py -3 "%~dp0main.py"
exit /b %errorlevel%
