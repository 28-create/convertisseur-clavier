# Installe Convertisseur Clavier pour l'utilisateur courant (sans admin) :
# menu Demarrer (recherche Windows), touches globales, menu clic droit
# de l'Explorateur (option), entree de desinstallation.
# Usage : powershell -ExecutionPolicy Bypass -File installer.ps1
#   [-Exe chemin-de-l-exe] [-Raccourci 'CTRL+ALT+K'] [-SansMenuContextuel]
#   [-SansSurveillance] [-SansDemarrage]
# L'exe est cherche a cote du script (ConvertisseurClavier-*.exe).
# La surveillance du presse-papiers demarre avec Windows (valeur Run HKCU) ;
# -SansSurveillance la desactive, -SansDemarrage l'installe sans la lancer
# (utilise par le test en bac a sable).
# Le menu clic droit (HKCU, sans admin) ajoute :
#   fichiers *  -> "Ouvrir avec Convertisseur Clavier"
#   fichiers .txt -> "Convertir avec Convertisseur Clavier" (--convert-file)
#   dossiers + fond -> "Ouvrir (ici) avec Convertisseur Clavier"
# Note : le clic droit de Word/navigateur appartient a chaque appli et ne
# peut pas etre etendu par un installeur ; pour du texte selectionne
# partout, utilisez Ctrl+C puis Ctrl+Alt+H (presse-papiers) puis Ctrl+V.
param(
  [string]$AppDir = (Join-Path $env:LOCALAPPDATA 'Programs\ConvertisseurClavier'),
  [string]$MenuDir = (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'),
  [string]$RegName = 'ConvertisseurClavier',
  [string]$Nom = 'Convertisseur Clavier',
  [string]$Raccourci = 'CTRL+ALT+K',
  [string]$Exe = '',
  [string]$RunName = 'ConvertisseurClavier',
  [switch]$SansMenuContextuel,
  [switch]$SansSurveillance,
  [switch]$SansDemarrage,
  [string]$ShellRoot = '',
  [string]$ShellName = 'ConvertisseurClavier',
  [string]$LnkPressePapiers = 'Convertisseur Clavier - Presse-papiers',
  [string]$RaccourciPressePapiers = 'CTRL+ALT+H'
)
$ErrorActionPreference = 'Stop'

function Assert-SafeName([string]$Label, [string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value) -or $Value -match '[\\/:*?"<>|\[\]]') {
    throw "Nom invalide pour $Label : $Value"
  }
}

function New-LiteralRegKey([string]$Path) {
  if ($Path -match '^HKCU:\\(.+)$') {
    $sub = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey($Matches[1])
    if ($null -ne $sub) { $sub.Close() }
    return
  }
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -Path $Path -Force | Out-Null
  }
}

Assert-SafeName 'RegName' $RegName
Assert-SafeName 'Nom' $Nom
Assert-SafeName 'RunName' $RunName
Assert-SafeName 'ShellName' $ShellName
Assert-SafeName 'LnkPressePapiers' $LnkPressePapiers

if (-not $Exe) {
  # Tri par version numerique, pas par nom : sinon 9.9.9 passerait
  # devant 10.0.0 (comparaison alphabetique).
  $candidat = Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'ConvertisseurClavier-*.exe' |
    ForEach-Object {
      $m = [regex]::Match($_.Name, '\d+\.\d+\.\d+')
      $v = if ($m.Success) { [version]$m.Value } else { [version]'0.0.0' }
      [PSCustomObject]@{ Fichier = $_; Version = $v }
    } |
    Sort-Object -Property Version -Descending | Select-Object -First 1
  if (-not $candidat) { Write-Host "Aucun ConvertisseurClavier-*.exe a cote du script."; exit 1 }
  $Exe = $candidat.Fichier.FullName
}
if (-not (Test-Path -LiteralPath $Exe -PathType Leaf)) { Write-Host "Introuvable : $Exe"; exit 1 }

