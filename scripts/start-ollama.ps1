$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$portableOllama = Join-Path $projectRoot 'data/runtime/ollama/ollama.exe'
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_NUM_PARALLEL = '1'
if (Test-Path -LiteralPath $portableOllama) {
    $env:OLLAMA_MODELS = Join-Path $projectRoot 'data/runtime/models'
    & $portableOllama serve
} else {
    & (Get-Command ollama -ErrorAction Stop).Source serve
}
exit $LASTEXITCODE
