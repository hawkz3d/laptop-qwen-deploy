$out = "C:\probe2.txt"
"=== SOGOU PROC PARENT ===" | Out-File $out -Encoding utf8
Get-CimInstance Win32_Process | Where-Object {$_.Name -match 'Sogou|SGTool'} | ForEach-Object { $_.ProcessId.ToString() + " " + $_.Name + " PPID=" + $_.ParentProcessId } | Out-File $out -Append -Encoding utf8
"=== ALL RUN/RUNONCE/STARTUPAPPROVED ===" | Out-File $out -Append -Encoding utf8
$paths = @(
 "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run",
 "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce",
 "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce",
 "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce",
 "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
 "HKLM:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
 "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder",
 "HKLM:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"
)
foreach ($p in $paths) {
  $item = Get-ItemProperty $p -ErrorAction SilentlyContinue
  if ($item) {
    $item.PSObject.Properties | Where-Object {$_.Name -notmatch '^PS'} | ForEach-Object { $p + " | " + $_.Name } | Out-File $out -Append -Encoding utf8
  }
}
"=== STARTUP FOLDERS ===" | Out-File $out -Append -Encoding utf8
Get-ChildItem "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp" -ErrorAction SilentlyContinue | ForEach-Object { "ProgData: " + $_.Name } | Out-File $out -Append -Encoding utf8
Get-ChildItem "<USERS_DIR>\*\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\StartUp" -ErrorAction SilentlyContinue | ForEach-Object { "User: " + $_.FullName } | Out-File $out -Append -Encoding utf8
"=== CROSSDEVICE / CDP SERVICES ===" | Out-File $out -Append -Encoding utf8
Get-Service | Where-Object {$_.Name -match 'cross|cdp|device'} | ForEach-Object { $_.Name + " | " + $_.Status + " | " + $_.StartType } | Out-File $out -Append -Encoding utf8
"=== IME related Sogou ===" | Out-File $out -Append -Encoding utf8
Get-ChildItem "HKLM:\SOFTWARE\Microsoft\CTF\TIP" -ErrorAction SilentlyContinue | ForEach-Object { $_.Name } | Out-File $out -Append -Encoding utf8
"=== DONE ===" | Out-File $out -Append -Encoding utf8
