# Test bout-en-bout de l'installeur (bac a sable, sans admin) :
# installe avec deux faux exe versionnes (9.9.9 et 10.0.0), verifie que
# le plus recent (10.0.0) est choisi, menu + touches + registre + menu
# clic droit (dans une ruche de test), puis desinstalle via la copie
# installee et verifie le menage.
# Usage : powershell -NoProfile -ExecutionPolicy Bypass -File test_installer.ps1
$ErrorActionPreference = 'Stop'
# $env:TEMP peut contenir un nom court 8.3 (ex. RUNNER~1) alors que COM
# enregistre le nom long : on canonise pour comparer des chaines egales.
$tmp = Join-Path (Get-Item $env:TEMP).FullName 'TestInstallConv'
$reg = 'ConvertisseurClavier-Test'
$nom = 'Convertisseur Clavier Test'
$lnkClipNom = 'Convertisseur Clavier Test Presse-papiers'
$shellName = 'ConvertisseurClavier-Test'
$shellRoot = 'HKCU:\Software\TestInstallConv-Classes'
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
if (Test-Path $shellRoot) { Remove-Item $shellRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$faux9 = Join-Path $tmp 'ConvertisseurClavier-9.9.9-TEST.exe'
$faux10 = Join-Path $tmp 'ConvertisseurClavier-10.0.0-TEST.exe'
[IO.File]::WriteAllBytes($faux9, [byte[]]@(77, 90))
[IO.File]::WriteAllBytes($faux10, [byte[]]@(77, 90))
Copy-Item "$PSScriptRoot\desinstaller.ps1" (Join-Path $tmp 'desinstaller.ps1')
Copy-Item "$PSScriptRoot\installer.ps1" (Join-Path $tmp 'installer.ps1')

& (Join-Path $tmp 'installer.ps1') -AppDir (Join-Path $tmp 'App') -MenuDir (Join-Path $tmp 'Menu') -RegName $reg -Nom $nom -LnkPressePapiers $lnkClipNom -ShellRoot $shellRoot -ShellName $shellName
$lnk = Join-Path (Join-Path $tmp 'Menu') ($nom + '.lnk')
if (-not (Test-Path $lnk)) { Write-Host 'ECHEC : .lnk absent'; exit 1 }
$sc = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
# Windows normalise l'ordre : CTRL+ALT+K est stocke 'Alt+Ctrl+K'
$ok = ($sc.TargetPath -eq (Join-Path $tmp 'App\ConvertisseurClavier.exe')) -and ($sc.Hotkey -eq 'Alt+Ctrl+K')
Write-Host ('cible=' + $sc.TargetPath)
Write-Host ('touche=' + $sc.Hotkey)
$lnk2 = Join-Path (Join-Path $tmp 'Menu') ($lnkClipNom + '.lnk')
$sc2 = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk2)
$ok = $ok -and (Test-Path $lnk2) -and ($sc2.Arguments -eq '--convert-clipboard') -and ($sc2.Hotkey -eq 'Alt+Ctrl+H')
Write-Host ('presse-papiers=' + $sc2.Arguments + '/' + $sc2.Hotkey)
$rk = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$reg"
$props = Get-ItemProperty $rk
$ok = $ok -and ($props.DisplayVersion -eq '10.0.0') -and ($props.DisplayName -eq $nom)
$ok = $ok -and (Test-Path (Join-Path $tmp 'App\desinstaller.ps1'))
Write-Host ('registre=' + $props.DisplayVersion + '/' + $props.DisplayName)
Write-Host ('desinst-copie=' + (Test-Path (Join-Path $tmp 'App\desinstaller.ps1')))
# Menu clic droit (ruche de test) : 4 entrees + verbes.
$exeAttendu = Join-Path $tmp 'App\ConvertisseurClavier.exe'
$cmda = (Get-ItemProperty -LiteralPath "$shellRoot\*\shell\$shellName\command").'(Default)'
$cmdt = (Get-ItemProperty -LiteralPath "$shellRoot\SystemFileAssociations\.txt\shell\$shellName.Convertir\command").'(Default)'
$cmdd = (Get-ItemProperty -LiteralPath "$shellRoot\Directory\shell\$shellName\command").'(Default)'
$cmdb = (Get-ItemProperty -LiteralPath "$shellRoot\Directory\Background\shell\$shellName\command").'(Default)'
$ok = $ok -and ($cmda -eq ('"' + $exeAttendu + '" "%1"'))
$ok = $ok -and ($cmdt -eq ('"' + $exeAttendu + '" --convert-file "%1"'))
$ok = $ok -and ($cmdd -eq ('"' + $exeAttendu + '" "%1"'))
$ok = $ok -and ($cmdb -eq ('"' + $exeAttendu + '" "%V"'))
Write-Host ('clic-droit=' + $cmda + ' | ' + $cmdt)
Write-Host ('checks-install=' + $ok)

& (Join-Path $tmp 'App\desinstaller.ps1') -AppDir (Join-Path $tmp 'App') -MenuDir (Join-Path $tmp 'Menu') -RegName $reg -Nom $nom -LnkPressePapiers $lnkClipNom -ShellRoot $shellRoot -ShellName $shellName
$restes = @()
if (Test-Path $lnk) { $restes += "lnk:$lnk" }
if (Test-Path $lnk2) { $restes += "lnk:$lnk2" }
if (Test-Path (Join-Path $tmp 'App')) { $restes += 'App' }
if (Test-Path $rk) { $restes += "reg:$rk" }
foreach ($k in @(
  "$shellRoot\*\shell\$shellName",
  "$shellRoot\SystemFileAssociations\.txt\shell\$shellName.Convertir",
  "$shellRoot\Directory\shell\$shellName",
  "$shellRoot\Directory\Background\shell\$shellName"
)) {
  if (Test-Path -LiteralPath $k) { $restes += "shell:$k" }
}
$ok = $ok -and ($restes.Count -eq 0)
if (Test-Path $shellRoot) { Remove-Item $shellRoot -Recurse -Force }
Remove-Item $tmp -Recurse -Force
if (-not $ok) { Write-Host ('ECHEC : verification, restes=' + ($restes -join ' | ')); exit 1 }
Write-Host 'INSTALL-OK'
