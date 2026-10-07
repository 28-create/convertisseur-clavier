# Installe Convertisseur Clavier pour l'utilisateur courant (sans admin) :
# menu Demarrer (recherche Windows), touche globale, entree de desinstallation.
# Usage : powershell -ExecutionPolicy Bypass -File installer.ps1
#   [-Exe chemin-de-l-exe] [-Raccourci 'CTRL+ALT+K']
# L'exe est cherche a cote du script (ConvertisseurClavier-*.exe).
param(
  [string]$AppDir = (Join-Path $env:LOCALAPPDATA 'Programs\ConvertisseurClavier'),
  [string]$MenuDir = (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'),
  [string]$RegName = 'ConvertisseurClavier',
  [string]$Nom = 'Convertisseur Clavier',
  [string]$Raccourci = 'CTRL+ALT+K',
  [string]$Exe = ''
)
$ErrorActionPreference = 'Stop'

if (-not $Exe) {
  $candidat = Get-ChildItem -Path $PSScriptRoot -Filter 'ConvertisseurClavier-*.exe' |
    Sort-Object Name -Descending | Select-Object -First 1
  if (-not $candidat) { Write-Host "Aucun ConvertisseurClavier-*.exe a cote du script."; exit 1 }
  $Exe = $candidat.FullName
}
if (-not (Test-Path $Exe)) { Write-Host "Introuvable : $Exe"; exit 1 }

$ver = (Get-Item $Exe).VersionInfo.ProductVersion
if (-not $ver) {
  $m = [regex]::Match([IO.Path]::GetFileName($Exe), '(\d+\.\d+\.\d+)')
  $ver = if ($m.Success) { $m.Groups[1].Value } else { 'inconnue' }
}

New-Item -ItemType Directory -Force -Path $AppDir | Out-Null
New-Item -ItemType Directory -Force -Path $MenuDir | Out-Null
Copy-Item $Exe (Join-Path $AppDir 'ConvertisseurClavier.exe') -Force
$desinstSrc = Join-Path $PSScriptRoot 'desinstaller.ps1'
if (Test-Path $desinstSrc) { Copy-Item $desinstSrc $AppDir -Force }

$lnk = Join-Path $MenuDir ($Nom + '.lnk')
$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($lnk)
$sc.TargetPath = Join-Path $AppDir 'ConvertisseurClavier.exe'
$sc.WorkingDirectory = $AppDir
$sc.Hotkey = $Raccourci
$sc.Description = 'Convertisseur de clavier Latin/Hebreu (AZERTY/QWERTY)'
$sc.Save()

$reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegName"
New-Item -Path $reg -Force | Out-Null
New-ItemProperty -Path $reg -Name 'DisplayName' -Value $Nom -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name 'DisplayVersion' -Value $ver -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name 'Publisher' -Value 'Mimran' -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name 'InstallLocation' -Value $AppDir -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name 'DisplayIcon' -Value (Join-Path $AppDir 'ConvertisseurClavier.exe') -PropertyType String -Force | Out-Null
$uninst = 'powershell -ExecutionPolicy Bypass -File "' + (Join-Path $AppDir 'desinstaller.ps1') + '"'
New-ItemProperty -Path $reg -Name 'UninstallString' -Value $uninst -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name 'NoModify' -Value 1 -PropertyType DWord -Force | Out-Null
New-ItemProperty -Path $reg -Name 'NoRepair' -Value 1 -PropertyType DWord -Force | Out-Null

Write-Host "Installe : $Nom $ver"
Write-Host "Menu Demarrer : $lnk ($Raccourci)"
