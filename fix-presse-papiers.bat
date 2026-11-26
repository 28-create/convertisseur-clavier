@echo off
setlocal
rem Evite l'execution d'un py.exe/python.exe place dans le dossier courant.
set "NoDefaultCurrentDirectoryInExePath=1"
rem Prefere le lanceur Python systeme (py -3), repli sur un vrai python 3
rem (elimine le faux positif du stub Microsoft Store).
if exist "%SystemRoot%\py.exe" (
  "%SystemRoot%\py.exe" -3 -c "import sys; raise SystemExit(0 if sys.version_info[0]>=3 else 1)" >nul 2>&1
  if not errorlevel 1 (
    "%SystemRoot%\py.exe" -3 "%~dp0fix-presse-papiers.py" %*
    goto :done
  )
)
python.exe -c "import sys; raise SystemExit(0 if sys.version_info[0]>=3 else 1)" >nul 2>&1
if not errorlevel 1 (
  python.exe "%~dp0fix-presse-papiers.py" %*
  goto :done
)
echo Python 3 introuvable : installez-le depuis https://www.python.org/downloads/
echo ^(cocher "Add python.exe to PATH" pendant l'installation^).
pause
exit /b 1
:done
if errorlevel 1 pause
