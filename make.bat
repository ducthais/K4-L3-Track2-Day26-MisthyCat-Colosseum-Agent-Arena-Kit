@echo off
setlocal
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0make.py" %*
) else (
    python "%~dp0make.py" %*
)