$ver = (Get-Item -LiteralPath $Exe).VersionInfo.ProductVersion
if (-not $ver) {
  $m = [regex]::Match([IO.Path]::GetFileName($Exe), '(\d+\.\d+\.\d+)')
  $ver = if ($m.Success) { $m.Groups[1].Value } else { 'inconnue' }
}

if (-not (Test-Path -LiteralPath $AppDir)) { New-Item -ItemType Directory -Force -Path $AppDir | Out-Null }
if (-not (Test-Path -LiteralPath $MenuDir)) { New-Item -ItemType Directory -Force -Path $MenuDir | Out-Null }
$exeInst = Join-Path $AppDir 'ConvertisseurClavier.exe'
# Mise a jour : l'ancien guetteur verrouille l'exe, on l'arrete avant la copie.
if (Test-Path -LiteralPath $exeInst) {
  try {
    Start-Process -FilePath $exeInst -ArgumentList '--paste-stop' -WindowStyle Hidden -Wait | Out-Null
  } catch {
    # Ancienne version sans --paste-stop (ou exe de test) : on continue.
  }
}
Copy-Item -LiteralPath $Exe -Destination $exeInst -Force
$desinstSrc = Join-Path $PSScriptRoot 'desinstaller.ps1'
if (Test-Path -LiteralPath $desinstSrc) { Copy-Item -LiteralPath $desinstSrc -Destination $AppDir -Force }

$lnk = Join-Path $MenuDir ($Nom + '.lnk')
$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($lnk)
$sc.TargetPath = $exeInst
$sc.WorkingDirectory = $AppDir
$sc.Hotkey = $Raccourci
$sc.Description = 'Convertisseur de clavier Latin/Hebreu (AZERTY/QWERTY)'
$sc.Save()

# Touche globale presse-papiers : selectionnez le texte partout
# (Word, navigateur, barre de recherche), Ctrl+C, Ctrl+Alt+H, Ctrl+V.
# L'exe convertit lui-meme le presse-papiers (Python inutile).
$lnkClip = Join-Path $MenuDir ($LnkPressePapiers + '.lnk')
$sc2 = $shell.CreateShortcut($lnkClip)
$sc2.TargetPath = $exeInst
$sc2.Arguments = '--convert-clipboard'
$sc2.WorkingDirectory = $AppDir
$sc2.Hotkey = $RaccourciPressePapiers
$sc2.Description = 'Convertit le presse-papiers Latin<->Hebreu (Ctrl+C, Ctrl+Alt+H, Ctrl+V)'
$sc2.Save()

$reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$RegName"
New-LiteralRegKey $reg
New-ItemProperty -LiteralPath $reg -Name 'DisplayName' -Value $Nom -PropertyType String -Force | Out-Null
New-ItemProperty -LiteralPath $reg -Name 'DisplayVersion' -Value $ver -PropertyType String -Force | Out-Null
New-ItemProperty -LiteralPath $reg -Name 'Publisher' -Value 'Mimran' -PropertyType String -Force | Out-Null
New-ItemProperty -LiteralPath $reg -Name 'InstallLocation' -Value $AppDir -PropertyType String -Force | Out-Null
New-ItemProperty -LiteralPath $reg -Name 'DisplayIcon' -Value $exeInst -PropertyType String -Force | Out-Null
$uninst = 'powershell -ExecutionPolicy Bypass -File "' + (Join-Path $AppDir 'desinstaller.ps1') + '"'
New-ItemProperty -LiteralPath $reg -Name 'UninstallString' -Value $uninst -PropertyType String -Force | Out-Null
New-ItemProperty -LiteralPath $reg -Name 'NoModify' -Value 1 -PropertyType DWord -Force | Out-Null
New-ItemProperty -LiteralPath $reg -Name 'NoRepair' -Value 1 -PropertyType DWord -Force | Out-Null

# Surveillance du presse-papiers au demarrage de session (HKCU, sans admin).
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
if (-not $SansSurveillance) {
  New-LiteralRegKey $runKey
  $runVal = '"' + $exeInst + '" --paste-watch'
  New-ItemProperty -LiteralPath $runKey -Name $RunName -Value $runVal -PropertyType String -Force | Out-Null
  Write-Host "Surveillance : demarrage automatique ($RunName)"
} else {
  Remove-ItemProperty -LiteralPath $runKey -Name $RunName -ErrorAction SilentlyContinue
  Write-Host 'Surveillance : desactivee (-SansSurveillance)'
}

