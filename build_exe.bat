@echo off
REM ============================================================
REM  Build SysDiag v4.exe  -  a executer sous Windows
REM ============================================================
setlocal

echo.
echo === SysDiag v4 - Build de l'executable ===
echo.

REM 1. Verifier que Python est installe
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    echo Installez Python 3.10+ depuis https://www.python.org/downloads/
    echo IMPORTANT: cochez "Add python.exe to PATH" pendant l'installation.
    pause
    exit /b 1
)

REM 2. Creer un environnement virtuel propre (recommande)
if not exist "build_env" (
    echo Creation de l'environnement virtuel...
    python -m venv build_env
)
call build_env\Scripts\activate.bat

REM 3. Installer les dependances
echo Installation des dependances...
pip install --upgrade pip >nul
pip install pyinstaller psutil requests

REM 4. Nettoyer les anciens builds
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM 5. Lancer PyInstaller avec le fichier .spec
echo.
echo Compilation en cours...
pyinstaller sysdiag.spec --noconfirm

REM 6. Resultat
if exist "dist\SysDiag_v4.exe" (
    echo.
    echo ============================================
    echo   BUILD REUSSI : dist\SysDiag_v4.exe
    echo ============================================
) else (
    echo.
    echo [ERREUR] Le build a echoue. Verifiez les messages ci-dessus.
)

deactivate
pause
