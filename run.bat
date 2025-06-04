@echo off

title discord bot: sem

SETLOCAL

REM set path to virtual environment
set VENV_DIR=.venv
set VENV_ACTIVATE=%VENV_DIR%\Scripts\activate

REM check if venv exists
if not exist "%VENV_DIR%" (
	echo creating virtual environment..
	python -m venv %VENV_DIR%
)

REM activate venv
call "%VENV_ACTIVATE%"

REM pull latest changes from git
git reset --hard -q HEAD
git pull -q origin main

REM install requirements
pip install -r req.txt

REM run bot
python main.py

ENDLOCAL

pause