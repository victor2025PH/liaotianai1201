# Upload projects using tar (most reliable method)
# Usage: .\scripts\local\upload_with_tar.ps1 -ServerIP "10-56-61-200"

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "",
    
    [Parameter(Mandatory=$false)]
    [string]$ServerUser = "ubuntu"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Upload Projects Using Tar (Most Reliable)" -ForegroundColor Cyan
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

# Check tar command
$tarCommand = Get-Command tar -ErrorAction SilentlyContinue
if (-not $tarCommand) {
    Write-Host "ERROR: tar command not found" -ForegroundColor Red
    Write-Host "Please install tar or use WinSCP sync feature" -ForegroundColor Yellow
    exit 1
}

# Check ssh command
$sshCommand = Get-Command ssh -ErrorAction SilentlyContinue
if (-not $sshCommand) {
    Write-Host "ERROR: ssh command not found" -ForegroundColor Red
    Write-Host "Please install OpenSSH client from Windows Settings" -ForegroundColor Yellow
    exit 1
}

Write-Host "OK: tar and ssh commands available" -ForegroundColor Green
Write-Host ""

# Local base path
$LocalBasePath = "D:\telegram-ai-system"
if (-not (Test-Path $LocalBasePath)) {
    Write-Host "ERROR: Local project directory does not exist: $LocalBasePath" -ForegroundColor Red
    exit 1
}

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
    ssh "$ServerUser@${ServerIP}" "mkdir -p $ServerProjectPath && chmod 755 $ServerProjectPath" 2>&1 | Out-Null
    Write-Host "OK: Server directory created" -ForegroundColor Green
    
    # Upload using tar (streaming, most reliable)
    Write-Host "Uploading files using tar (this may take a few minutes)..." -ForegroundColor Cyan
    
    try {
        # Use tar to compress and stream to server
        # This method:
        # 1. Compresses all files (excluding node_modules, dist, .git)
        # 2. Streams directly to server via SSH
        # 3. Extracts on server
        # 4. Handles all subdirectories automatically
        
        $tarArgs = @(
            "-czf", "-",
            "-C", $LocalProjectPath,
            "--exclude=node_modules",
            "--exclude=dist",
            "--exclude=.git",
            "--exclude=*.log",
            "."
        )
        
        $sshArgs = "cd $ServerProjectPath && tar -xzf -"
        
        # Execute: tar -czf - | ssh ... "tar -xzf -"
        $tarProcess = Start-Process -FilePath "tar" -ArgumentList $tarArgs -NoNewWindow -PassThru -RedirectStandardOutput ([System.IO.Pipes.PipeStream]::CreatePipe()) -ErrorAction SilentlyContinue
        
        # Alternative: Use PowerShell to pipe
        Write-Host "Compressing and uploading..." -ForegroundColor Gray
        
        # Create a temporary script to handle the pipe
        $tempScript = [System.IO.Path]::GetTempFileName() + ".ps1"
        $scriptContent = @"
`$tarOutput = & tar -czf - -C "$LocalProjectPath" --exclude=node_modules --exclude=dist --exclude=.git --exclude='*.log' . 2>&1
`$tarOutput | ssh "$ServerUser@${ServerIP}" "cd $ServerProjectPath && tar -xzf -" 2>&1
"@
        $scriptContent | Out-File -FilePath $tempScript -Encoding UTF8
        
        # Execute the script
        $result = & powershell -ExecutionPolicy Bypass -File $tempScript 2>&1
        
        # Clean up
        Remove-Item $tempScript -ErrorAction SilentlyContinue
        
        # Simpler approach: Use tar to create archive, then scp it
        Write-Host "Creating tar archive..." -ForegroundColor Gray
        $tempTar = [System.IO.Path]::GetTempFileName() + ".tar.gz"
        
        # Create tar archive
        & tar -czf $tempTar -C $LocalProjectPath --exclude=node_modules --exclude=dist --exclude=.git --exclude='*.log' . 2>&1 | Out-Null
        
        if (-not (Test-Path $tempTar)) {
            throw "Failed to create tar archive"
        }
        
        $tarSize = (Get-Item $tempTar).Length / 1MB
        Write-Host "Archive size: $([math]::Round($tarSize, 2)) MB" -ForegroundColor Gray
        
        # Upload archive
        Write-Host "Uploading archive..." -ForegroundColor Gray
        $scpResult = scp $tempTar "$ServerUser@${ServerIP}:/tmp/$($project.Name).tar.gz" 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to upload archive: $scpResult"
        }
        
        # Extract on server
        Write-Host "Extracting on server..." -ForegroundColor Gray
        $extractResult = ssh "$ServerUser@${ServerIP}" "cd $ServerProjectPath && tar -xzf /tmp/$($project.Name).tar.gz && rm /tmp/$($project.Name).tar.gz" 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to extract archive: $extractResult"
        }
        
        # Clean up local archive
        Remove-Item $tempTar -ErrorAction SilentlyContinue
        
        Write-Host "OK: Upload completed: $($project.Name)" -ForegroundColor Green
        $SuccessCount++
        
    } catch {
        Write-Host "ERROR: Upload failed: $($project.Name)" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        $FailedProjects += "$($project.Name) (upload failed: $_)"
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
    foreach ($failed in $FailedProjects) {
        Write-Host "  - $failed" -ForegroundColor Red
    }
}
Write-Host ""

if ($SuccessCount -gt 0) {
    Write-Host "OK: Files uploaded successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps (execute on server):" -ForegroundColor Yellow
    Write-Host "1. Verify: ls -la /home/ubuntu/telegram-ai-system/*/package.json" -ForegroundColor White
    Write-Host "2. Build: sudo bash /home/ubuntu/telegram-ai-system/scripts/server/build_and_start_all.sh" -ForegroundColor White
}
