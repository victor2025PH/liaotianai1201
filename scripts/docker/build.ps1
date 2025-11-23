# Docker 镜像构建脚本 (PowerShell)
# 用法: .\build.ps1 [service] [tag] [-Push]

param(
    [Parameter(Mandatory=$false)]
    [string]$Service = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Tag = "latest",
    
    [Parameter(Mandatory=$false)]
    [switch]$Push = $false
)

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# 默认配置
$Registry = if ($env:DOCKER_REGISTRY) { $env:DOCKER_REGISTRY } else { "group-ai" }
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# 构建函数
function Build-Image {
    param(
        [string]$ServiceName,
        [string]$ImageTag
    )
    
    $Context = ""
    $Dockerfile = ""
    $BuildArgs = @()
    
    switch ($ServiceName) {
        "admin-backend" { 
            $Context = Join-Path $ProjectRoot "admin-backend"
            $Dockerfile = Join-Path $ProjectRoot "admin-backend\Dockerfile"
        }
        "admin-frontend" { 
            $Context = Join-Path $ProjectRoot "admin-frontend"
            $Dockerfile = Join-Path $ProjectRoot "admin-frontend\Dockerfile"
            $BuildArgs = @("--build-arg", "VITE_API_BASE_URL=$($env:VITE_API_BASE_URL)")
        }
        "saas-demo" { 
            $Context = Join-Path $ProjectRoot "saas-demo"
            $Dockerfile = Join-Path $ProjectRoot "saas-demo\Dockerfile"
            $BuildArgs = @("--build-arg", "NEXT_PUBLIC_API_URL=$($env:NEXT_PUBLIC_API_URL)")
        }
        "session-service" { 
            $Context = $ProjectRoot
            $Dockerfile = Join-Path $ProjectRoot "deploy\session-service.Dockerfile"
        }
        "all" {
            Write-ColorOutput "构建所有服务..." "Yellow"
            Build-Image "admin-backend" $ImageTag
            Build-Image "admin-frontend" $ImageTag
            Build-Image "saas-demo" $ImageTag
            Build-Image "session-service" $ImageTag
            return
        }
        default {
            Write-ColorOutput "错误: 未知的服务 '$ServiceName'" "Red"
            Write-ColorOutput "可用服务: admin-backend, admin-frontend, saas-demo, session-service, all" "Yellow"
            exit 1
        }
    }
    
    $ImageName = "$Registry/$ServiceName`:$ImageTag"
    
    Write-ColorOutput "构建镜像: $ImageName" "Green"
    Write-ColorOutput "Context: $Context" "Gray"
    Write-ColorOutput "Dockerfile: $Dockerfile" "Gray"
    
    # 构建镜像
    $BuildCmd = @("build", "-f", $Dockerfile, "-t", $ImageName) + $BuildArgs + $Context
    docker $BuildCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "构建失败!" "Red"
        exit 1
    }
    
    # 如果指定了推送，则推送镜像
    if ($Push) {
        Write-ColorOutput "推送镜像: $ImageName" "Yellow"
        docker push $ImageName
        
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "推送失败!" "Red"
            exit 1
        }
    }
    
    Write-ColorOutput "✓ 构建完成: $ImageName" "Green"
}

# 主函数
if ([string]::IsNullOrEmpty($Service)) {
    Write-ColorOutput "错误: 请指定要构建的服务" "Red"
    Write-ColorOutput "用法: .\build.ps1 [service] [tag] [-Push]" "Yellow"
    Write-ColorOutput ""
    Write-ColorOutput "服务:" "Cyan"
    Write-ColorOutput "  admin-backend    - 后端 API 服务"
    Write-ColorOutput "  admin-frontend   - 前端管理界面 (Vite)"
    Write-ColorOutput "  saas-demo       - SaaS Demo 前端 (Next.js)"
    Write-ColorOutput "  session-service - Session 服务"
    Write-ColorOutput "  all             - 构建所有服务"
    Write-ColorOutput ""
    Write-ColorOutput "示例:" "Cyan"
    Write-ColorOutput "  .\build.ps1 admin-backend latest"
    Write-ColorOutput "  .\build.ps1 admin-backend v1.0.0 -Push"
    Write-ColorOutput "  .\build.ps1 all latest"
    exit 1
}

Build-Image $Service $Tag

