@echo off
chcp 65001 >nul 2>&1
title Inventor Fingerprint Agent - To'liq O'rnatish

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║       Inventor Fingerprint Agent - O'rnatish dasturi     ║
echo ║                  Versiya 2.0                             ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

:: ─── Administrator tekshiruvi ───
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [XATO] Administrator huquqi talab etiladi!
    echo.
    echo  Iltimos, SETUP.bat ustiga o'ng klik qilib
    echo  "Administrator sifatida ishga tushirish" tanlang.
    echo.
    pause
    exit /b 1
)

set AGENT_DIR=%~dp0
set VENV_DIR=%AGENT_DIR%venv
set PY_EXE=%VENV_DIR%\Scripts\python.exe
set PIP_EXE=%VENV_DIR%\Scripts\pip.exe
set PY_INSTALLER=%AGENT_DIR%_python_installer.exe
set PY_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

echo  O'rnatish papkasi: %AGENT_DIR%
echo.

:: ════════════════════════════════════════
:: QADAM 1: Python tekshirish va o'rnatish
:: ════════════════════════════════════════
echo [1/6] Python tekshirilmoqda...

:: Avval PATH dagi Python ni tekshir
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
    echo       Python !PY_VER! topildi ✓
    set SYS_PYTHON=python
    goto python_ok
)

:: C:\Python311 ni tekshir
if exist "C:\Python311\python.exe" (
    echo       Python C:\Python311 da topildi ✓
    set SYS_PYTHON=C:\Python311\python.exe
    goto python_ok
)

:: Python yo'q — yuklab o'rnatamiz
echo       Python topilmadi. Avtomatik yuklab o'rnatilmoqda...
echo.
echo       Internet orqali Python 3.11 yuklanmoqda...
echo       (Bu bir necha daqiqa davom etishi mumkin)
echo.

:: PowerShell bilan yuklab olish
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $wc = New-Object System.Net.WebClient; Write-Host '      Yuklanmoqda: python-3.11.9-amd64.exe ...'; $wc.DownloadFile('%PY_URL%', '%PY_INSTALLER%'); Write-Host '      Yuklash tugadi!' }"

if not exist "%PY_INSTALLER%" (
    echo.
    echo  [XATO] Python yuklanmadi! Internet ulanishini tekshiring.
    echo.
    echo  Qo'lda o'rnatish uchun:
    echo    https://www.python.org/downloads/release/python-3119/
    echo    (python-3.11.9-amd64.exe yuklab, "Add to PATH" ni belgilab o'rnating)
    echo.
    pause
    exit /b 1
)

echo.
echo       Python o'rnatilmoqda (avtomatik rejimda)...
"%PY_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1

if %errorlevel% neq 0 (
    echo  [XATO] Python o'rnatishda xatolik yuz berdi!
    del /f /q "%PY_INSTALLER%" >nul 2>&1
    pause
    exit /b 1
)

:: PATH yangilash
set "PATH=C:\Program Files\Python311;C:\Program Files\Python311\Scripts;%PATH%"
set SYS_PYTHON=python

:: Vaqtinchalik faylni o'chirish
del /f /q "%PY_INSTALLER%" >nul 2>&1
echo       Python 3.11 o'rnatildi ✓

:python_ok

:: ════════════════════════════════════════
:: QADAM 2: pip yangilash
:: ════════════════════════════════════════
echo.
echo [2/6] pip yangilanmoqda...
%SYS_PYTHON% -m pip install --upgrade pip --quiet --no-warn-script-location
echo       pip yangilandi ✓

:: ════════════════════════════════════════
:: QADAM 3: Virtual muhit
:: ════════════════════════════════════════
echo.
echo [3/6] Virtual muhit yaratilmoqda...
if exist "%VENV_DIR%" (
    echo       Eski venv tozalanmoqda...
    rmdir /s /q "%VENV_DIR%" >nul 2>&1
)
%SYS_PYTHON% -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo  [XATO] Virtual muhit yaratishda xatolik!
    pause
    exit /b 1
)
echo       Virtual muhit yaratildi ✓

:: ════════════════════════════════════════
:: QADAM 4: Kutubxonalar o'rnatish
:: ════════════════════════════════════════
echo.
echo [4/6] Kutubxonalar o'rnatilmoqda...

