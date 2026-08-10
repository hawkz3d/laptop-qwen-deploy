$out = "C:\disable_log.txt"
"=== SOGOU PARENT 14564 ===" | Out-File $out -Encoding utf8
Get-CimInstance Win32_Process -Filter "ProcessId=14564" -ErrorAction SilentlyContinue | ForEach-Object { $_.Name + " | " + $_.CommandLine } | Out-File $out -Append -Encoding utf8
"=== DISABLE SERVICES ===" | Out-File $out -Append -Encoding utf8
try {
  Set-Service ClickToRunSvc -StartupType Disabled
  Stop-Service ClickToRunSvc -Force -ErrorAction SilentlyContinue
  $s = Get-Service ClickToRunSvc
  ("ClickToRunSvc -> " + $s.Status + " / " + $s.StartType) | Out-File $out -Append -Encoding utf8
} catch { ("ClickToRunSvc ERR: " + $_.Exception.Message) | Out-File $out -Append -Encoding utf8 }
try {
  Set-Service igccservice -StartupType Disabled
  Stop-Service igccservice -Force -ErrorAction SilentlyContinue
  $s2 = Get-Service igccservice
  ("igccservice -> " + $s2.Status + " / " + $s2.StartType) | Out-File $out -Append -Encoding utf8
} catch { ("igccservice ERR: " + $_.Exception.Message) | Out-File $out -Append -Encoding utf8 }
"=== KILL SOGOU CLOUD/TOOL ===" | Out-File $out -Append -Encoding utf8
Stop-Process -Name SogouCloud,SGTool -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1
$alive = Get-Process -Name SogouCloud,SGTool -ErrorAction SilentlyContinue
if ($alive) { "still alive: " + ($alive.Name -join ',') | Out-File $out -Append -Encoding utf8 }
else { "SogouCloud/SGTool stopped" | Out-File $out -Append -Encoding utf8 }
"=== MEMORY AFTER ===" | Out-File $out -Append -Encoding utf8
$os = Get-CimInstance Win32_OperatingSystem
("Free: " + [math]::Round($os.FreePhysicalMemory/1MB,1) + " GB") | Out-File $out -Append -Encoding utf8
"=== DONE ===" | Out-File $out -Append -Encoding utf8
