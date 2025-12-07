# ============================================================
# Sync Scripts and Check Server Status (Local Environment - Windows)
# ============================================================
# 
# Running Environment: Local Windows Environment
# Function: Sync scripts to server via Git, then execute status check
# 
# One-click execution: .\scripts\local\sync-and-check-server.ps1
# ============================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerHost = $env:SERVER_HOST,
    
    [Parameter(Mandatory=$false)]
    [string]$ServerUser = $env:SERVER_USER,
    
    [Parameter(Mandatory=$false)]
    [string]$SshKeyPath = $env:SSH_KEY_PATH,
    
    [Parameter(Mandatory=$false)]
    [string]$ServerPassword = $env:SERVER_PASSWORD
)

$ErrorActionPreference = "Continue"

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🔄 Sync Scripts and Check Server Status" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# ============================================================
# Step 1: Commit and push scripts to Git
# ============================================================
Write-Host "[1/4] Committing and pushing scripts to Git..." -ForegroundColor Yellow

try {
    # Check if there are changes
    $gitStatus = git status --porcelain 2>&1
    if ($gitStatus) {
        Write-Host "  Found changes, committing..." -ForegroundColor Cyan
        
        # Add server scripts
        git add scripts/server/check-server-status.sh 2>&1 | Out-Null
        git add .github/workflows/deploy.yml 2>&1 | Out-Null
        
        # Commit
        $commitMessage = "Add server status check script"
        git commit -m $commitMessage 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Committed changes" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ No changes to commit or commit failed" -ForegroundColor Yellow
        }
        
        # Push to remote
        Write-Host "  Pushing to origin/main..." -ForegroundColor Cyan
        git push origin main 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Pushed to GitHub" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ Push failed or already up to date" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✓ No changes to commit" -ForegroundColor Green
    }
} catch {
    Write-Host "  ✗ Git operation failed: $_" -ForegroundColor Red
    Write-Host "  Continuing with SSH connection..." -ForegroundColor Yellow
}

Write-Host ""

# ============================================================
# Step 2: Connect to server and pull latest code
# ============================================================
Write-Host "[2/4] Connecting to server and pulling latest code..." -ForegroundColor Yellow

if (-not $ServerHost) {
    Write-Host "  ⚠ SERVER_HOST not set. Please provide server host:" -ForegroundColor Yellow
    $ServerHost = Read-Host "  Enter server host (e.g., 165.154.233.55)"
}

if (-not $ServerUser) {
    $ServerUser = "ubuntu"
    Write-Host "  Using default user: $ServerUser" -ForegroundColor Cyan
}

$projectDir = "/home/ubuntu/telegram-ai-system"

# Build SSH command
$sshCommand = "cd $projectDir && git pull origin main 2>&1"

if ($SshKeyPath -and (Test-Path $SshKeyPath)) {
    Write-Host "  Using SSH key: $SshKeyPath" -ForegroundColor Cyan
    $sshArgs = "-i", $SshKeyPath, "${ServerUser}@${ServerHost}", $sshCommand
} elseif ($ServerPassword) {
    Write-Host "  Using password authentication" -ForegroundColor Cyan
    # Use sshpass if available, otherwise prompt
    if (Get-Command sshpass -ErrorAction SilentlyContinue) {
        $sshArgs = "sshpass", "-p", $ServerPassword, "ssh", "-o", "StrictHostKeyChecking=no", "${ServerUser}@${ServerHost}", $sshCommand
    } else {
        Write-Host "  ⚠ sshpass not found. Will prompt for password." -ForegroundColor Yellow
        $sshArgs = "ssh", "-o", "StrictHostKeyChecking=no", "${ServerUser}@${ServerHost}", $sshCommand
    }
} else {
    Write-Host "  Using default SSH authentication" -ForegroundColor Cyan
    $sshArgs = "ssh", "-o", "StrictHostKeyChecking=no", "${ServerUser}@${ServerHost}", $sshCommand
}

