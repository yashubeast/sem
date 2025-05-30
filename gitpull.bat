@echo off

REM fetch and get latest commits
git fetch origin main >nul 2>&1

REM get local HEAD before pulling
for /f "delims=" %%i in ('git rev-parse HEAD') do set BEFORE=%%i

REM pull latest commits
git pull origin main > NUL 2>&1

REM get local HEAD after pulling
for /f "delims=" %%i in ('git rev-parse HEAD') do set AFTER=%%i

REM show log only if updated
if "%BEFORE%"=="%AFTER%" (
	echo nothing
) else(
	echo ==== New Commits Pulled ====
	git log --oneline %BEFORE%..%AFTER%
)