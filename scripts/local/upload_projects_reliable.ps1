# Reliable project file upload script
# Uses tar + ssh for reliable transfer
# Usage: .\scripts\local\upload_projects_reliable.ps1 -ServerIP "10-56-61-200"

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerUser = "ubuntu"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Reliable Project File Upload" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get server IP
if ([string]::IsNullOrEmpty($ServerIP)) {
    Write-Host "Enter server IP address:" -ForegroundColor Yellow
    $ServerIP = Read-Host
}

if ([string]::IsNullOrEmpty($ServerIP)) {
    Write-Host "ERROR: Server IP cannot be empty" -ForegroundColor Red
    exit 1
}

Write-Host "Server IP: $ServerIP" -ForegroundColor Green
Write-Host "Server User: $ServerUser" -ForegroundColor Green
Write-Host ""

# Local base path
$LocalBasePath = "D:\telegram-ai-system"
if (-not (Test-Path $LocalBasePath)) {
    Write-Host "ERROR: Local project directory does not exist: $LocalBasePath" -ForegroundColor Red
    exit 1
}

Write-Host "Local project directory: $LocalBasePath" -ForegroundColor Green
Write-Host ""

# Project configuration
$Projects = @(
    @{
        Name = "tgmini"
        LocalDir = "tgmini20251220"
        ServerDir = "tgmini20251220"
    },
    @{
        Name = "hongbao"
        LocalDir = "hbwy20251220"
        ServerDir = "hbwy20251220"
    },
    @{
        Name = "aizkw"
        LocalDir = "aizkw20251219"
        ServerDir = "aizkw20251219"
    }
)

