$p = Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 30 Name,Id,@{n='MB';e={[int]($_.WorkingSet64/1MB)}},Path
$p | Format-Table -AutoSize | Out-File -FilePath C:\procs.txt -Encoding utf8
"--- MEMORY ---" | Out-File -FilePath C:\procs.txt -Append -Encoding utf8
$os = Get-CimInstance Win32_OperatingSystem
("Total: " + [math]::Round($os.TotalVisibleMemorySize/1MB,1) + " GB Free: " + [math]::Round($os.FreePhysicalMemory/1MB,1) + " GB") | Out-File -FilePath C:\procs.txt -Append -Encoding utf8
