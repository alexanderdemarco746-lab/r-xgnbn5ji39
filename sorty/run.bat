@echo off
rem Start Sorty. First run creates the Python environment and installs the two packages.
setlocal
set "HERE=%~dp0"
if not exist "%HERE%.venv\Scripts\python.exe" (
  echo Setting up Sorty for the first time...
  py -3 -m venv "%HERE%.venv" || python -m venv "%HERE%.venv" || goto :fail
  "%HERE%.venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r "%HERE%requirements.txt" || goto :fail
)
"%HERE%.venv\Scripts\python.exe" "%HERE%server\app.py" %*
goto :eof
:fail
echo Setup failed. Install Python 3.10 or newer from python.org and run this again.
exit /b 1
