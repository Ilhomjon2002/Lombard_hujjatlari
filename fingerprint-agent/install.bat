@echo off
REM Fingerprint Authentication Agent - Windows Service Installer
REM Run as Administrator

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set AGENT_DIR=%~dp0
set VENV_DIR=%AGENT_DIR%venv
set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe
set AGENT_SCRIPT=%AGENT_DIR%agent.py

echo.
echo ================================================
echo Fingerprint Authentication Agent - Installer
echo ================================================
echo.

@REM REM Check if running as Administrator
@REM for /f "tokens=1" %%A in ('whoami /priv ^| find "SeServiceLogonRight"') do set ADMIN=1
@REM if not defined ADMIN (
@REM     echo ERROR: This script must be run as Administrator
@REM     echo.
@REM     echo Please right-click on this file and select "Run as Administrator"
@REM     pause
@REM     exit /b 1
@REM )



REM Eski tekshiruvni o'chirib tashlang yoki izoh qiling:
REM for /f "tokens=1" %%A in ('whoami /priv ^| find "SeServiceLogonRight"') do set ADMIN=1
REM if not defined ADMIN ( ... )

REM Yangi, ishonchli tekshiruv:
net session >nul 2>&1
if %errorlevel% == 0 (
    echo Administrative permissions confirmed.
) else (
    echo ERROR: This script must be run as Administrator
    echo.
    echo Please right-click on this file and select "Run as Administrator"
    pause
    exit /b 1
)









REM Check if Python exists
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python executable not found at: %PYTHON_EXE%
    echo.
    echo Please install the virtual environment first:
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo Agent Installation Script
echo.
echo Agent Directory: %AGENT_DIR%
echo Python Executable: %PYTHON_EXE%
echo Agent Script: %AGENT_SCRIPT%
echo.

REM Install/Uninstall menu
:menu
echo.
echo What would you like to do?
echo 1. Install as Windows Service
echo 2. Uninstall Windows Service
echo 3. Start Service
echo 4. Stop Service
echo 5. View Service Status
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto install_service
if "%choice%"=="2" goto uninstall_service
if "%choice%"=="3" goto start_service
if "%choice%"=="4" goto stop_service
if "%choice%"=="5" goto status_service
if "%choice%"=="6" goto end
goto menu

:install_service
echo.
echo Installing Fingerprint Authentication Agent as Windows Service...
echo.

%PYTHON_EXE% "%AGENT_DIR%install_service.py" install

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Successfully installed as Windows Service!
    echo You can now start the service with: net start FingerprintAgent
    echo.
) else (
    echo.
    echo ERROR: Failed to install service
    echo.
)

goto menu

:uninstall_service
echo.
echo Uninstalling Fingerprint Authentication Agent...
echo.

REM Stop the service first
net stop FingerprintAgent >nul 2>&1

%PYTHON_EXE% "%AGENT_DIR%install_service.py" remove

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Successfully uninstalled Windows Service!
    echo.
) else (
    echo.
    echo ERROR: Failed to uninstall service
    echo.
)

goto menu

:start_service
echo.
echo Starting Fingerprint Authentication Agent service...
net start FingerprintAgent

if %ERRORLEVEL% EQU 0 (
    echo Service started successfully
) else (
    echo ERROR: %ERRORLEVEL%, Failed to start service
)
goto menu

:stop_service
echo.
echo Stopping Fingerprint Authentication Agent service...
net stop FingerprintAgent

if %ERRORLEVEL% EQU 0 (
    echo Service stopped successfully
) else (
    echo ERROR: Failed to stop service
)
goto menu

:status_service
echo.
echo Checking Fingerprint Authentication Agent service status...
sc query FingerprintAgent

echo.
goto menu

:end
echo.
echo Exiting installer...
echo.
pause
exit /b 0
