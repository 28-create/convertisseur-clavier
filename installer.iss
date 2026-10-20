; Installation vraie application : assistant Setup.exe (Inno Setup 6).
; Usage : python build_setup.py   (compile dist\Setup_ConvertisseurClavier-X.Y.Z.exe)
; La version ci-dessous est GENEREE depuis convertisseur.html :
;   python gen_version.py   (ne pas la modifier a la main).
#define MyAppVersion "1.12.4"
#define MyAppExe "ConvertisseurClavier-" + MyAppVersion + ".exe"

[Setup]
AppId=ConvertisseurClavier
AppName=Convertisseur Clavier
AppVersion={#MyAppVersion}
AppVerName=Convertisseur Clavier {#MyAppVersion}
AppPublisher=Mimran
AppPublisherURL=https://github.com/28-create/convertisseur-clavier
VersionInfoCompany=Mimran
VersionInfoDescription=Installation de Convertisseur Clavier
VersionInfoProductName=Convertisseur Clavier
VersionInfoProductVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\ConvertisseurClavier
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=Setup_ConvertisseurClavier-{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=yes
SetupIconFile=app.ico
UninstallDisplayIcon={app}\ConvertisseurClavier.exe
WizardSmallImageFile=installer-logo.png

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"

[CustomMessages]
french.TaskContextMenu=Ajouter au menu clic droit de l'Explorateur (ouvrir / convertir)
english.TaskContextMenu=Add to the Explorer context menu (open / convert)
hebrew.TaskContextMenu=הוסף לתפריט הקשר של סייר הקבצים (פתיחה / המרה)
french.TaskSurveillance=Surveiller le presse-papiers au démarrage (propose la conversion avant Ctrl+V)
english.TaskSurveillance=Monitor the clipboard at startup (proposes conversion before Ctrl+V)
hebrew.TaskSurveillance=נטר את לוח הגזירים בעת האתחול (מציע המרה לפני Ctrl+V)
french.WindowsIntegration=Intégration Windows :
english.WindowsIntegration=Windows integration:
hebrew.WindowsIntegration=שילוב ב-Windows:
french.ClipboardShortcutName=Convertir le presse-papiers
english.ClipboardShortcutName=Convert clipboard
hebrew.ClipboardShortcutName=המר לוח גזירים
french.IconAppComment=Convertisseur de clavier Latin/Hébreu (AZERTY/QWERTY)
english.IconAppComment=Latin/Hebrew keyboard converter (AZERTY/QWERTY)
hebrew.IconAppComment=ממיר מקלדת לטינית/עברית (AZERTY/QWERTY)
french.IconClipboardComment=Convertit le presse-papiers (Ctrl+C, Ctrl+Alt+H, Ctrl+V)
english.IconClipboardComment=Converts the clipboard (Ctrl+C, Ctrl+Alt+H, Ctrl+V)
hebrew.IconClipboardComment=ממיר את לוח הגזירים (Ctrl+C, Ctrl+Alt+H, Ctrl+V)
french.RunSurveillance=Lancer la surveillance du presse-papiers
english.RunSurveillance=Start clipboard monitoring
hebrew.RunSurveillance=הפעל ניטור לוח גזירים
french.ContextOpen=Ouvrir avec Convertisseur Clavier
english.ContextOpen=Open with Convertisseur Clavier
hebrew.ContextOpen=פתח עם Convertisseur Clavier
french.ContextConvert=Convertir avec Convertisseur Clavier
english.ContextConvert=Convert with Convertisseur Clavier
hebrew.ContextConvert=המר עם Convertisseur Clavier
french.ContextOpenHere=Ouvrir Convertisseur Clavier ici
english.ContextOpenHere=Open Convertisseur Clavier here
hebrew.ContextOpenHere=פתח את Convertisseur Clavier כאן

[Tasks]
Name: "contextmenu"; Description: "{cm:TaskContextMenu}"; GroupDescription: "{cm:WindowsIntegration}"
Name: "surveillance"; Description: "{cm:TaskSurveillance}"; GroupDescription: "{cm:WindowsIntegration}"
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExe}"; DestDir: "{app}"; DestName: "ConvertisseurClavier.exe"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Convertisseur Clavier"; Filename: "{app}\ConvertisseurClavier.exe"; HotKey: "ctrl+alt+k"; Comment: "{cm:IconAppComment}"
Name: "{autoprograms}\{cm:ClipboardShortcutName}"; Filename: "{app}\ConvertisseurClavier.exe"; Parameters: "--convert-clipboard"; HotKey: "ctrl+alt+h"; Comment: "{cm:IconClipboardComment}"
Name: "{autodesktop}\Convertisseur Clavier"; Filename: "{app}\ConvertisseurClavier.exe"; Tasks: desktopicon

[Registry]
; Clic droit sur un fichier : ouvrir dans l'application.
Root: HKCU; Subkey: "Software\Classes\*\shell\ConvertisseurClavier"; ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ContextOpen}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\ConvertisseurClavier"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ConvertisseurClavier.exe,0"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\ConvertisseurClavier"; ValueType: string; ValueName: "Position"; ValueData: "Middle"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\ConvertisseurClavier\command"; ValueType: string; ValueData: """{app}\ConvertisseurClavier.exe"" ""%1"""; Tasks: contextmenu
; Clic droit sur un .txt : conversion directe vers .converti.txt.
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.txt\shell\ConvertirClavier"; ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ContextConvert}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.txt\shell\ConvertirClavier"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ConvertisseurClavier.exe,0"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.txt\shell\ConvertirClavier\command"; ValueType: string; ValueData: """{app}\ConvertisseurClavier.exe"" --convert-file ""%1"""; Tasks: contextmenu
; Clic droit sur un dossier : ouvrir l'application.
Root: HKCU; Subkey: "Software\Classes\Directory\shell\ConvertisseurClavier"; ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ContextOpen}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\ConvertisseurClavier"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ConvertisseurClavier.exe,0"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\ConvertisseurClavier\command"; ValueType: string; ValueData: """{app}\ConvertisseurClavier.exe"" ""%1"""; Tasks: contextmenu
; Clic droit sur le fond d'un dossier : ouvrir l'application ici.
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\ConvertisseurClavier"; ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ContextOpenHere}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\ConvertisseurClavier"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ConvertisseurClavier.exe,0"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\ConvertisseurClavier\command"; ValueType: string; ValueData: """{app}\ConvertisseurClavier.exe"" ""%V"""; Tasks: contextmenu
; Surveillance du presse-papiers au demarrage de session (option).
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "ConvertisseurClavier"; ValueData: """{app}\ConvertisseurClavier.exe"" --paste-watch"; Flags: uninsdeletevalue; Tasks: surveillance

[Run]
Filename: "{app}\ConvertisseurClavier.exe"; Description: "{cm:LaunchProgram,Convertisseur Clavier}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\ConvertisseurClavier.exe"; Parameters: "--paste-watch"; Description: "{cm:RunSurveillance}"; Flags: nowait postinstall skipifsilent; Tasks: surveillance

[UninstallRun]
; Arrete le guetteur avant de supprimer l'exe (sinon le fichier reste verrouille).
Filename: "{app}\ConvertisseurClavier.exe"; Parameters: "--paste-stop"; Flags: runhidden waituntilterminated; RunOnceId: "StopSurveillance"

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Result := '';
  // Une mise a jour doit pouvoir remplacer l'exe : on arrete l'ancien guetteur.
  if FileExists(ExpandConstant('{app}\ConvertisseurClavier.exe')) then
    Exec(ExpandConstant('{app}\ConvertisseurClavier.exe'),
         '--paste-stop', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;
