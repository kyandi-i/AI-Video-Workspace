param(
    [switch]$Dev,
    [switch]$NoBrowser,
    [int]$Port = 8765,
    [int]$FrontendPort = 5173
)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $launchArgs = @('run', '--locked', '--project', 'backend', 'python', 'scripts/start.py', '--port', $Port, '--frontend-port', $FrontendPort)
    if ($Dev) { $launchArgs += '--dev' }
    if ($NoBrowser) { $launchArgs += '--no-browser' }
    & uv @launchArgs
    if ($LASTEXITCODE -ne 0) { throw "Application exited with code $LASTEXITCODE" }
}
finally { Pop-Location }
