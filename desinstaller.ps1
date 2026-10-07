# Desinstalle Convertisseur Clavier (miroir d'installer.ps1).
# Usage : powershell -ExecutionPolicy Bypass -File desinstaller.ps1
param(
  [string]$AppDir = (Join-Path $env:LOCALAPPDATA 'Programs\ConvertisseurClavier'),
  [string]$MenuDir = (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'),
  [string]$RegName = 'ConvertisseurClavier',
  [string]$Nom = 'Convertisseur Clavier'
)
$ErrorActionPreference = 'Stop'

$lnk = Join-Path $MenuDir ($Nom + '.lnk')
if (Test-Path $lnk) { Remove-Item $lnk -Force }
$reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegName"
if (Test-Path $reg) { Remove-Item $reg -Recurse -Force }
if (Test-Path $AppDir) { Remove-Item $AppDir -Recurse -Force }
Write-Host 'Desinstalle.'
