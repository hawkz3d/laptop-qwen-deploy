$out = "C:\kill_log.txt"
"=== RETRY KILL ===" | Out-File $out -Encoding utf8
taskkill /f /im SGTool.exe /t 2>&1 | Out-File $out -Append -Encoding utf8
taskkill /f /im SogouCloud.exe /t 2>&1 | Out-File $out -Append -Encoding utf8
Start-Sleep -Seconds 3
$alive = Get-Process -Name SGTool,SogouCloud -ErrorAction SilentlyContinue
if ($alive) { "STILL ALIVE: " + ($alive | ForEach-Object { $_.Name + ':' + $_.Id }) | Out-File $out -Append -Encoding utf8 }
else { "SGTool/SogouCloud all gone" | Out-File $out -Append -Encoding utf8 }
"=== AVAILABLE MEMORY ===" | Out-File $out -Append -Encoding utf8
$avail = (Get-Counter '\Memory\Available MBytes' -ErrorAction SilentlyContinue).CounterSamples[0].CookedValue
("Available: " + [math]::Round($avail/1024,2) + " GB") | Out-File $out -Append -Encoding utf8
$os = Get-CimInstance Win32_OperatingSystem
("Free(OS): " + [math]::Round($os.FreePhysicalMemory/1MB,1) + " GB") | Out-File $out -Append -Encoding utf8
"=== DONE ===" | Out-File $out -Append -Encoding utf8
