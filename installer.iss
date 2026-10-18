; Installation vraie application : assistant Setup.exe (Inno Setup 6).
; Usage : python build_setup.py   (compile dist\Setup_ConvertisseurClavier-X.Y.Z.exe)
; La version ci-dessous est GENEREE depuis convertisseur.html :
;   python gen_version.py   (ne pas la modifier a la main).
#define MyAppVersion "1.9.0"
#define MyAppExe "ConvertisseurClavier-" + MyAppVersion + ".exe"

[Setup]
AppId={{E52AB6FD-CFB5-483B-AE1F-0614FE930D83}}
AppName=Convertisseur Clavier
AppVersion={#MyAppVersion}
AppVerName=Convertisseur Clavier {#MyAppVersion}
AppPublisher=Mimran
AppPublisherURL=https://github.com/28-create/convertisseur-clavier
DefaultDirName={localappdata}\Programs\ConvertisseurClavier
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=Setup_ConvertisseurClavier-{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "contextmenu"; Description: "Ajouter au menu clic droit de l'Explorateur (ouvrir / convertir)"; GroupDescription: "Intégration Windows :"; Flags: checkedonce
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExe}"; DestDir: "{app}"; DestName: "ConvertisseurClavier.exe"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Convertisseur Clavier"; Filename: "{app}\ConvertisseurClavier.exe"; HotKey: "ctrl+alt+k"; Comment: "Convertisseur de clavier Latin/Hebreu (AZERTY/QWERTY)"
Name: "{autoprograms}\Convertir le presse-papiers"; Filename: "{app}\ConvertisseurClavier.exe"; Parameters: "--convert-clipboard"; HotKey: "ctrl+alt+h"; Comment: "Convertit le presse-papiers (Ctrl+C, Ctrl+Alt+H, Ctrl+V)"
Name: "{autodesktop}\Convertisseur Clavier"; Filename: "{app}\ConvertisseurClavier.exe"; Tasks: desktopicon

[Registry]
; Clic droit sur un fichier : ouvrir dans l'application.
Root: HKCU; Subkey: "Software\Classes\*\shell\ConvertisseurClavier"; ValueType: string; ValueName: "MUIVerb"; ValueData: "Ouvrir avec Convertisseur Clavier"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\ConvertisseurClavier"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ConvertisseurClavier.exe,0"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\ConvertisseurClavier"; ValueType: string; ValueName: "Position"; ValueData: "Middle"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\ConvertisseurClavier\command"; ValueType: string; ValueData: """{app}\ConvertisseurClavier.exe"" ""%1"""; Tasks: contextmenu
; Clic droit sur un .txt : conversion directe vers .converti.txt.
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.txt\shell\ConvertirClavier"; ValueType: string; ValueName: "MUIVerb"; ValueData: "Convertir avec Convertisseur Clavier"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.txt\shell\ConvertirClavier"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ConvertisseurClavier.exe,0"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.txt\shell\ConvertirClavier\command"; ValueType: string; ValueData: """{app}\ConvertisseurClavier.exe"" --convert-file ""%1"""; Tasks: contextmenu
; Clic droit sur un dossier : ouvrir l'application.
Root: HKCU; Subkey: "Software\Classes\Directory\shell\ConvertisseurClavier"; ValueType: string; ValueName: "MUIVerb"; ValueData: "Ouvrir avec Convertisseur Clavier"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\ConvertisseurClavier"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ConvertisseurClavier.exe,0"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\ConvertisseurClavier\command"; ValueType: string; ValueData: """{app}\ConvertisseurClavier.exe"" ""%1"""; Tasks: contextmenu
; Clic droit sur le fond d'un dossier : ouvrir l'application ici.
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\ConvertisseurClavier"; ValueType: string; ValueName: "MUIVerb"; ValueData: "Ouvrir Convertisseur Clavier ici"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\ConvertisseurClavier"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ConvertisseurClavier.exe,0"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\ConvertisseurClavier\command"; ValueType: string; ValueData: """{app}\ConvertisseurClavier.exe"" ""%V"""; Tasks: contextmenu

[Run]
Filename: "{app}\ConvertisseurClavier.exe"; Description: "{cm:LaunchProgram,Convertisseur Clavier}"; Flags: nowait postinstall skipifsilent
