[Setup]
AppId={{FBREEL-DOWNLOADER-0001}
AppName=Facebook Reel Downloader
AppVersion=1.0.0
AppPublisher=Facebook Reel Downloader
DefaultDirName={autopf}\Facebook Reel Downloader
DefaultGroupName=Facebook Reel Downloader
OutputDir=installer
OutputBaseFilename=FacebookReelDownloader-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\FacebookReelDownloader.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Facebook Reel Downloader"; Filename: "{app}\FacebookReelDownloader.exe"
Name: "{group}\Uninstall Facebook Reel Downloader"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Facebook Reel Downloader"; Filename: "{app}\FacebookReelDownloader.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\FacebookReelDownloader.exe"; Description: "Launch Facebook Reel Downloader now"; Flags: nowait postinstall skipifsilent
