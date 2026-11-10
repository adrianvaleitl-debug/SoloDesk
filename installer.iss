#define MyAppName "SoloDesk"
#define MyAppVersion "1.2"
#define MyAppPublisher "SoloDesk"
#define MyAppExeName "SoloDesk.exe"
[Setup]
AppId={{B7B3C8C0-CC0C-4C16-9D6B-5F6A3A0C9101}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SoloDesk
DefaultGroupName=SoloDesk
OutputDir=installer
OutputBaseFilename=SoloDesk-Setup-V1.2
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
[Files]
Source: "dist\SoloDesk\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\SoloDesk"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\SoloDesk"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch SoloDesk"; Flags: postinstall nowait skipifsilent
