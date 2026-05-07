#Requires -Version 5.1
<#
.SYNOPSIS
    Start the DataExtractor backend (and frontend when available).

.DESCRIPTION
    Checks for a .env file, installs dependencies if needed,
    then launches backend and frontend in separate console windows.

.PARAMETER BackendPort
    Port for the FastAPI backend. Default: 8000

.PARAMETER FrontendDir
    Path to the frontend directory. If the directory does not exist
    the frontend step is skipped. Default: ./frontend

.EXAMPLE
    .\start.ps1
    .\start.ps1 -BackendPort 9000 -FrontendDir ../my-frontend
#>

param(
    [int]    $BackendPort  = 8000,
    [string] $FrontendDir  = "frontend"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Helpers ──────────────────────────────────────────────────────────────────

function Write-Step([string]$msg) {
    Write-Host "`n>>> $msg" -ForegroundColor Cyan
}

function Write-Ok([string]$msg) {
    Write-Host "    [OK] $msg" -ForegroundColor Green
}

function Write-Warn([string]$msg) {
    Write-Host "    [!]  $msg" -ForegroundColor Yellow
}

function Write-Fail([string]$msg) {
    Write-Host "    [X]  $msg" -ForegroundColor Red
}

# ── .env check ───────────────────────────────────────────────────────────────

Write-Step "Checking configuration"

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Warn ".env created from .env.example – please fill in your API key before continuing."
        Write-Host "    Edit .env and re-run this script." -ForegroundColor Yellow
        exit 1
    } else {
        Write-Fail ".env file not found. Create one with at least OPENAI_API_KEY=sk-..."
        exit 1
    }
}

# Check that at least one API key looks set
$envContent = Get-Content ".env" -Raw
if ($envContent -notmatch "(OPENAI_API_KEY|ANTHROPIC_API_KEY)=sk-") {
    Write-Warn ".env found but no API key detected. Make sure OPENAI_API_KEY or ANTHROPIC_API_KEY is set."
} else {
    Write-Ok ".env looks good"
}

# ── Python / dependencies ─────────────────────────────────────────────────────

Write-Step "Checking Python environment"

try {
    $pyVersion = python --version 2>&1
    Write-Ok "Python: $pyVersion"
} catch {
    Write-Fail "Python not found. Please install Python 3.11+."
    exit 1
}

# Install/upgrade dependencies quietly
Write-Step "Installing backend dependencies"
python -m pip install -e "." -q
if ($LASTEXITCODE -ne 0) {
    Write-Fail "pip install failed. Check your internet connection or pyproject.toml."
    exit 1
}
Write-Ok "Dependencies up to date"

# ── Backend ───────────────────────────────────────────────────────────────────

Write-Step "Starting backend on http://localhost:$BackendPort"

$backendCmd = "python -m uvicorn main:app --host 0.0.0.0 --port $BackendPort --reload"

Start-Process powershell -ArgumentList `
    "-NoExit", "-Command", `
    "Write-Host 'DataExtractor Backend' -ForegroundColor Cyan; $backendCmd" `
    -WindowStyle Normal

Write-Ok "Backend window opened"
Write-Host "    Swagger UI : http://localhost:$BackendPort/docs" -ForegroundColor White
Write-Host "    Health     : http://localhost:$BackendPort/api/v1/health" -ForegroundColor White

# ── Frontend ──────────────────────────────────────────────────────────────────

Write-Step "Checking frontend"

if (-not (Test-Path $FrontendDir)) {
    Write-Warn "Frontend directory '$FrontendDir' not found – skipping."
    Write-Host "    When the frontend is ready, place it in '$FrontendDir' and re-run." -ForegroundColor DarkGray
} else {
    Write-Step "Starting frontend from '$FrontendDir'"

    # Detect package manager
    $frontendCmd = if (Test-Path "$FrontendDir/package.json") {
        $pm = if (Test-Path "$FrontendDir/pnpm-lock.yaml") { "pnpm" }
               elseif (Test-Path "$FrontendDir/yarn.lock")  { "yarn" }
               else                                          { "npm"  }
        "cd '$((Resolve-Path $FrontendDir).Path)'; $pm run dev"
    } else {
        Write-Warn "No package.json found in '$FrontendDir'. Skipping frontend."
        $null
    }

    if ($frontendCmd) {
        Start-Process powershell -ArgumentList `
            "-NoExit", "-Command", `
            "Write-Host 'DataExtractor Frontend' -ForegroundColor Magenta; $frontendCmd" `
            -WindowStyle Normal
        Write-Ok "Frontend window opened"
    }
}

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host "`n DataExtractor is starting up." -ForegroundColor Green
Write-Host " Press Ctrl+C in the backend window to stop.`n" -ForegroundColor DarkGray
