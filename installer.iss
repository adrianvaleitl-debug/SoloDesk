#define MyAppName "SoloDesk"
#define MyAppVersion "1.4"
#define MyAppPublisher "Adrian Vale"
#define MyAppExeName "SoloDesk.exe"
[Setup]
AppId={{B7B3C8C0-CC0C-4C16-9D6B-5F6A3A0C9101}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\SoloDesk
DefaultGroupName=SoloDesk
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer
OutputBaseFilename=SoloDesk-Setup-V1.4
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\solodesk.ico
UninstallDisplayIcon={app}\SoloDesk.exe
CloseApplications=yes
RestartApplications=yes
ArchitecturesInstallIn64BitMode=x64
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
[Files]
Source: "dist\SoloDesk\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\SoloDesk"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\solodesk.ico"
Name: "{autodesktop}\SoloDesk"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\solodesk.ico"; Tasks: desktopicon
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch SoloDesk"; Flags: postinstall nowait skipifsilent
