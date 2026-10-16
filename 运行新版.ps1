$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) { $bootstrapPython = $pythonCommand.Source }
    else {
        $bootstrapPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
        if (-not (Test-Path -LiteralPath $bootstrapPython)) { throw '请安装 Python 3.10 或以上版本。' }
    }
    & $bootstrapPython -m venv (Join-Path $projectRoot '.venv')
    & $venvPython -m pip install -r (Join-Path $projectRoot 'backend\requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Python 依赖安装失败。' }
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend\dist\index.html'))) { throw '前端构建文件不存在，请按 README 执行前端构建。' }
$baseUrl = 'http://127.0.0.1:8086'
try {
    $existing = Invoke-RestMethod -Uri "$baseUrl/api/graph/all" -TimeoutSec 2
    if ($existing.meta.version -ne '2.0.0') { throw '8086 端口已被其他服务占用。' }
    Start-Process $baseUrl
    exit 0
} catch {
    if (Get-NetTCPConnection -LocalPort 8086 -State Listen -ErrorAction SilentlyContinue) { throw '8086 端口已占用，未启动第二个进程。' }
}
$logs = Join-Path $projectRoot 'logs'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$server = Start-Process -FilePath $venvPython -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8086') -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'server.log') -RedirectStandardError (Join-Path $logs 'server-error.log') -PassThru
$server.Id | Set-Content -LiteralPath (Join-Path $logs 'server.pid')
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 400
    try { $health = Invoke-RestMethod -Uri "$baseUrl/api/health" -TimeoutSec 1; if ($health.status -eq 'ok') { Start-Process $baseUrl; exit 0 } } catch {}
}
throw '服务启动超时，请查看 logs\server-error.log。'
