# ============================================================
# Check Server Status Remotely (Local Environment - Windows)
# ============================================================
# 
# Running Environment: Local Windows Environment
# Function: Connect to server and execute status check script
# 
# One-click execution: .\scripts\local\check-server-status-remote.ps1
# ============================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "165.154.255.48",
    
    [Parameter(Mandatory=$false)]
    [string]$Username = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "8iDcGrYb52Fxpzee"
)

$ErrorActionPreference = "Continue"

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🔍 Check Server Status Remotely" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Server: $ServerIP" -ForegroundColor Cyan
Write-Host "User: $Username`n" -ForegroundColor Cyan

# Check Posh-SSH module
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Write-Host "Installing Posh-SSH module..." -ForegroundColor Yellow
    Install-Module -Name Posh-SSH -Force -Scope CurrentUser -SkipPublisherCheck
}

Import-Module Posh-SSH -ErrorAction Stop

# Connect to server
Write-Host "[1/3] Connecting to server..." -ForegroundColor Yellow
try {
    $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
    
    $session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey -ErrorAction Stop
    if ($session) {
        Write-Host "✓ Connected to server" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to connect" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Connection error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Pull latest code
Write-Host "[2/3] Pulling latest code from GitHub..." -ForegroundColor Yellow
$pullCommand = "cd /home/ubuntu/telegram-ai-system && git pull origin main 2>&1"
$pullResult = Invoke-SSHCommand -SessionId $session.SessionId -Command $pullCommand

if ($pullResult.ExitStatus -eq 0 -or $pullResult.Output -match "Already up to date" -or $pullResult.Output -match "Updating") {
    Write-Host "✓ Code synchronized" -ForegroundColor Green
    if ($pullResult.Output) {
        Write-Host $pullResult.Output -ForegroundColor Gray
    }
} else {
    Write-Host "⚠ Git pull may have issues" -ForegroundColor Yellow
    if ($pullResult.Error) {
        Write-Host $pullResult.Error -ForegroundColor Red
    }
}

Write-Host ""

# Execute status check
Write-Host "[3/3] Executing status check on server..." -ForegroundColor Yellow
Write-Host ""

$checkCommand = "cd /home/ubuntu/telegram-ai-system && bash scripts/server/check-server-status.sh"
$checkResult = Invoke-SSHCommand -SessionId $session.SessionId -Command $checkCommand

# Display output
if ($checkResult.Output) {
    Write-Host $checkResult.Output
}

if ($checkResult.Error) {
    Write-Host $checkResult.Error -ForegroundColor Red
}

Write-Host ""

# Check if there are issues
if ($checkResult.Output -match "Found \d+ issue") {
    Write-Host "⚠ Issues detected. Would you like to run auto-fix? (y/N): " -ForegroundColor Yellow -NoNewline
    $runFix = Read-Host
    
    if ($runFix -eq "y" -or $runFix -eq "Y") {
        Write-Host "`nRunning auto-fix script..." -ForegroundColor Yellow
        
        $fixCommand = "cd /home/ubuntu/telegram-ai-system && bash scripts/server/fix-service.sh"
        $fixResult = Invoke-SSHCommand -SessionId $session.SessionId -Command $fixCommand
        
        Write-Host ""
        if ($fixResult.Output) {
            Write-Host $fixResult.Output
        }
        if ($fixResult.Error) {
            Write-Host $fixResult.Error -ForegroundColor Red
        }
        
        Write-Host ""
        Write-Host "✓ Auto-fix completed!" -ForegroundColor Green
    }
}

# Close session
Remove-SSHSession -SessionId $session.SessionId | Out-Null

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Status check completed!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

