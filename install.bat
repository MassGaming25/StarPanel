@echo off
setlocal enabledelayedexpansion
title StarPanel Installer

echo.
echo   +==================================+
echo   ^|     StarPanel  --  Installer     ^|
echo   +==================================+
echo.

set "SCRIPT_DIR=%~dp0"
set "INSTALL_DIR=%LOCALAPPDATA%\StarPanel"
set "BIN_DIR=%LOCALAPPDATA%\StarPanel\bin"

REM ── Check Python ──────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Python not found.
    echo           Download from: https://www.python.org/downloads/
    echo           Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo   [OK]   Python %PY_VER% found

REM ── Check PyQt6 ───────────────────────────────────────────────────
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo   [SETUP] Installing PyQt6...
    pip install PyQt6 --quiet
    if errorlevel 1 (
        echo   [ERROR] Failed to install PyQt6.
        pause
        exit /b 1
    )
)
echo   [OK]   PyQt6 found

REM ── Copy app files ────────────────────────────────────────────────
echo   [INSTALL] Copying app to %INSTALL_DIR%...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
xcopy /E /I /Y "%SCRIPT_DIR%src" "%INSTALL_DIR%\src\" >nul
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
echo   [OK]   App files copied

REM ── Create launcher script ────────────────────────────────────────
set "LAUNCHER=%BIN_DIR%\starpanel.bat"
echo @echo off > "%LAUNCHER%"
echo python "%INSTALL_DIR%\src\main.py" %%* >> "%LAUNCHER%"
echo   [OK]   Launcher created: %LAUNCHER%

REM ── Install icon ─────────────────────────────────────────────────
if exist "%SCRIPT_DIR%assets\starpanel_256.png" (
    copy /Y "%SCRIPT_DIR%assets\starpanel_256.png" "%INSTALL_DIR%\starpanel.png" >nul
    echo   [OK]   Icon copied
)

REM ── Create Start Menu shortcut ────────────────────────────────────
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\StarPanel.lnk"
set "VBS=%TEMP%\make_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS%"
echo sLinkFile = "%SHORTCUT%" >> "%VBS%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS%"
echo oLink.TargetPath = "cmd.exe" >> "%VBS%"
echo oLink.Arguments = "/c ""%LAUNCHER%""" >> "%VBS%"
echo oLink.WorkingDirectory = "%INSTALL_DIR%\src" >> "%VBS%"
echo oLink.IconLocation = "%INSTALL_DIR%\starpanel.png" >> "%VBS%"
echo oLink.Description = "StarPanel - Star Citizen Companion" >> "%VBS%"
echo oLink.Save >> "%VBS%"
cscript //nologo "%VBS%"
del "%VBS%"
echo   [OK]   Start Menu shortcut created

REM ── Create Desktop shortcut ───────────────────────────────────────
set "DESK_SHORT=%USERPROFILE%\Desktop\StarPanel.lnk"
set "VBS=%TEMP%\make_shortcut2.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS%"
echo sLinkFile = "%DESK_SHORT%" >> "%VBS%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS%"
echo oLink.TargetPath = "cmd.exe" >> "%VBS%"
echo oLink.Arguments = "/c ""%LAUNCHER%""" >> "%VBS%"
echo oLink.WorkingDirectory = "%INSTALL_DIR%\src" >> "%VBS%"
echo oLink.IconLocation = "%INSTALL_DIR%\starpanel.png" >> "%VBS%"
echo oLink.Description = "StarPanel - Star Citizen Companion" >> "%VBS%"
echo oLink.Save >> "%VBS%"
cscript //nologo "%VBS%"
del "%VBS%"
echo   [OK]   Desktop shortcut created

echo.
echo   +  StarPanel installed successfully!
echo      Launch from Start Menu, Desktop shortcut, or run:
echo      %LAUNCHER%
echo.
pause
