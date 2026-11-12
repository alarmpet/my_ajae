# my_ajae W46 하루 한 글 게시 — 윈도우 작업 스케줄러 등록(사용자가 직접 실행). 2026-11-13 ~ 11-21 매일 19:00.
# 지우려면: Unregister-ScheduledTask -TaskName my_ajae-daily-post -Confirm:$false
$a = New-ScheduledTaskAction -Execute "C:\Python313\python.exe" -Argument "D:\my_ajae\tools\run_schedule.py" -WorkingDirectory "D:\my_ajae"
$t = New-ScheduledTaskTrigger -Daily -At "2026-11-13T19:00:00"
$t.EndBoundary = "2026-11-21T23:59:00"
$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName "my_ajae-daily-post" -Action $a -Trigger $t -Settings $s -Description "my_ajae W46 daily post" | Out-Null
Get-ScheduledTask -TaskName "my_ajae-daily-post" | Get-ScheduledTaskInfo | Select-Object NextRunTime
