param([int]$Port = 8070,
    [string]$EnvFile = 'C:\Users\admin\Downloads\AI20K\Day06\K5-L3B-Day06-2A202603907-DataIngestionEngineering\starter\.env')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$AgentPython = Join-Path (Split-Path -Parent $EnvFile) '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $AgentPython)) { $AgentPython = 'python' }
& $AgentPython -m src.web.server --env-file $EnvFile --port $Port
