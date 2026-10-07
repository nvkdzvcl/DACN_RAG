param(
    [string]$EnvFile = 'deploy/production.env'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) {
        throw 'Create deploy/production.env from deploy/production.env.example first.'
    }
    if (-not (Test-Path -LiteralPath 'frontend/dist/index.html' -PathType Leaf)) {
        throw 'Build the frontend first: npm --prefix frontend run build'
    }
    # Validate the chosen file, then let it override a reused development shell.
    & python -c "import sys; from dotenv import dotenv_values; from urllib.parse import urlsplit; c=dotenv_values(sys.argv[1]); u=urlsplit(c.get('CUSTOMER_PUBLIC_URL') or ''); ok=c.get('APP_ENV')=='production' and c.get('SERVE_FRONTEND')=='true' and u.scheme=='https' and bool(u.hostname) and not(u.username or u.password or u.query or u.fragment) and u.path in ('','/') and all(c.get(k) for k in ('DATABASE_URL','QDRANT_PATH','KNOWLEDGE_PATH')); sys.exit(0 if ok else 'Invalid production settings: require production, frontend, HTTPS origin and explicit data paths. Use the deployment template.')" $EnvFile
    if ($LASTEXITCODE -ne 0) { throw 'Production configuration validation failed.' }
    # One worker: SQLite, embedded Qdrant, in-memory limits and Telegram polling share state.
    & python -m dotenv -f $EnvFile run --override -- python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --proxy-headers --forwarded-allow-ips 127.0.0.1 --no-access-log --no-server-header --timeout-graceful-shutdown 240
    $serverExit = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $serverExit
