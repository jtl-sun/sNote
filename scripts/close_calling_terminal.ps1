$ErrorActionPreference = "SilentlyContinue"

$selfProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$PID"
$caller = Get-CimInstance Win32_Process -Filter "ProcessId=$($selfProcess.ParentProcessId)"
if ($null -eq $caller) { exit 0 }

$targetProcessId = $null
if ($caller.Name -ieq "cmd.exe") {
    $callerParent = Get-CimInstance Win32_Process -Filter "ProcessId=$($caller.ParentProcessId)"
    if ($null -ne $callerParent -and $callerParent.Name -in @("powershell.exe", "pwsh.exe")) {
        $targetProcessId = $callerParent.ProcessId
    } else {
        $targetProcessId = $caller.ProcessId
    }
} elseif ($caller.Name -in @("powershell.exe", "pwsh.exe")) {
    $targetProcessId = $caller.ProcessId
}

if ($null -ne $targetProcessId -and $targetProcessId -ne $PID) {
    Stop-Process -Id $targetProcessId -Force
}
