param(
    [string]$EnvFile = '.env',
    [Parameter(ValueFromRemainingArguments=$true)] [string[]]$CliArgs
)
$ErrorActionPreference = 'Stop'
$taskPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    $taskPython = 'python'
}
Push-Location $PSScriptRoot
try {
    & $taskPython -u -m src.day7.cli --env-file $EnvFile @CliArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally { Pop-Location }
