# Student Management System - Docker Manager (PowerShell)

param(
    [Parameter(Position = 0)]
    [string]$Command,

    [Parameter(Position = 1)]
    [string]$Argument
)

# ---- Logging helpers (approved verb: Write-) ----
function Write-MsgInfo { param([string]$msg); Write-Host "[INFO]    $msg" -ForegroundColor Cyan }
function Write-MsgSuccess { param([string]$msg); Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-MsgWarn { param([string]$msg); Write-Host "[WARNING] $msg" -ForegroundColor Yellow }
function Write-MsgErr { param([string]$msg); Write-Host "[ERROR]   $msg" -ForegroundColor Red }

# ---- Check Docker ----
function Test-DockerRunning {
    try {
        docker info 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { throw }
        Write-MsgSuccess "Docker is running"
        return $true
    }
    catch {
        Write-MsgErr "Docker is not running. Please start Docker Desktop and try again."
        return $false
    }
}

# ---- Development ----
function Start-DevEnvironment {
    Write-MsgInfo "Starting development environment..."
    docker-compose --env-file .env.docker up -d
    Write-MsgSuccess "Development environment started"
    Write-MsgInfo "Frontend  : http://localhost:5173"
    Write-MsgInfo "Backend   : http://localhost:8000"
    Write-MsgInfo "API Docs  : http://localhost:8000/docs"
    Write-MsgInfo "MySQL     : localhost:3307 (host port, container uses 3306)"
    Write-MsgInfo "phpMyAdmin: http://localhost:8181 (only with --profile tools)"
}

function Stop-DevEnvironment {
    Write-MsgInfo "Stopping development environment..."
    docker-compose down
    Write-MsgSuccess "Development environment stopped"
}

function Restart-DevEnvironment {
    Write-MsgInfo "Restarting development environment..."
    docker-compose restart
    Write-MsgSuccess "Development environment restarted"
}

function Show-DevLogs {
    param([string]$Service)
    if ($Service) {
        docker-compose logs -f $Service
    }
    else {
        docker-compose logs -f
    }
}

function Invoke-DevBuild {
    Write-MsgInfo "Building development images (no cache)..."
    docker-compose build --no-cache
    Write-MsgSuccess "Development images built"
}

# ---- Production ----
function Start-ProdEnvironment {
    Write-MsgInfo "Starting production environment..."
    docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
    Write-MsgSuccess "Production environment started"
    Write-MsgInfo "Application: http://localhost:80"
}

function Stop-ProdEnvironment {
    Write-MsgInfo "Stopping production environment..."
    docker-compose -f docker-compose.prod.yml down
    Write-MsgSuccess "Production environment stopped"
}

function Invoke-ProdBuild {
    Write-MsgInfo "Building production images (no cache)..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    Write-MsgSuccess "Production images built"
}

# ---- Database ----
function Backup-Database {
    Write-MsgInfo "Creating database backup..."
    $BackupFile = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
    docker exec student-management-mysql mysqldump -u root -p123456 student_management > $BackupFile
    Write-MsgSuccess "Database backup created: $BackupFile"
}

function Restore-Database {
    param([string]$BackupFile)
    if (-not $BackupFile) {
        Write-MsgErr "Please provide backup file path. Example: .\docker-manager.ps1 db:restore backup.sql"
        return
    }
    if (-not (Test-Path $BackupFile)) {
        Write-MsgErr "Backup file not found: $BackupFile"
        return
    }
    Write-MsgInfo "Restoring database from $BackupFile..."
    Get-Content $BackupFile | docker exec -i student-management-mysql mysql -u root -p123456 student_management
    Write-MsgSuccess "Database restored"
}

function Open-DbShell {
    Write-MsgInfo "Opening MySQL shell..."
    docker exec -it student-management-mysql mysql -u root -p123456 student_management
}

# ---- Health ----
function Test-ServiceHealth {
    Write-MsgInfo "Checking service health..."
    docker-compose ps
    Write-Host ""

    Write-MsgInfo "Backend health:"
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 5
        Write-MsgSuccess "Backend is healthy (HTTP $($r.StatusCode))"
    }
    catch {
        Write-MsgErr "Backend is not healthy or not running"
    }

    Write-Host ""
    Write-MsgInfo "Frontend health:"
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:5173/" -UseBasicParsing -TimeoutSec 5
        Write-MsgSuccess "Frontend is healthy (HTTP $($r.StatusCode))"
    }
    catch {
        Write-MsgErr "Frontend is not healthy or not running"
    }
}

# ---- Cleanup ----
function Remove-AllContainers {
    Write-MsgWarn "This will remove ALL containers, volumes, and images!"
    $confirm = Read-Host "Are you sure? Type 'yes' to confirm"
    if ($confirm -eq "yes") {
        Write-MsgInfo "Cleaning up..."
        docker-compose down -v
        docker system prune -af --volumes
        Write-MsgSuccess "Cleanup completed"
    }
    else {
        Write-MsgInfo "Cleanup cancelled"
    }
}

# ---- Usage ----
function Show-Usage {
    Write-Host ""
    Write-Host "Student Management System - Docker Manager" -ForegroundColor Cyan
    Write-Host "Usage: .\docker-manager.ps1 [COMMAND] [ARGUMENT]" -ForegroundColor White
    Write-Host ""
    Write-Host "Development Commands:" -ForegroundColor Yellow
    Write-Host "  dev:start       Start development environment"
    Write-Host "  dev:stop        Stop development environment"
    Write-Host "  dev:restart     Restart development environment"
    Write-Host "  dev:logs        Show logs (optional: pass service name as ARGUMENT)"
    Write-Host "  dev:build       Rebuild development images (no cache)"
    Write-Host ""
    Write-Host "Production Commands:" -ForegroundColor Yellow
    Write-Host "  prod:start      Start production environment"
    Write-Host "  prod:stop       Stop production environment"
    Write-Host "  prod:build      Build production images (no cache)"
    Write-Host ""
    Write-Host "Database Commands:" -ForegroundColor Yellow
    Write-Host "  db:backup       Create database backup"
    Write-Host "  db:restore      Restore database (ARGUMENT = backup file path)"
    Write-Host "  db:shell        Open MySQL interactive shell"
    Write-Host ""
    Write-Host "Utility Commands:" -ForegroundColor Yellow
    Write-Host "  health          Check service health"
    Write-Host "  cleanup         Remove ALL containers, volumes, and images"
    Write-Host "  help            Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\docker-manager.ps1 dev:start"
    Write-Host "  .\docker-manager.ps1 dev:logs backend"
    Write-Host "  .\docker-manager.ps1 db:backup"
    Write-Host "  .\docker-manager.ps1 db:restore backup_20260209.sql"
    Write-Host ""
}

# ============ MAIN ============
if (-not (Test-DockerRunning)) {
    exit 1
}

switch ($Command) {
    "dev:start" { Start-DevEnvironment }
    "dev:stop" { Stop-DevEnvironment }
    "dev:restart" { Restart-DevEnvironment }
    "dev:logs" { Show-DevLogs -Service $Argument }
    "dev:build" { Invoke-DevBuild }
    "prod:start" { Start-ProdEnvironment }
    "prod:stop" { Stop-ProdEnvironment }
    "prod:build" { Invoke-ProdBuild }
    "db:backup" { Backup-Database }
    "db:restore" { Restore-Database -BackupFile $Argument }
    "db:shell" { Open-DbShell }
    "health" { Test-ServiceHealth }
    "cleanup" { Remove-AllContainers }
    default { Show-Usage }
}
