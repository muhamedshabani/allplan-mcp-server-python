@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
python "%SCRIPT_DIR%register_python_host.py" %*

if errorlevel 1 (
    echo Registration failed.
    exit /b %errorlevel%
)

echo Registration completed. See registration_result.json and utils_log.txt.