if (-not $SansMenuContextuel) {
  $classes = if ($ShellRoot) { $ShellRoot } else { 'HKCU:\Software\Classes' }
  # Fichiers * : ouvrir dans l'application (contenu precharge).
  $k = "$classes\*\shell\$ShellName"
  New-LiteralRegKey $k
  New-ItemProperty -LiteralPath $k -Name 'MUIVerb' -Value 'Ouvrir avec Convertisseur Clavier' -PropertyType String -Force | Out-Null
  New-ItemProperty -LiteralPath $k -Name 'Icon' -Value "$exeInst,0" -PropertyType String -Force | Out-Null
  New-ItemProperty -LiteralPath $k -Name 'Position' -Value 'Middle' -PropertyType String -Force | Out-Null
  New-LiteralRegKey "$k\command"
  New-ItemProperty -LiteralPath "$k\command" -Name '(Default)' -Value ('"' + $exeInst + '" -- "%1"') -PropertyType String -Force | Out-Null
  # Fichiers .txt : conversion directe vers .converti.txt.
  $k = "$classes\SystemFileAssociations\.txt\shell\$ShellName.Convertir"
  New-LiteralRegKey $k
  New-ItemProperty -LiteralPath $k -Name 'MUIVerb' -Value 'Convertir avec Convertisseur Clavier' -PropertyType String -Force | Out-Null
  New-ItemProperty -LiteralPath $k -Name 'Icon' -Value "$exeInst,0" -PropertyType String -Force | Out-Null
  New-LiteralRegKey "$k\command"
  New-ItemProperty -LiteralPath "$k\command" -Name '(Default)' -Value ('"' + $exeInst + '" --convert-file="%1"') -PropertyType String -Force | Out-Null
  # Dossiers : ouvrir l'application.
  $k = "$classes\Directory\shell\$ShellName"
  New-LiteralRegKey $k
  New-ItemProperty -LiteralPath $k -Name 'MUIVerb' -Value 'Ouvrir avec Convertisseur Clavier' -PropertyType String -Force | Out-Null
  New-ItemProperty -LiteralPath $k -Name 'Icon' -Value "$exeInst,0" -PropertyType String -Force | Out-Null
  New-LiteralRegKey "$k\command"
  New-ItemProperty -LiteralPath "$k\command" -Name '(Default)' -Value ('"' + $exeInst + '"') -PropertyType String -Force | Out-Null
  # Fond d'un dossier : ouvrir l'application ici.
  $k = "$classes\Directory\Background\shell\$ShellName"
  New-LiteralRegKey $k
  New-ItemProperty -LiteralPath $k -Name 'MUIVerb' -Value 'Ouvrir Convertisseur Clavier ici' -PropertyType String -Force | Out-Null
  New-ItemProperty -LiteralPath $k -Name 'Icon' -Value "$exeInst,0" -PropertyType String -Force | Out-Null
  New-LiteralRegKey "$k\command"
  New-ItemProperty -LiteralPath "$k\command" -Name '(Default)' -Value ('"' + $exeInst + '"') -PropertyType String -Force | Out-Null
  Write-Host "Menu clic droit : installe ($ShellName)"
} else {
  Write-Host 'Menu clic droit : ignore (-SansMenuContextuel)'
}

Write-Host "Installe : $Nom $ver"
Write-Host "Menu Demarrer : $lnk ($Raccourci)"
Write-Host "Presse-papiers : $lnkClip ($RaccourciPressePapiers)"

if (-not $SansSurveillance -and -not $SansDemarrage) {
  try {
    Start-Process -FilePath $exeInst -ArgumentList '--paste-watch' -WindowStyle Hidden | Out-Null
    Write-Host 'Surveillance : demarree'
  } catch {
    Write-Host ('Surveillance : demarrage impossible : ' + $_.Exception.Message)
  }
}
