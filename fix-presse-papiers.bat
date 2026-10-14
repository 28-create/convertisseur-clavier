@echo off
rem Prefere le lanceur Python (py -3), repli sur python si absent.
where py >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp0fix-presse-papiers.py" %*
) else (
  where python >nul 2>&1
  if not errorlevel 1 (
    python "%~dp0fix-presse-papiers.py" %*
  ) else (
    echo Python 3 introuvable : installez-le depuis https://www.python.org/downloads/
    echo ^(cocher "Add python.exe to PATH" pendant l'installation^).
    pause
    exit /b 1
  )
)
if errorlevel 1 pause
