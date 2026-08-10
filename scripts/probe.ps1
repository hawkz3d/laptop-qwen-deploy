$out = "C:\probe.txt"
"=== RUN (HKCU) ===" | Out-File $out -Encoding utf8
$r = Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -ErrorAction SilentlyContinue
$r.PSObject.Properties | Where-Object {$_.Name -notmatch '^PS'} | ForEach-Object { $_.Name + " = " + $_.Value } | Out-File $out -Append -Encoding utf8
"=== RUN (HKLM) ===" | Out-File $out -Append -Encoding utf8
$r2 = Get-ItemProperty "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run" -ErrorAction SilentlyContinue
$r2.PSObject.Properties | Where-Object {$_.Name -notmatch '^PS'} | ForEach-Object { $_.Name + " = " + $_.Value } | Out-File $out -Append -Encoding utf8
"=== RUN (WOW6432) ===" | Out-File $out -Append -Encoding utf8
$r3 = Get-ItemProperty "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run" -ErrorAction SilentlyContinue
$r3.PSObject.Properties | Where-Object {$_.Name -notmatch '^PS'} | ForEach-Object { $_.Name + " = " + $_.Value } | Out-File $out -Append -Encoding utf8
"=== SERVICES (match) ===" | Out-File $out -Append -Encoding utf8
Get-CimInstance Win32_Service | Where-Object {$_.PathName -match 'Sogou|ClickToRun|IGCC|igcc|CrossDevice|cdp'} | ForEach-Object { $_.Name + " | " + $_.State + " | " + $_.StartMode + " | " + $_.PathName } | Out-File $out -Append -Encoding utf8
"=== SCHED TASKS (match) ===" | Out-File $out -Append -Encoding utf8
Get-ScheduledTask | Where-Object {$_.TaskName -match 'Sogou|IGCC|igcc|Cross'} | ForEach-Object { $_.TaskName + " | " + $_.State } | Out-File $out -Append -Encoding utf8
"=== PROBE DONE ===" | Out-File $out -Append -Encoding utf8
