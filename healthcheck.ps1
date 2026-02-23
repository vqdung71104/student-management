# Health Check Script for Docker Services (PowerShell)

param(
    [switch]$Wait
)

# Configuration
$BackendUrl = if ($env:BACKEND_URL) { $env:BACKEND_URL }    else { "http://localhost:8000" }
$FrontendUrl = if ($env:FRONTEND_URL) { $env:FRONTEND_URL }   else { "http://localhost:5173" }
$MySQLContainer = if ($env:MYSQL_CONTAINER) { $env:MYSQL_CONTAINER } else { "student-management-mysql" }
$MaxRetries = 30
$RetryInterval = 2

function Write-StatusOk {
    param([string]$Service, [string]$Message)
    Write-Host "[OK]   " -ForegroundColor Green -NoNewline
    Write-Host "${Service}: ${Message}"
}

function Write-StatusWarn {
    param([string]$Service, [string]$Message)
    Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
    Write-Host "${Service}: ${Message}"
}

function Write-StatusErr {
    param([string]$Service, [string]$Message)
    Write-Host "[FAIL] " -ForegroundColor Red -NoNewline
    Write-Host "${Service}: ${Message}"
}

function Test-MySQL {
    Write-Host "Checking MySQL..." -ForegroundColor Blue
    try {
        docker exec $MySQLContainer mysqladmin ping -h localhost -u root -p123456 --silent 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-StatusOk "MySQL" "Database is responding"
            return $true
        }
        else {
            Write-StatusErr "MySQL" "Database is not responding (exit code: $LASTEXITCODE)"
            return $false
        }
    }
    catch {
        Write-StatusErr "MySQL" "Database is not responding"
        return $false
    }
}

function Test-Backend {
    Write-Host "Checking Backend API..." -ForegroundColor Blue
    try {
        $response = Invoke-WebRequest -Uri "$BackendUrl/" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-StatusOk "Backend" "API is responding (HTTP $($response.StatusCode))"
            return $true
        }
        else {
            Write-StatusErr "Backend" "Unexpected status code: $($response.StatusCode)"
            return $false
        }
    }
    catch {
        Write-StatusErr "Backend" "API is not responding"
        return $false
    }
}

function Test-Frontend {
    Write-Host "Checking Frontend..." -ForegroundColor Blue
    try {
        $response = Invoke-WebRequest -Uri "$FrontendUrl/" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-StatusOk "Frontend" "Frontend is responding (HTTP $($response.StatusCode))"
            return $true
        }
        else {
            Write-StatusErr "Frontend" "Unexpected status code: $($response.StatusCode)"
            return $false
        }
    }
    catch {
        Write-StatusErr "Frontend" "Frontend is not responding"
        return $false
    }
}

function Test-Containers {
    Write-Host "Checking Docker Containers..." -ForegroundColor Blue
    try {
        $runningList = docker-compose ps --services --filter "status=running" 2>$null
        $totalList = docker-compose ps --services 2>$null
        $running = ($runningList | Where-Object { $_ -ne "" }).Count
        $total = ($totalList   | Where-Object { $_ -ne "" }).Count

        if ($running -gt 0 -and $running -eq $total) {
            Write-StatusOk "Containers" "All containers are running ($running/$total)"
            return $true
        }
        else {
            Write-StatusWarn "Containers" "Some containers are not running ($running/$total)"
            return $false
        }
    }
    catch {
        Write-StatusErr "Containers" "Failed to check containers"
        return $false
    }
}

function Wait-ForServices {
    Write-Host "Waiting for services to be ready..." -ForegroundColor Blue
    $retries = 0
    while ($retries -lt $MaxRetries) {
        $mysqlOk = Test-MySQL
        $backendOk = Test-Backend
        $frontOk = Test-Frontend
        if ($mysqlOk -and $backendOk -and $frontOk) {
            Write-Host "[OK] All services are ready!" -ForegroundColor Green
            return $true
        }
        $retries++
        Write-Host "Retry $retries/$MaxRetries... (waiting ${RetryInterval}s)" -ForegroundColor Yellow
        Start-Sleep -Seconds $RetryInterval
    }
    Write-Host "[FAIL] Services failed to start within timeout" -ForegroundColor Red
    return $false
}

# ---- Main ----
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Student Management System - Health Check"  -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if ($Wait) {
    $result = Wait-ForServices
    if (-not $result) { exit 1 }
}
else {
    Test-Containers
    Write-Host ""
    $mysqlOk = Test-MySQL
    Write-Host ""
    $backendOk = Test-Backend
    Write-Host ""
    $frontendOk = Test-Frontend
    Write-Host ""

    if ($mysqlOk -and $backendOk -and $frontendOk) {
        Write-Host "[OK] All services are healthy" -ForegroundColor Green
        exit 0
    }
    else {
        Write-Host "[FAIL] Some services are unhealthy" -ForegroundColor Red
        exit 1
    }
}