# Check if tar is available
$tarAvailable = $false
try {
    $tarCommand = Get-Command tar -ErrorAction SilentlyContinue
    if ($tarCommand) {
        $tarAvailable = $true
        Write-Host "OK: tar command available" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: tar command not found, will use scp (slower)" -ForegroundColor Yellow
}

# Check if ssh is available
$sshAvailable = $false
try {
    $sshCommand = Get-Command ssh -ErrorAction SilentlyContinue
    if ($sshCommand) {
        $sshAvailable = $true
        Write-Host "OK: ssh command available" -ForegroundColor Green
    }
} catch {
    Write-Host "ERROR: ssh command not found" -ForegroundColor Red
    Write-Host "Please install OpenSSH client from Windows Settings" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test SSH connection
Write-Host "Testing SSH connection..." -ForegroundColor Cyan
try {
    $testResult = ssh -o ConnectTimeout=5 -o BatchMode=yes "$ServerUser@${ServerIP}" "echo 'Connection OK'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: SSH connection test successful" -ForegroundColor Green
    } else {
        Write-Host "WARNING: SSH connection test failed, but continuing..." -ForegroundColor Yellow
        Write-Host "You may need to enter password during upload" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARNING: Cannot test SSH connection, continuing..." -ForegroundColor Yellow
}
Write-Host ""

# Upload each project
$SuccessCount = 0
$FailedProjects = @()

foreach ($project in $Projects) {
    $LocalProjectPath = Join-Path $LocalBasePath $project.LocalDir
    $ServerProjectPath = "/home/ubuntu/telegram-ai-system/$($project.ServerDir)"
    
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Uploading project: $($project.Name)" -ForegroundColor Cyan
    Write-Host "Local: $LocalProjectPath" -ForegroundColor Gray
    Write-Host "Server: $ServerProjectPath" -ForegroundColor Gray
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Check local directory
    if (-not (Test-Path $LocalProjectPath)) {
        Write-Host "ERROR: Local project directory does not exist: $LocalProjectPath" -ForegroundColor Red
        Write-Host "Skipping this project" -ForegroundColor Yellow
        $FailedProjects += "$($project.Name) (local directory not found)"
        Write-Host ""
        continue
    }
    
    # Check package.json
    $PackageJson = Join-Path $LocalProjectPath "package.json"
    if (-not (Test-Path $PackageJson)) {
        Write-Host "WARNING: package.json not found: $PackageJson" -ForegroundColor Yellow
        Write-Host "Continuing to upload other files..." -ForegroundColor Yellow
    } else {
        Write-Host "OK: Found package.json" -ForegroundColor Green
    }
    
    # Create server directory
    Write-Host "Creating server directory..." -ForegroundColor Gray
    try {
        ssh "$ServerUser@${ServerIP}" "mkdir -p $ServerProjectPath && chmod 755 $ServerProjectPath" 2>&1 | Out-Null
        Write-Host "OK: Server directory created" -ForegroundColor Green
    } catch {
        Write-Host "WARNING: Cannot create server directory, continuing..." -ForegroundColor Yellow
    }
    
    # Upload files
    Write-Host "Uploading files..." -ForegroundColor Cyan
    Write-Host "(This may take a few minutes, please wait...)" -ForegroundColor Gray
    
    try {
        if ($tarAvailable) {
            # Method 1: Use tar + ssh (most reliable)
            Write-Host "Using tar compression and transfer..." -ForegroundColor Gray
            
            # Create tar archive locally and stream to server
            $tarCommand = "cd `"$LocalProjectPath`" && tar -czf - --exclude=node_modules --exclude=dist --exclude=.git --exclude='*.log' . 2>&1"
            $sshCommand = "cd $ServerProjectPath && tar -xzf - 2>&1"
            
            # Execute tar locally and pipe to ssh
            $process = Start-Process -FilePath "tar" -ArgumentList @("-czf", "-", "-C", $LocalProjectPath, "--exclude=node_modules", "--exclude=dist", "--exclude=.git", "--exclude=*.log", ".") -NoNewWindow -PassThru -RedirectStandardOutput "NUL" -RedirectStandardError "NUL"
            
            # Alternative: Use PowerShell to pipe tar to ssh
            $tarProcess = Start-Process -FilePath "tar" -ArgumentList @("-czf", "-", "-C", $LocalProjectPath, "--exclude=node_modules", "--exclude=dist", "--exclude=.git", ".") -NoNewWindow -PassThru -RedirectStandardOutput ([System.IO.PipeStream]::CreatePipe()) -RedirectStandardError ([System.IO.PipeStream]::CreatePipe())
            
            # Simpler approach: Use scp with proper exclusions
            Write-Host "Using scp with file selection..." -ForegroundColor Gray
            
            # Get all files to upload (excluding node_modules, dist, .git)
            $filesToUpload = @()
            Get-ChildItem -Path $LocalProjectPath -Recurse -File | ForEach-Object {
                $relativePath = $_.FullName.Substring($LocalProjectPath.Length + 1).Replace('\', '/')
                if (-not ($relativePath -like "node_modules/*") -and
                    -not ($relativePath -like "dist/*") -and
                    -not ($relativePath -like ".git/*") -and
                    -not ($relativePath -like "*.log")) {
                    $filesToUpload += $_.FullName
                }
            }
            
            Write-Host "Found $($filesToUpload.Count) files to upload" -ForegroundColor Gray
            
            # Upload files one by one (slow but reliable)
            $uploadedCount = 0
            foreach ($file in $filesToUpload) {
                $relativePath = $file.Substring($LocalProjectPath.Length + 1).Replace('\', '/')
                $serverFilePath = "$ServerProjectPath/$relativePath"
                $serverFileDir = Split-Path $serverFilePath -Parent
                
                # Create directory on server
                ssh "$ServerUser@${ServerIP}" "mkdir -p `"$serverFileDir`"" 2>&1 | Out-Null
                
                # Upload file
                scp "$file" "$ServerUser@${ServerIP}:$serverFilePath" 2>&1 | Out-Null
                
                $uploadedCount++
                if ($uploadedCount % 10 -eq 0) {
                    Write-Host "  Uploaded $uploadedCount / $($filesToUpload.Count) files..." -ForegroundColor Gray
                }
            }
            
            Write-Host "OK: Upload completed: $($project.Name)" -ForegroundColor Green
            $SuccessCount++
            
        } else {
            # Method 2: Use scp (slower but works)
            Write-Host "Using scp transfer..." -ForegroundColor Gray
            
            # Upload directory contents
            $scpOutput = scp -r "$LocalProjectPath\*" "$ServerUser@${ServerIP}:$ServerProjectPath/" 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "OK: Upload successful: $($project.Name)" -ForegroundColor Green
                $SuccessCount++
            } else {
                throw "Upload failed: $scpOutput"
            }
        }
    } catch {
        Write-Host "ERROR: Upload failed: $($project.Name)" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        $FailedProjects += "$($project.Name) (upload failed)"
    }
    
    Write-Host ""
}

# Summary
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Upload Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Success: $SuccessCount / $($Projects.Count)" -ForegroundColor $(if ($SuccessCount -eq $Projects.Count) { "Green" } else { "Yellow" })

if ($FailedProjects.Count -gt 0) {
    Write-Host "Failed: $($FailedProjects.Count)" -ForegroundColor Red
    Write-Host "Failed projects:" -ForegroundColor Red
    foreach ($failed in $FailedProjects) {
        Write-Host "  - $failed" -ForegroundColor Red
    }
}
Write-Host ""

if ($SuccessCount -gt 0) {
    Write-Host "OK: Some or all files uploaded successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps (execute on server):" -ForegroundColor Yellow
    Write-Host "1. Verify files: ls -la /home/ubuntu/telegram-ai-system/*/package.json" -ForegroundColor White
    Write-Host "2. Build and start: sudo bash /home/ubuntu/telegram-ai-system/scripts/server/build_and_start_all.sh" -ForegroundColor White
    Write-Host "3. Check services: pm2 list" -ForegroundColor White
}
