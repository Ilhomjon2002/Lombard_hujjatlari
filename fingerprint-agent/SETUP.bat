@echo off
chcp 65001 >nul 2>&1
title Inventor Fingerprint Agent - O'rnatish

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║    Inventor Fingerprint Agent - O'rnatish dasturi   ║
echo ║              ZKTeco barmoq izi agenti               ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: Administrator tekshiruvi
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [XATO] Bu faylni Administrator sifatida ishga tushiring!
    echo.
    echo  1. SETUP.bat ustiga o'ng klik qiling
    echo  2. "Administrator sifatida ishga tushirish" tanlang
    echo.
    pause
    exit /b 1
)

set AGENT_DIR=%~dp0
set VENV_DIR=%AGENT_DIR%venv
set PY_EXE=%VENV_DIR%\Scripts\python.exe
set PIP_EXE=%VENV_DIR%\Scripts\pip.exe

echo [1/5] Python tekshirilmoqda...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [XATO] Python o'rnatilmagan!
    echo.
    echo Python 3.10 yoki 3.11 ni o'rnating:
    echo   https://www.python.org/downloads/
    echo.
    echo O'rnatishda "Add Python to PATH" katakchasini belgilang!
    echo.
    start https://www.python.org/downloads/release/python-31011/
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo     Python %PY_VER% topildi ✓

echo.
echo [2/5] Virtual muhit yaratilmoqda...
if exist "%VENV_DIR%" (
    echo     Mavjud venv topildi, tozalanmoqda...
    rmdir /s /q "%VENV_DIR%" >nul 2>&1
)
python -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo [XATO] Virtual muhit yaratishda xatolik!
    pause
    exit /b 1
)
echo     Virtual muhit yaratildi ✓

echo.
echo [3/5] Kerakli kutubxonalar o'rnatilmoqda...
echo     (Bu bir necha daqiqa davom etishi mumkin)
echo.

"%PIP_EXE%" install --upgrade pip --quiet
"%PIP_EXE%" install flask flask-cors requests --quiet
if %errorlevel% neq 0 (
    echo [XATO] Flask o'rnatishda xatolik!
    pause
    exit /b 1
)
echo     Flask, Flask-CORS, Requests ✓

echo.
echo     pyzkfp o'rnatilmoqda (ZKTeco kutubxonasi)...
"%PIP_EXE%" install pyzkfp --quiet
if %errorlevel% neq 0 (
    echo [OGOHLANTIRISH] pyzkfp o'rnatilmadi.
    echo     Bu ZKFinger SDK o'rnatilmagan bo'lsa oddiy holat.
    echo     pyzkfp keyinroq qo'lda o'rnatilishi mumkin.
) else (
    echo     pyzkfp ✓
)

echo.
echo [4/5] libzkfp.dll tekshirilmoqda...
if exist "%AGENT_DIR%libzkfp.dll" (
    echo     libzkfp.dll topildi ✓
    
    :: System32 ga nusxalash
    copy /y "%AGENT_DIR%libzkfp.dll" "C:\Windows\System32\" >nul 2>&1
    if %errorlevel% equ 0 (
        echo     System32 ga ko'chirildi ✓
    ) else (
        echo     [OGOHLANTIRISH] System32 ga ko'chirib bo'lmadi. Qo'lda bajaring.
    )
    
    :: SysWOW64 ga nusxalash (64-bit Windows uchun)
    if exist "C:\Windows\SysWOW64\" (
        copy /y "%AGENT_DIR%libzkfp.dll" "C:\Windows\SysWOW64\" >nul 2>&1
        if %errorlevel% equ 0 echo     SysWOW64 ga ko'chirildi ✓
    )
) else (
    echo [OGOHLANTIRISH] libzkfp.dll topilmadi!
    echo     ZKFinger SDK sovg'asi bilan birga ushbu fayl bo'lishi kerak.
)

echo.
echo [5/5] Ishga tushirish fayli yaratilmoqda...

:: run_agent.bat yangilash
(
    echo @echo off
    echo chcp 65001 ^>nul 2^>^&1
    echo title Inventor Fingerprint Agent
    echo echo Inventor Fingerprint Agent ishga tushmoqda...
    echo echo Agentni to'xtatish uchun bu oynani yoping yoki Ctrl+C bosing
    echo echo.
    echo cd /d "%%~dp0"
    echo "%%~dp0venv\Scripts\python.exe" "%%~dp0agent.py"
    echo pause
) > "%AGENT_DIR%run_agent.bat"
echo     run_agent.bat yangilandi ✓

:: Desktop ga yorliq yaratish
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT=%DESKTOP%\Fingerprint Agent.lnk

powershell -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s = $ws.CreateShortcut('%SHORTCUT%'); ^
   $s.TargetPath = '%AGENT_DIR%run_agent.bat'; ^
   $s.WorkingDirectory = '%AGENT_DIR%'; ^
   $s.WindowStyle = 1; ^
   $s.Description = 'Inventor Fingerprint Agent'; ^
   $s.Save()" >nul 2>&1

if exist "%SHORTCUT%" (
    echo     Desktop yorlig'i yaratildi ✓
) else (
    echo     [OGOHLANTIRISH] Desktop yorlig'i yaratilmadi
)

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║               O'RNATISH MUVAFFAQIYATLI!             ║
echo ╚══════════════════════════════════════════════════════╝
echo.
echo  Agentni ishga tushirish uchun:
echo    1. Desktop dagi "Fingerprint Agent" yorlig'ini bosing
echo    YOKI
echo    2. run_agent.bat faylini ikki marta bosing
echo.
echo  MUHIM: Agentni har doim barmoq izi ishlatishdan OLDIN
echo         ishga tushirish kerak!
echo.
set /p AUTOSTART="Hozir agentni ishga tushirish? (ha/yo'q): "
if /i "%AUTOSTART%"=="ha" (
    echo.
    echo Agent ishga tushmoqda...
    start "Fingerprint Agent" "%AGENT_DIR%run_agent.bat"
)

echo.
pause
