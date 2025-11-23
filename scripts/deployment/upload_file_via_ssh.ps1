# 通过 SSH 上传文件的辅助函数
# 支持多种方法：Posh-SSH、SCP、SFTP

param(
    [Parameter(Mandatory=$true)]
    [object]$Session,
    
    [Parameter(Mandatory=$true)]
    [string]$LocalFile,
    
    [Parameter(Mandatory=$true)]
    [string]$RemotePath,
    
    [Parameter(Mandatory=$false)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$false)]
    [string]$Username,
    
    [Parameter(Mandatory=$false)]
    [string]$Password
)

$ErrorActionPreference = "Continue"

# 方法 1: 使用 Posh-SSH Set-SCPItem (3.x)
if (Get-Command Set-SCPItem -ErrorAction SilentlyContinue) {
    try {
        Set-SCPItem -Session $Session -Path $LocalFile -Destination $RemotePath -ErrorAction Stop
        return $true
    } catch {
        Write-Host "  Set-SCPItem 失败: $_" -ForegroundColor Yellow
    }
}

# 方法 2: 使用 Posh-SSH Set-SCPFile (2.x)
if (Get-Command Set-SCPFile -ErrorAction SilentlyContinue) {
    try {
        # 检查参数格式
        $params = @{
            LocalFile = $LocalFile
            RemotePath = $RemotePath
        }
        
        # 尝试不同的参数名
        if ($Session.SessionId) {
            $params['SessionId'] = $Session.SessionId
        } elseif ($Session) {
            $params['Session'] = $Session
        }
        
        Set-SCPFile @params -ErrorAction Stop
        return $true
    } catch {
        Write-Host "  Set-SCPFile 失败: $_" -ForegroundColor Yellow
    }
}

# 方法 3: 使用原生 SCP 命令
if ($ServerIP -and $Username -and $Password) {
    if (Get-Command scp -ErrorAction SilentlyContinue) {
        try {
            $env:SSHPASS = $Password
            $scpOutput = scp -o StrictHostKeyChecking=no -o ConnectTimeout=30 "$LocalFile" "${Username}@${ServerIP}:${RemotePath}" 2>&1
            Remove-Item Env:\SSHPASS -ErrorAction SilentlyContinue
            
            if ($LASTEXITCODE -eq 0) {
                return $true
            } else {
                Write-Host "  SCP 失败: $scpOutput" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  SCP 错误: $_" -ForegroundColor Yellow
            Remove-Item Env:\SSHPASS -ErrorAction SilentlyContinue
        }
    }
}

# 方法 4: 使用 SFTP (通过 SSH 命令)
if ($ServerIP -and $Username -and $Password) {
    try {
        # 使用 PowerShell 的 SFTP 功能（如果可用）
        $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
        $credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
        
        # 创建临时 SFTP 脚本
        $sftpScript = @"
put "$LocalFile" "$RemotePath"
quit
"@
        $sftpScript | Out-File -FilePath "$env:TEMP\sftp_upload.txt" -Encoding ASCII
        
        $env:SSHPASS = $Password
        $sftpOutput = sshpass -e sftp -o StrictHostKeyChecking=no -b "$env:TEMP\sftp_upload.txt" "${Username}@${ServerIP}" 2>&1
        Remove-Item Env:\SSHPASS -ErrorAction SilentlyContinue
        Remove-Item "$env:TEMP\sftp_upload.txt" -ErrorAction SilentlyContinue
        
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
    } catch {
        Write-Host "  SFTP 失败: $_" -ForegroundColor Yellow
    }
}

# 方法 5: 分块传输（适用于大文件）
if ($Session -and (Test-Path $LocalFile)) {
    try {
        Write-Host "  使用分块传输..." -ForegroundColor Gray
        $fileBytes = [IO.File]::ReadAllBytes($LocalFile)
        $chunkSize = 32768  # 32KB chunks
        $totalChunks = [Math]::Ceiling($fileBytes.Length / $chunkSize)
        $fileName = Split-Path $LocalFile -Leaf
        $remoteFile = "$RemotePath/$fileName"
        
        # 在远程服务器上创建文件
        Invoke-SSHCommand -SessionId $Session.SessionId -Command "touch $remoteFile; chmod 600 $remoteFile" | Out-Null
        
        # 分块传输
        for ($i = 0; $i -lt $totalChunks; $i++) {
            $start = $i * $chunkSize
            $length = [Math]::Min($chunkSize, $fileBytes.Length - $start)
            $chunk = $fileBytes[$start..($start + $length - 1)]
            $base64Chunk = [Convert]::ToBase64String($chunk)
            
            $result = Invoke-SSHCommand -SessionId $Session.SessionId -Command @"
echo '$base64Chunk' | base64 -d >> $remoteFile
"@
            
            if ($result.ExitStatus -ne 0) {
                throw "分块传输失败 (块 $($i+1)/$totalChunks)"
            }
            
            if (($i + 1) % 10 -eq 0) {
                Write-Host "    进度: $($i+1)/$totalChunks" -ForegroundColor Gray
            }
        }
        
        Write-Host "  ✓ 分块传输完成" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  分块传输失败: $_" -ForegroundColor Red
    }
}

return $false

