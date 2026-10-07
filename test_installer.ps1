# Test bout-en-bout de l'installeur (bac a sable, sans admin) :
# installe un faux exe versionne, verifie menu + touche + registre,
# puis desinstalle via la copie installee et verifie le menage.
# Usage : powershell -ExecutionPolicy Bypass -File test_installer.ps1
$ErrorActionPreference = 'Stop'
$tmp = Join-Path $env:TEMP 'TestInstallConv'
$reg = 'ConvertisseurClavier-Test'
$nom = 'Convertisseur Clavier Test'
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$faux = Join-Path $tmp 'ConvertisseurClavier-9.9.9-TEST.exe'
[IO.File]::WriteAllBytes($faux, [byte[]]@(77, 90))
Copy-Item "$PSScriptRoot\desinstaller.ps1" (Join-Path $tmp 'desinstaller.ps1')

& "$PSScriptRoot\installer.ps1" -AppDir (Join-Path $tmp 'App') -MenuDir (Join-Path $tmp 'Menu') -RegName $reg -Nom $nom -Exe $faux
$lnk = Join-Path (Join-Path $tmp 'Menu') ($nom + '.lnk')
if (-not (Test-Path $lnk)) { Write-Host 'ECHEC : .lnk absent'; exit 1 }
$sc = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
# Windows normalise l'ordre : CTRL+ALT+K est stocke 'Alt+Ctrl+K'
$ok = ($sc.TargetPath -eq (Join-Path $tmp 'App\ConvertisseurClavier.exe')) -and ($sc.Hotkey -eq 'Alt+Ctrl+K')
Write-Host ('cible=' + $sc.TargetPath)
Write-Host ('touche=' + $sc.Hotkey)
$rk = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$reg"
$ok = $ok -and ((Get-ItemProperty $rk).DisplayVersion -eq '9.9.9') -and ((Get-ItemProperty $rk).DisplayName -eq $nom)
$ok = $ok -and (Test-Path (Join-Path $tmp 'App\desinstaller.ps1'))
Write-Host ('registre=' + (Get-ItemProperty $rk).DisplayVersion)

& (Join-Path $tmp 'App\desinstaller.ps1') -AppDir (Join-Path $tmp 'App') -MenuDir (Join-Path $tmp 'Menu') -RegName $reg -Nom $nom
$ok = $ok -and (-not (Test-Path $lnk)) -and (-not (Test-Path (Join-Path $tmp 'App'))) -and (-not (Test-Path $rk))
Remove-Item $tmp -Recurse -Force
if (-not $ok) { Write-Host 'ECHEC : verification'; exit 1 }
Write-Host 'INSTALL-OK'
