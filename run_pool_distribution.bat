@echo off

set DEADLINE_CMD=C:\Program Files\Thinkbox\Deadline10\bin\deadlinecommand.exe
set SCRIPT_PATH=\\10.16.34.40\DeadlineRepository\custom\scripts\General\PoolManagerAuto.py

echo Execution du script...
"%DEADLINE_CMD%" -ExecuteScript "%SCRIPT_PATH%"

echo.
echo Script termine - Code: %ERRORLEVEL%
pause