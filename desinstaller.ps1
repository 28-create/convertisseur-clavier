# Desinstalle Convertisseur Clavier (miroir d'installer.ps1).
# Usage : powershell -ExecutionPolicy Bypass -File desinstaller.ps1
#   [-SansMenuContextuel si l'install l'etait, sinon le menage du
#    menu clic droit est fait par defaut]
param(
  [string]$AppDir = (Join-Path $env:LOCALAPPDATA 'Programs\ConvertisseurClavier'),
  [string]$MenuDir = (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'),
  [string]$RegName = 'ConvertisseurClavier',
  [string]$Nom = 'Convertisseur Clavier',
  [string]$RunName = 'ConvertisseurClavier',
  [string]$ShellRoot = '',
  [string]$ShellName = 'ConvertisseurClavier',
  [string]$LnkPressePapiers = 'Convertisseur Clavier - Presse-papiers'
)
$ErrorActionPreference = 'Stop'

function Assert-SafeName([string]$Label, [string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value) -or $Value -match '[\\/:*?"<>|\[\]]') {
    throw "Nom invalide pour $Label : $Value"
  }
}

Assert-SafeName 'RegName' $RegName
Assert-SafeName 'Nom' $Nom
Assert-SafeName 'RunName' $RunName
Assert-SafeName 'ShellName' $ShellName
Assert-SafeName 'LnkPressePapiers' $LnkPressePapiers

# Arrete le guetteur avant de supprimer son exe (fichier verrouille sinon).
$exeInst = Join-Path $AppDir 'ConvertisseurClavier.exe'
if (Test-Path -LiteralPath $exeInst) {
  try {
    Start-Process -FilePath $exeInst -ArgumentList '--paste-stop' -WindowStyle Hidden -Wait | Out-Null
  } catch {
    # Ancienne version sans --paste-stop : on continue.
  }
}
# Retire le demarrage automatique de la surveillance.
Remove-ItemProperty -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name $RunName -ErrorAction SilentlyContinue

$lnk = Join-Path $MenuDir ($Nom + '.lnk')
if (Test-Path -LiteralPath $lnk) { Remove-Item -LiteralPath $lnk -Force }
$lnkClip = Join-Path $MenuDir ($LnkPressePapiers + '.lnk')
if (Test-Path -LiteralPath $lnkClip) { Remove-Item -LiteralPath $lnkClip -Force }
$reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegName"
if (Test-Path -LiteralPath $reg) { Remove-Item -LiteralPath $reg -Recurse -Force }
$classes = if ($ShellRoot) { $ShellRoot } else { 'HKCU:\Software\Classes' }
foreach ($k in @(
  "$classes\*\shell\$ShellName",
  "$classes\SystemFileAssociations\.txt\shell\$ShellName.Convertir",
  "$classes\Directory\shell\$ShellName",
  "$classes\Directory\Background\shell\$ShellName"
)) {
  if (Test-Path -LiteralPath $k) { Remove-Item -LiteralPath $k -Recurse -Force }
}
if (Test-Path -LiteralPath $AppDir) { Remove-Item -LiteralPath $AppDir -Recurse -Force }
Write-Host 'Desinstalle.'
