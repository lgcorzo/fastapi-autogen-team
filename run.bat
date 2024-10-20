@echo off
setlocal

:: Set the PYTHONPATH environment variable
set "PYTHONPATH=%PYTHONPATH%;%cd%\app"
set root=C:\Users\l.corzo\AppData\Local\miniconda3
call %root%\Scripts\activate.bat %root%
call conda activate pyautogen
echo "Starting autogen ..."
uvicorn --reload --log-level debug app.main:app --host 0.0.0.0

pause
endlocal

