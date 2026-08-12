@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0siteprobe.ps1" %*
exit /b %ERRORLEVEL%
