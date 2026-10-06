# Cree un raccourci Windows vers fix-presse-papiers.bat avec touche globale.
# Usage : powershell -ExecutionPolicy Bypass -File installer-raccourci.ps1
#   [-Destination "$env:USERPROFILE\Desktop"] [-Nom 'Fix clavier'] [-Raccourci 'CTRL+ALT+H']
# Puis : selectionner le texte > Ctrl+C > Ctrl+Alt+H > Ctrl+V
param(
  [string]$Destination = "$env:USERPROFILE\Desktop",
  [string]$Nom = 'Fix clavier',
  [string]$Raccourci = 'CTRL+ALT+H'
)
$bat = Join-Path $PSScriptRoot 'fix-presse-papiers.bat'
if (-not (Test-Path $bat)) { Write-Host "Introuvable : $bat"; exit 1 }
if (-not (Test-Path $Destination)) { Write-Host "Dossier introuvable : $Destination"; exit 1 }
$lnk = Join-Path $Destination ($Nom + '.lnk')
$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($lnk)
$sc.TargetPath = $bat
$sc.WorkingDirectory = $PSScriptRoot
$sc.Hotkey = $Raccourci
$sc.Description = 'Convertit le presse-papiers Latin<->Hebreu / QWERTY<->AZERTY'
$sc.Save()
Write-Host "Cree : $lnk ($Raccourci)"
