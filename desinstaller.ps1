# Desinstalle Convertisseur Clavier (miroir d'installer.ps1).
# Usage : powershell -ExecutionPolicy Bypass -File desinstaller.ps1
#   [-SansMenuContextuel si l'install l'etait, sinon le menage du
#    menu clic droit est fait par defaut]
param(
  [string]$AppDir = (Join-Path $env:LOCALAPPDATA 'Programs\ConvertisseurClavier'),
  [string]$MenuDir = (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'),
  [string]$RegName = 'ConvertisseurClavier',
  [string]$Nom = 'Convertisseur Clavier',
  [string]$ShellRoot = '',
  [string]$ShellName = 'ConvertisseurClavier',
  [string]$LnkPressePapiers = 'Convertisseur Clavier - Presse-papiers'
)
$ErrorActionPreference = 'Stop'

$lnk = Join-Path $MenuDir ($Nom + '.lnk')
if (Test-Path $lnk) { Remove-Item $lnk -Force }
$lnkClip = Join-Path $MenuDir ($LnkPressePapiers + '.lnk')
if (Test-Path $lnkClip) { Remove-Item $lnkClip -Force }
$reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegName"
if (Test-Path $reg) { Remove-Item $reg -Recurse -Force }
$classes = if ($ShellRoot) { $ShellRoot } else { 'HKCU:\Software\Classes' }
foreach ($k in @(
  "$classes\*\shell\$ShellName",
  "$classes\SystemFileAssociations\.txt\shell\$ShellName.Convertir",
  "$classes\Directory\shell\$ShellName",
  "$classes\Directory\Background\shell\$ShellName"
)) {
  if (Test-Path $k) { Remove-Item $k -Recurse -Force }
}
if (Test-Path $AppDir) { Remove-Item $AppDir -Recurse -Force }
Write-Host 'Desinstalle.'