"%PIP_EXE%" install --upgrade pip --quiet --no-warn-script-location

echo       Flask o'rnatilmoqda...
"%PIP_EXE%" install flask==3.0.3 flask-cors==4.0.1 requests==2.31.0 --quiet --no-warn-script-location
if %errorlevel% neq 0 (
    echo  [XATO] Flask o'rnatishda xatolik!
    pause
    exit /b 1
)
echo       Flask ✓

echo       pyzkfp (ZKTeco) o'rnatilmoqda...
"%PIP_EXE%" install pyzkfp --quiet --no-warn-script-location
if %errorlevel% equ 0 (
    echo       pyzkfp ✓
) else (
    echo       [OGOHLANTIRISH] pyzkfp o'rnatilmadi. Skaner SDK kerak bo'lishi mumkin.
)

:: ════════════════════════════════════════
:: QADAM 5: libzkfp.dll nusxalash
:: ════════════════════════════════════════
echo.
echo [5/6] ZKTeco kutubxonasi (libzkfp.dll) sozlanmoqda...
if exist "%AGENT_DIR%libzkfp.dll" (
    copy /y "%AGENT_DIR%libzkfp.dll" "C:\Windows\System32\" >nul 2>&1
    if %errorlevel% equ 0 (
        echo       System32 ga ko'chirildi ✓
    ) else (
        echo       [OGOHLANTIRISH] System32 ga ko'chirilmadi
    )
    if exist "C:\Windows\SysWOW64\" (
        copy /y "%AGENT_DIR%libzkfp.dll" "C:\Windows\SysWOW64\" >nul 2>&1
        echo       SysWOW64 ga ko'chirildi ✓
    )
) else (
    echo       [OGOHLANTIRISH] libzkfp.dll topilmadi! Skaner ishlamasligi mumkin.
)

:: ════════════════════════════════════════
:: QADAM 6: Ishga tushirish sozlash
:: ════════════════════════════════════════
echo.
echo [6/6] Ishga tushirish sozlanmoqda...

:: run_agent.bat yangilash
(
    echo @echo off
    echo chcp 65001 ^>nul 2^>^&1
    echo title Inventor Fingerprint Agent
    echo cd /d "%%~dp0"
    echo echo ==========================================
    echo echo   Inventor Fingerprint Agent ishlamoqda
    echo echo   Port: 8001  ^|  Yopish: oynani yoping
    echo echo ==========================================
    echo echo.
    echo "%%~dp0venv\Scripts\python.exe" "%%~dp0agent.py"
    echo pause
) > "%AGENT_DIR%run_agent.bat"
echo       run_agent.bat yangilandi ✓

:: Desktop yorlig'i
set SHORTCUT=%USERPROFILE%\Desktop\Fingerprint Agent.lnk
powershell -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath='%AGENT_DIR%run_agent.bat'; $s.WorkingDirectory='%AGENT_DIR%'; $s.Description='Inventor Fingerprint Agent'; $s.Save()" >nul 2>&1
if exist "%SHORTCUT%" (
    echo       Desktop yorlig'i yaratildi ✓
) else (
    echo       [OGOHLANTIRISH] Desktop yorlig'i yaratilmadi
)

:: Boshlang'ich menyuga qo'shish (ixtiyoriy)
set STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Fingerprint Agent.lnk
powershell -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%STARTMENU%'); $s.TargetPath='%AGENT_DIR%run_agent.bat'; $s.WorkingDirectory='%AGENT_DIR%'; $s.Description='Inventor Fingerprint Agent'; $s.Save()" >nul 2>&1

:: ════════════════════════════════════════
:: YAKUNIY
:: ════════════════════════════════════════
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║             O'RNATISH MUVAFFAQIYATLI TUGADI!            ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo  Ishga tushirish:
echo    Desktop dagi "Fingerprint Agent" belgisini bosing
echo.
echo  MUHIM: Agentni har doim tizimga kirganda ishga tushiring!
echo         Inventor tizimida barmoq izi ishlatishdan oldin
echo         bu agent ishlab turishi SHART.
echo.

set /p RUN_NOW="Hozir agentni ishga tushirish? (ha/yo'q): "
if /i "%RUN_NOW%"=="ha" (
    echo.
    echo  Agent ishga tushmoqda...
    start "" "%AGENT_DIR%run_agent.bat"
)

echo.
pause
