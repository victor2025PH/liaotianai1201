# Deployment Script
$ErrorActionPreference = "Continue"
$logFile = "e:\002-工作文件\重要程序\聊天AI群聊程序\deployment_log.txt"

# Clear log
"=== Deployment Started: $(Get-Date) ===" | Out-File $logFile

# Change to project directory
Set-Location "e:\002-工作文件\重要程序\聊天AI群聊程序"
"Working directory: $(Get-Location)" | Out-File $logFile -Append

# Git add
"=== Git Add ===" | Out-File $logFile -Append
$addResult = git add -A 2>&1
$addResult | Out-File $logFile -Append

# Git status
"=== Git Status ===" | Out-File $logFile -Append
$statusResult = git status 2>&1
$statusResult | Out-File $logFile -Append

# Git commit
"=== Git Commit ===" | Out-File $logFile -Append
$commitResult = git commit -m "feat: Add advanced chat features" 2>&1
$commitResult | Out-File $logFile -Append

# Git push
"=== Git Push ===" | Out-File $logFile -Append
$pushResult = git push origin master 2>&1
$pushResult | Out-File $logFile -Append

"=== Deployment Completed: $(Get-Date) ===" | Out-File $logFile -Append

Write-Host "Deployment complete. Check $logFile for details."
