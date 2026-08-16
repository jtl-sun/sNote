param(
    [Parameter(Mandatory = $true)]
    [string]$Pythonw,
    [Parameter(Mandatory = $true)]
    [string]$WorkingDirectory,
    [Parameter(Mandatory = $true)]
    [string]$AppPath
)

$ErrorActionPreference = "SilentlyContinue"

# Start the GUI without attaching a console window.
$env:PYTHONPATH = $AppPath
Start-Process -FilePath $Pythonw -ArgumentList "-m", "snote" -WorkingDirectory $WorkingDirectory
Start-Sleep -Milliseconds 250

# Close only the terminal session that launched `sn`. If sn.cmd was started by
# PowerShell, cmd.exe is an intermediate child, so close its PowerShell parent.
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
