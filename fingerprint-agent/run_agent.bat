@echo off
echo Eski agentni to'xtatish...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Fingerprint Agent*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Fingerprint Agent*" 2>nul

echo Yangi agentni yuklash...
title Fingerprint Agent v2.0
cd /d "%~dp0"
python agent.py
pause
