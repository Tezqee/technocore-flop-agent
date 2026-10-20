@echo off
title Technocore Interactive - $FLOP Airdrop
color 0B
cd /d "%~dp0"
if "%TECHNOCORE_PASS%"=="" (
    set /p TECHNOCORE_PASS=  Passphrase: 
)
.venv\Scripts\python.exe flop_airdrop.py
pause
