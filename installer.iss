#ifndef ARCH
  #define ARCH "x64"
#endif

[Setup]
AppId={{FBREEL-DOWNLOADER-0001}
AppName=Facebook Reel Downloader
AppVersion=1.0.2
AppPublisher=Facebook Reel Downloader
DefaultDirName={autopf}\Facebook Reel Downloader
DefaultGroupName=Facebook Reel Downloader
OutputDir=installer
OutputBaseFilename=FacebookReelDownloader-Setup-{#ARCH}
SetupIconFile=media\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=yes
#if ARCH == "x64"
ArchitecturesInstallIn64BitMode=x64compatible
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\{#ARCH}\FacebookReelDownloader.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Facebook Reel Downloader"; Filename: "{app}\FacebookReelDownloader.exe"
Name: "{group}\Uninstall Facebook Reel Downloader"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Facebook Reel Downloader"; Filename: "{app}\FacebookReelDownloader.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\FacebookReelDownloader.exe"; Description: "Launch Facebook Reel Downloader now"; Flags: nowait postinstall skipifsilent
