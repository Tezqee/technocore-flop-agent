@echo off
title Technocore Auto Runner - $FLOP Airdrop
color 0A
echo.
echo  ===================================================
echo   Technocore Auto Runner - $FLOP Airdrop Helper
echo  ===================================================
echo.

:: Pindah ke folder script
cd /d "%~dp0"

:: Cek identity.pem
if not exist "identity.pem" (
    echo  [ERR] identity.pem tidak ditemukan!
    echo  [ERR] Buat DID dulu: jalankan flop_airdrop.bat
    pause
    exit /b 1
)

:: Minta passphrase kalau belum diset
if "%TECHNOCORE_PASS%"=="" (
    echo  Masukkan passphrase identity kamu:
    set /p TECHNOCORE_PASS=  Passphrase: 
    echo.
)

:: Pilih mode
echo  Pilih mode:
echo  [1] Loop otomatis tiap 10 menit (tak terbatas)
echo  [2] Loop otomatis tiap 5 menit
echo  [3] Loop otomatis tiap 1 jam
echo  [4] Kirim sekali lalu keluar
echo.
set /p MODE=  Pilihan [1]: 
if "%MODE%"=="" set MODE=1

if "%MODE%"=="1" (
    .venv\Scripts\python.exe auto_runner.py --interval 600 --room lobby
) else if "%MODE%"=="2" (
    .venv\Scripts\python.exe auto_runner.py --interval 300 --room lobby
) else if "%MODE%"=="3" (
    .venv\Scripts\python.exe auto_runner.py --interval 3600 --room lobby
) else if "%MODE%"=="4" (
    .venv\Scripts\python.exe auto_runner.py --once --room lobby
) else (
    .venv\Scripts\python.exe auto_runner.py --interval 600 --room lobby
)

echo.
echo  Selesai.
pause
