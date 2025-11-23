# 并行部署所有服务器脚本
# 使用方法: .\deploy_all_servers_parallel.ps1

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "并行部署所有服务器" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 服务器配置
$servers = @(
    @{
        Name = "洛杉矶服务器"
        IP = "165.154.255.48"
        Username = "ubuntu"
        Password = "8iDcGrYb52Fxpzee"
    },
    @{
        Name = "马尼拉服务器"
        IP = "165.154.233.179"
        Username = "ubuntu"
        Password = "8iDcGrYb52Fxpzee"
    },
    @{
        Name = "worker-01"
        IP = "165.154.254.99"
        Username = "ubuntu"
        Password = "Along2025!!!"
    }
)

Write-Host "准备部署 $($servers.Count) 个服务器..." -ForegroundColor Yellow
Write-Host ""

# 创建部署作业
$jobs = @()
$jobResults = @{}

foreach ($server in $servers) {
    Write-Host "启动部署作业: $($server.Name) ($($server.IP))..." -ForegroundColor Cyan
    
    # 获取项目根目录（当前脚本所在目录的父目录的父目录）
    $scriptPath = $PSScriptRoot
    $projectRoot = Split-Path -Parent (Split-Path -Parent $scriptPath)
    $deployScript = Join-Path $scriptPath "deploy_to_server.ps1"
    
    $job = Start-Job -ScriptBlock {
        param($ServerIP, $Username, $Password, $ServerName, $ProjectRoot, $DeployScript)
        
        # 设置工作目录
        Set-Location $ProjectRoot
        
        # 执行部署
        $output = & pwsh -ExecutionPolicy Bypass -File $DeployScript `
            -ServerIP $ServerIP `
            -Username $Username `
            -Password $Password `
            -ServerName $ServerName 2>&1
        
        return @{
            ServerName = $ServerName
            ServerIP = $ServerIP
            Output = $output
            Success = $LASTEXITCODE -eq 0
        }
    } -ArgumentList $server.IP, $server.Username, $server.Password, $server.Name, $projectRoot, $deployScript
    
    $jobs += @{
        Job = $job
        Server = $server
    }
    
    Write-Host "  ✓ 作业已启动 (Job ID: $($job.Id))" -ForegroundColor Green
}

Write-Host "`n所有部署作业已启动，等待完成...`n" -ForegroundColor Yellow

# 显示进度
$completed = 0
$total = $jobs.Count

while ($completed -lt $total) {
    Start-Sleep -Seconds 2
    
    foreach ($jobInfo in $jobs) {
        $job = $jobInfo.Job
        $server = $jobInfo.Server
        
        if ($job.State -eq "Completed" -and -not $jobResults.ContainsKey($server.IP)) {
            $result = Receive-Job -Job $job
            $jobResults[$server.IP] = $result
            $completed++
            
            Write-Host "[$completed/$total] $($server.Name) 部署完成" -ForegroundColor $(if ($result.Success) { "Green" } else { "Red" })
        } elseif ($job.State -eq "Failed") {
            if (-not $jobResults.ContainsKey($server.IP)) {
                $jobResults[$server.IP] = @{
                    ServerName = $server.Name
                    ServerIP = $server.IP
                    Success = $false
                    Output = "作业失败"
                }
                $completed++
                Write-Host "[$completed/$total] $($server.Name) 部署失败" -ForegroundColor Red
            }
        }
    }
    
    # 显示进度条
    $percent = [math]::Round(($completed / $total) * 100)
    Write-Progress -Activity "并行部署中" -Status "$completed/$total 完成" -PercentComplete $percent
}

Write-Progress -Activity "并行部署中" -Completed

# 等待所有作业完成
$jobs | ForEach-Object { Wait-Job -Job $_.Job | Out-Null }

# 清理作业
$jobs | ForEach-Object { Remove-Job -Job $_.Job }

# 显示结果摘要
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "部署结果摘要" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$successCount = 0
$failCount = 0

foreach ($server in $servers) {
    $result = $jobResults[$server.IP]
    
    if ($result.Success) {
        Write-Host "✓ $($server.Name) ($($server.IP))" -ForegroundColor Green
        Write-Host "  状态: 部署成功" -ForegroundColor Gray
        $successCount++
    } else {
        Write-Host "✗ $($server.Name) ($($server.IP))" -ForegroundColor Red
        Write-Host "  状态: 部署失败" -ForegroundColor Gray
        Write-Host "  错误: $($result.Output -join '`n')" -ForegroundColor Yellow
        $failCount++
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "总计: 成功 $successCount, 失败 $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })
Write-Host "========================================`n" -ForegroundColor Cyan

# 显示详细输出（可选）
$showDetails = Read-Host "是否显示详细输出? (y/n)"
if ($showDetails -eq "y") {
    foreach ($server in $servers) {
        $result = $jobResults[$server.IP]
        Write-Host "`n========================================" -ForegroundColor Cyan
        Write-Host "$($server.Name) 详细输出" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ($result.Output -join "`n")
        Write-Host ""
    }
}

