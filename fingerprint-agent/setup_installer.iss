; Inno Setup Script — Inventor Fingerprint Agent O'rnatuvchisi
; Inno Setup 6.x dan yuklab oling: https://jrsoftware.org/isdl.php

[Setup]
AppName=UzLombard
AppVersion=2.0
AppPublisher=UzLombard System
DefaultDirName={commonpf}\UzLombard
DefaultGroupName=UzLombard
OutputBaseFilename=UzLombard_Setup
OutputDir=installer_output
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=uzlombard.ico
UninstallDisplayIcon={app}\UzLombard.exe

; O'rnatishdan keyin sayt ochilsin
[Run]
Filename: "{app}\UzLombard.exe"; Description: "Dasturni hozir ishga tushirish"; Flags: postinstall nowait skipifsilent

[Files]
; Asosiy dastur
Source: "dist\InventorAgent.exe"; DestDir: "{app}"; DestName: "UzLombard.exe"; Flags: ignoreversion
; Ikonka
Source: "uzlombard.ico"; DestDir: "{app}"; Flags: ignoreversion

; libzkfp.dll — System32 va SysWOW64 ga ham
Source: "libzkfp.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "libzkfp.dll"; DestDir: "{sys}"; Flags: ignoreversion uninsneveruninstall
Source: "libzkfp.dll"; DestDir: "{syswow64}"; Flags: ignoreversion uninsneveruninstall; Check: IsWin64

; config.json (sayt URL si)
Source: "dist\InventorAgent\config.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist; Check: FileExists(ExpandConstant('{src}\dist\InventorAgent\config.json'))

[Icons]
; Desktop yorlig'i
Name: "{userdesktop}\UzLombard"; Filename: "{app}\UzLombard.exe"; IconFilename: "{app}\uzlombard.ico"
; Boshlang'ich menyu
Name: "{group}\UzLombard"; Filename: "{app}\UzLombard.exe"; IconFilename: "{app}\uzlombard.ico"
Name: "{group}\O'chirish"; Filename: "{uninstallexe}"

[Registry]
; Windows ishga tushganda avtomatik ishga tushirish
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "UzLombard"; ValueData: """{app}\UzLombard.exe"""; Flags: uninsdeletevalue

[UninstallDelete]
Type: files; Name: "{app}\logs\*"
Type: dirifempty; Name: "{app}\logs"
Type: dirifempty; Name: "{app}"

[Messages]
WelcomeLabel2=Bu dastur Inventor tizimi uchun barmoq izi agentini o'rnatadi.%n%nDastur o'rnatilgandan so'ng, kompyuter har ishga tushganda avtomatik ravishda fonda ishlaydi va barmoq izi imzolash imkonini beradi.
FinishedHeadingLabel=O'rnatish muvaffaqiyatli yakunlandi!
FinishedLabel=Inventor Fingerprint Agent o'rnatildi.%n%nDastur kompyuter har yoqilganda avtomatik ishga tushadi.%n%n"Dasturni hozir ishga tushirish" belgilab "Tugallash" tugmasini bosing.
