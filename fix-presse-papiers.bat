@echo off
rem Prefere le lanceur Python (py -3), repli sur python si absent.
set "PYEXE=python"
where py >nul 2>&1 && set "PYEXE=py -3"
%PYEXE% "%~dp0fix-presse-papiers.py" %*
if errorlevel 1 pause
