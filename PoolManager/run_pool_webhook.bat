@echo off

set SCRIPT_PATH=\\10.16.34.40\DeadlineRepository\custom\scripts\General\PoolManager\PoolManagerWebhook.py
set PYTHONPATH=R:\pipeline\networkInstall\python_shares\python311_deadline_discord_pkgs\Lib\site-packages

R:\pipeline\networkInstall\python\Python.3.11.9\python.exe %SCRIPT_PATH%

pause