try {
    Write-Host "  Executing: git pull origin main" -ForegroundColor Cyan
    $pullOutput = & $sshArgs[0] $sshArgs[1..($sshArgs.Length-1)] 2>&1
    
    if ($LASTEXITCODE -eq 0 -or $pullOutput -match "Already up to date" -or $pullOutput -match "Updating") {
        Write-Host "  ✓ Code synchronized" -ForegroundColor Green
        if ($pullOutput) {
            Write-Host "  $pullOutput" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⚠ Git pull may have issues: $pullOutput" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ SSH connection failed: $_" -ForegroundColor Red
    Write-Host "  Please check:" -ForegroundColor Yellow
    Write-Host "    1. Server host is correct: $ServerHost" -ForegroundColor White
    Write-Host "    2. SSH key or password is correct" -ForegroundColor White
    Write-Host "    3. Network connectivity" -ForegroundColor White
    exit 1
}

Write-Host ""

# ============================================================
# Step 3: Execute status check script on server
# ============================================================
Write-Host "[3/4] Executing status check on server..." -ForegroundColor Yellow

$checkScript = "bash $projectDir/scripts/server/check-server-status.sh"

if ($SshKeyPath -and (Test-Path $SshKeyPath)) {
    $checkArgs = "-i", $SshKeyPath, "${ServerUser}@${ServerHost}", $checkScript
} elseif ($ServerPassword) {
    if (Get-Command sshpass -ErrorAction SilentlyContinue) {
        $checkArgs = "sshpass", "-p", $ServerPassword, "ssh", "-o", "StrictHostKeyChecking=no", "${ServerUser}@${ServerHost}", $checkScript
    } else {
        $checkArgs = "ssh", "-o", "StrictHostKeyChecking=no", "${ServerUser}@${ServerHost}", $checkScript
    }
} else {
    $checkArgs = "ssh", "-o", "StrictHostKeyChecking=no", "${ServerUser}@${ServerHost}", $checkScript
}

try {
    Write-Host "  Running status check..." -ForegroundColor Cyan
    Write-Host ""
    & $checkArgs[0] $checkArgs[1..($checkArgs.Length-1)] 2>&1
    Write-Host ""
} catch {
    Write-Host "  ✗ Failed to execute check script: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================
# Step 4: Ask if user wants to run auto-fix
# ============================================================
Write-Host "[4/4] Status check completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review the status check results above" -ForegroundColor White
Write-Host "  2. If issues found, you can:" -ForegroundColor White
Write-Host "     - Run diagnosis: bash scripts/server/diagnose-service.sh" -ForegroundColor Cyan
Write-Host "     - Run auto-fix: bash scripts/server/fix-service.sh" -ForegroundColor Cyan
Write-Host "     - View logs: bash scripts/server/view-service-logs.sh" -ForegroundColor Cyan
Write-Host ""

$runFix = Read-Host "Do you want to run auto-fix script? (y/N)"
if ($runFix -eq "y" -or $runFix -eq "Y") {
    Write-Host "`nRunning auto-fix script..." -ForegroundColor Yellow
    
    $fixScript = "bash $projectDir/scripts/server/fix-service.sh"
    
    if ($SshKeyPath -and (Test-Path $SshKeyPath)) {
        $fixArgs = "-i", $SshKeyPath, "${ServerUser}@${ServerHost}", $fixScript
    } elseif ($ServerPassword) {
        if (Get-Command sshpass -ErrorAction SilentlyContinue) {
            $fixArgs = "sshpass", "-p", $ServerPassword, "ssh", "-o", "StrictHostKeyChecking=no", "${ServerUser}@${ServerHost}", $fixScript
        } else {
            $fixArgs = "ssh", "-o", "StrictHostKeyChecking=no", "${ServerUser}@${ServerHost}", $fixScript
        }
    } else {
        $fixArgs = "ssh", "-o", "StrictHostKeyChecking=no", "${ServerUser}@${ServerHost}", $fixScript
    }
    
    try {
        & $fixArgs[0] $fixArgs[1..($fixArgs.Length-1)] 2>&1
        Write-Host ""
        Write-Host "✓ Auto-fix completed!" -ForegroundColor Green
    } catch {
        Write-Host "✗ Auto-fix failed: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Process completed!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

