# SSH Configuration Verification Script
# Encoding: UTF-8 with BOM

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub Actions SSH Configuration Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check GitHub Secrets
Write-Host "Step 1: Check GitHub Secrets Configuration" -ForegroundColor Yellow
Write-Host ""
Write-Host "Please manually check if the following GitHub Secrets are configured:" -ForegroundColor White
Write-Host "  1. SERVER_HOST - Server IP address" -ForegroundColor Gray
Write-Host "  2. SERVER_USER - SSH username (usually ubuntu)" -ForegroundColor Gray
Write-Host "  3. SERVER_SSH_KEY - SSH private key (full content)" -ForegroundColor Gray
Write-Host ""
Write-Host "Open this link to check:" -ForegroundColor White
Write-Host "  https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions" -ForegroundColor Cyan
Write-Host ""
$continue = Read-Host "Have you checked GitHub Secrets? (Y/n)"
if ($continue -eq "n" -or $continue -eq "N") {
    Write-Host "Please configure GitHub Secrets first, then run this script again" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] GitHub Secrets check completed" -ForegroundColor Green
Write-Host ""

# Step 2: Check Server SSH Key Configuration
Write-Host "Step 2: Check Server SSH Key Configuration" -ForegroundColor Yellow
Write-Host ""
Write-Host "Please run the following commands on the server:" -ForegroundColor White
Write-Host ""
Write-Host "# Check if SSH Key exists" -ForegroundColor Gray
Write-Host "ls -la ~/.ssh/" -ForegroundColor Cyan
Write-Host ""
Write-Host "# Check authorized_keys" -ForegroundColor Gray
Write-Host "ls -la ~/.ssh/authorized_keys" -ForegroundColor Cyan
Write-Host "cat ~/.ssh/authorized_keys" -ForegroundColor Cyan
Write-Host ""
Write-Host "# Fix permissions (.ssh should be 700, authorized_keys should be 600)" -ForegroundColor Gray
Write-Host "chmod 700 ~/.ssh" -ForegroundColor Cyan
Write-Host "chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Cyan
Write-Host ""
$continue = Read-Host "Have you checked SSH Key configuration on server? (Y/n)"
if ($continue -eq "n" -or $continue -eq "N") {
    Write-Host "Please configure SSH Key on server first, then run this script again" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Server SSH Key configuration check completed" -ForegroundColor Green
Write-Host ""

# Step 3: Test SSH Connection
Write-Host "Step 3: Test SSH Connection" -ForegroundColor Yellow
Write-Host ""
$serverHost = Read-Host "Enter server IP address (e.g., 165.154.235.170)"
$serverUser = Read-Host "Enter SSH username (e.g., ubuntu)"

Write-Host ""
Write-Host "Testing SSH connection..." -ForegroundColor White
Write-Host "Command: ssh $serverUser@$serverHost 'echo SSH_TEST_SUCCESS'" -ForegroundColor Gray
Write-Host ""

try {
    $testCmd = "echo 'SSH_TEST_SUCCESS'; whoami; pwd"
    $result = ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "${serverUser}@${serverHost}" $testCmd 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] SSH connection successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Server response:" -ForegroundColor White
        $result | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    } else {
        Write-Host "[ERROR] SSH connection failed" -ForegroundColor Red
        Write-Host ""
        Write-Host "Error message:" -ForegroundColor Red
        $result | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        Write-Host ""
        Write-Host "Possible causes:" -ForegroundColor Yellow
        Write-Host "  1. SSH Key not configured correctly" -ForegroundColor Gray
        Write-Host "  2. Server firewall blocking connection" -ForegroundColor Gray
        Write-Host "  3. Incorrect server IP or username" -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host "[ERROR] SSH connection test error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Push code to GitHub" -ForegroundColor White
Write-Host "  2. Check GitHub Actions run results" -ForegroundColor White
Write-Host "  3. If still failing, check workflow logs for specific errors" -ForegroundColor White
Write-Host ""
