# Check local project directory structure
# Usage: Run this script in PowerShell

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Checking Local Project Directory Structure" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$BasePath = "D:\telegram-ai-system"

if (-not (Test-Path $BasePath)) {
    Write-Host "ERROR: Project root directory does not exist: $BasePath" -ForegroundColor Red
    exit 1
}

Write-Host "Project root directory: $BasePath" -ForegroundColor Green
Write-Host ""

# Check three project directories
$Projects = @(
    @{
        Name = "tgmini"
        Dir = "tgmini20251220"
    },
    @{
        Name = "hongbao"
        Dir = "hbwy20251220"
    },
    @{
        Name = "aizkw"
        Dir = "aizkw20251219"
    }
)

$AllValid = $true

foreach ($project in $Projects) {
    $ProjectPath = Join-Path $BasePath $project.Dir
    
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Checking project: $($project.Name)" -ForegroundColor Cyan
    Write-Host "Directory: $ProjectPath" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not (Test-Path $ProjectPath)) {
        Write-Host "ERROR: Directory does not exist" -ForegroundColor Red
        $AllValid = $false
        Write-Host ""
        continue
    }
    
    Write-Host "OK: Directory exists" -ForegroundColor Green
    Write-Host ""
    
    # Check package.json
    $PackageJson = Join-Path $ProjectPath "package.json"
    if (Test-Path $PackageJson) {
        Write-Host "OK: package.json exists" -ForegroundColor Green
        try {
            $packageContent = Get-Content $PackageJson -Raw -Encoding UTF8 | ConvertFrom-Json
            Write-Host "   Project name: $($packageContent.name)" -ForegroundColor Gray
            Write-Host "   Version: $($packageContent.version)" -ForegroundColor Gray
        } catch {
            Write-Host "   WARNING: Could not parse package.json" -ForegroundColor Yellow
        }
    } else {
        Write-Host "ERROR: package.json does not exist" -ForegroundColor Red
        $AllValid = $false
    }
    Write-Host ""
    
    # Check key files
    $KeyFiles = @("vite.config.ts", "vite.config.js", "tsconfig.json", "index.html", "App.tsx")
    Write-Host "Checking key files:" -ForegroundColor Yellow
    foreach ($file in $KeyFiles) {
        $FilePath = Join-Path $ProjectPath $file
        if (Test-Path $FilePath) {
            Write-Host "   OK: $file" -ForegroundColor Green
        } else {
            Write-Host "   WARNING: $file does not exist" -ForegroundColor Yellow
        }
    }
    Write-Host ""
    
    # Check components directory
    $ComponentsPath = Join-Path $ProjectPath "components"
    if (Test-Path $ComponentsPath) {
        Write-Host "OK: components directory exists" -ForegroundColor Green
        $componentFiles = Get-ChildItem -Path $ComponentsPath -Filter "*.tsx" -File -ErrorAction SilentlyContinue
        Write-Host "   TSX file count: $($componentFiles.Count)" -ForegroundColor Gray
    } else {
        Write-Host "WARNING: components directory does not exist" -ForegroundColor Yellow
    }
    Write-Host ""
    
    # Check for unexpected nested directory structure
    $ExcludedDirs = @("components", "contexts", "src", "hooks", "node_modules", "dist", ".git")
    $SubDirs = Get-ChildItem -Path $ProjectPath -Directory -ErrorAction SilentlyContinue | Where-Object { 
        $_.Name -notin $ExcludedDirs
    }
    if ($SubDirs -and $SubDirs.Count -gt 0) {
        Write-Host "WARNING: Found unexpected subdirectories (structure may be incorrect):" -ForegroundColor Yellow
        foreach ($subDir in $SubDirs) {
            Write-Host "   - $($subDir.Name)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "OK: Directory structure is normal (no unexpected nesting)" -ForegroundColor Green
    }
    Write-Host ""
    
    # List directory contents (first 15 items)
    Write-Host "Directory contents (first 15 items):" -ForegroundColor Yellow
    $items = Get-ChildItem -Path $ProjectPath -ErrorAction SilentlyContinue | Select-Object -First 15
    foreach ($item in $items) {
        $icon = if ($item.PSIsContainer) { "[DIR]" } else { "[FILE]" }
        Write-Host "   $icon $($item.Name)" -ForegroundColor Gray
    }
    Write-Host ""
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

if ($AllValid) {
    Write-Host "SUCCESS: All project directory structures are correct!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Upload Guide:" -ForegroundColor Yellow
    Write-Host "1. Use WinSCP or scp to upload the entire project directory" -ForegroundColor White
    Write-Host "2. Make sure to upload to the corresponding subdirectory on the server:" -ForegroundColor White
    Write-Host "   - tgmini20251220 -> /home/ubuntu/telegram-ai-system/tgmini20251220/" -ForegroundColor Gray
    Write-Host "   - hbwy20251220 -> /home/ubuntu/telegram-ai-system/hbwy20251220/" -ForegroundColor Gray
    Write-Host "   - aizkw20251219 -> /home/ubuntu/telegram-ai-system/aizkw20251219/" -ForegroundColor Gray
    Write-Host "3. Exclude node_modules and dist directories when uploading" -ForegroundColor White
} else {
    Write-Host "ERROR: Some project directory structures have issues" -ForegroundColor Red
    Write-Host "   Please check the output above and ensure each project has package.json" -ForegroundColor Yellow
}
