$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$portableOllama = Join-Path $projectRoot 'data/runtime/ollama/ollama.exe'
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_MAX_LOADED_MODELS = '2'
$env:OLLAMA_NUM_PARALLEL = '1'
try {
    $null = Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 2
    Write-Host 'Ollama is already running at 127.0.0.1:11434; reusing the existing service.'
    exit 0
} catch {}
$installedOllama = Get-Command ollama -ErrorAction SilentlyContinue
if ($installedOllama) {
    & $installedOllama.Source serve
} elseif (Test-Path -LiteralPath $portableOllama) {
    $env:OLLAMA_MODELS = Join-Path $projectRoot 'data/runtime/models'
    & $portableOllama serve
} else {
    throw 'Ollama was not found. Install Ollama or restore data/runtime/ollama/ollama.exe.'
}
exit $LASTEXITCODE
