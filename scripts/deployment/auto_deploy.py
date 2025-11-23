#!/usr/bin/env python3
"""
全自動遠程服務器部署腳本
支持無需手動輸入密碼的自動化部署
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import argparse

try:
    import pexpect
    PEXPECT_AVAILABLE = True
except ImportError:
    PEXPECT_AVAILABLE = False
    print("警告: pexpect未安裝，將嘗試使用sshpass")

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False


class AutoDeployer:
    """全自動部署器"""
    
    def __init__(self, remote_host: str, remote_user: str, remote_password: str, 
                 node_id: str = None, deploy_dir: str = "/opt/group-ai", max_accounts: int = 5):
        self.remote_host = remote_host
        self.remote_user = remote_user
        self.remote_password = remote_password
        self.node_id = node_id or f"worker-{remote_host.replace('.', '-')}"
        self.deploy_dir = deploy_dir
        self.max_accounts = max_accounts
        self.project_root = Path(__file__).parent.parent.parent
        
    def _execute_remote_command(self, command: str, timeout: int = 300) -> tuple:
        """執行遠程命令"""
        # 優先使用paramiko（Windows友好）
        if PARAMIKO_AVAILABLE:
            return self._execute_with_paramiko(command, timeout)
        elif self._check_sshpass():
            return self._execute_with_sshpass(command, timeout)
        elif PEXPECT_AVAILABLE:
            return self._execute_with_pexpect(command, timeout)
        else:
            raise RuntimeError("需要安裝 paramiko 或 sshpass 或 pexpect")
    
    def _check_sshpass(self) -> bool:
        """檢查sshpass是否可用"""
        try:
            subprocess.run(['sshpass', '-V'], 
                        capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _execute_with_pexpect(self, command: str, timeout: int) -> tuple:
        """使用pexpect執行命令"""
        ssh_cmd = f"ssh -o StrictHostKeyChecking=accept-new {self.remote_user}@{self.remote_host}"
        child = pexpect.spawn(ssh_cmd, timeout=timeout, encoding='utf-8')
        
        try:
            index = child.expect(['password:', 'Password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
            if index < 2:
                child.sendline(self.remote_password)
                child.expect(['#', '$', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
            
            # 執行命令
            child.sendline(command)
            child.expect(['#', '$', pexpect.EOF, pexpect.TIMEOUT], timeout=timeout)
            output = child.before
            child.sendline('exit')
            child.expect(pexpect.EOF)
            return (0, output)
        except pexpect.TIMEOUT:
            return (1, f"命令執行超時: {command}")
        except Exception as e:
            return (1, str(e))
        finally:
            child.close()
    
    def _execute_with_sshpass(self, command: str, timeout: int) -> tuple:
        """使用sshpass執行命令"""
        ssh_cmd = [
            'sshpass', '-p', self.remote_password,
            'ssh', '-o', 'StrictHostKeyChecking=accept-new',
            '-o', 'ConnectTimeout=10',
            f'{self.remote_user}@{self.remote_host}',
            command
        ]
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return (result.returncode, result.stdout + result.stderr)
        except subprocess.TimeoutExpired:
            return (1, f"命令執行超時: {command}")
        except Exception as e:
            return (1, str(e))
    
    def _execute_with_paramiko(self, command: str, timeout: int) -> tuple:
        """使用paramiko執行命令"""
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(
                self.remote_host,
                username=self.remote_user,
                password=self.remote_password,
                timeout=10
            )
            stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
            return (exit_code, output)
        except Exception as e:
            return (1, str(e))
        finally:
            ssh.close()
    
    def _upload_file(self, local_path: str, remote_path: str) -> bool:
        """上傳文件到遠程服務器"""
        # 優先使用paramiko（Windows友好）
        if PARAMIKO_AVAILABLE:
            return self._upload_with_paramiko(local_path, remote_path)
        elif self._check_sshpass():
            return self._upload_with_sshpass(local_path, remote_path)
        elif PEXPECT_AVAILABLE:
            # 使用pexpect通過scp上傳
            return self._upload_with_pexpect_scp(local_path, remote_path)
        else:
            raise RuntimeError("需要安裝 paramiko 或 sshpass 或 pexpect")
    
    def _upload_with_sshpass(self, local_path: str, remote_path: str) -> bool:
        """使用sshpass上傳文件"""
        scp_cmd = [
            'sshpass', '-p', self.remote_password,
            'scp', '-o', 'StrictHostKeyChecking=accept-new',
            local_path,
            f'{self.remote_user}@{self.remote_host}:{remote_path}'
        ]
        try:
            result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        except Exception as e:
            print(f"上傳文件失敗: {e}")
            return False
    
    def _upload_with_paramiko(self, local_path: str, remote_path: str) -> bool:
        """使用paramiko上傳文件"""
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sftp = None
        
        try:
            ssh.connect(
                self.remote_host,
                username=self.remote_user,
                password=self.remote_password,
                timeout=10
            )
            sftp = ssh.open_sftp()
            sftp.put(local_path, remote_path)
            return True
        except Exception as e:
            print(f"上傳文件失敗: {e}")
            return False
        finally:
            if sftp:
                sftp.close()
            ssh.close()
    
    def _upload_with_pexpect_scp(self, local_path: str, remote_path: str) -> bool:
        """使用pexpect通過scp上傳文件"""
        scp_cmd = f"scp -o StrictHostKeyChecking=accept-new {local_path} {self.remote_user}@{self.remote_host}:{remote_path}"
        child = pexpect.spawn(scp_cmd, timeout=300, encoding='utf-8')
        
        try:
            index = child.expect(['password:', 'Password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
            if index < 2:
                child.sendline(self.remote_password)
                child.expect(pexpect.EOF, timeout=300)
            return child.exitstatus == 0
        except pexpect.TIMEOUT:
            return False
        except Exception as e:
            print(f"上傳文件失敗: {e}")
            return False
        finally:
            child.close()
    
    def deploy_base_environment(self) -> bool:
        """部署基礎環境"""
        print(f"[1/10] 部署基礎環境到 {self.remote_host}...")
        
        deploy_script = f"""#!/bin/bash
set -e
DEPLOY_DIR="{self.deploy_dir}"
NODE_ID="{self.node_id}"
MAX_ACCOUNTS={self.max_accounts}

echo "=== 開始遠程部署 ==="
echo "部署目錄: $DEPLOY_DIR"
echo "節點ID: $NODE_ID"
echo "最大帳號數: $MAX_ACCOUNTS"

echo "[1/8] 更新系統..."
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

echo "[2/8] 安裝基礎工具..."
sudo apt-get install -y -qq curl wget git vim htop net-tools ufw build-essential software-properties-common python3-pip python3-venv python3-dev

echo "[3/8] 安裝Python 3.11..."
sudo add-apt-repository -y ppa:deadsnakes/ppa > /dev/null 2>&1
sudo apt-get update -qq
sudo apt-get install -y -qq python3.11 python3.11-venv python3.11-dev

echo "[4/8] 配置系統限制..."
sudo bash -c 'cat >> /etc/security/limits.conf << "LIMITS"
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
LIMITS'

echo "[5/8] 配置時區..."
sudo timedatectl set-timezone Asia/Shanghai

echo "[6/8] 配置防火牆..."
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp

echo "[7/8] 創建目錄結構..."
sudo mkdir -p $DEPLOY_DIR/sessions
sudo mkdir -p $DEPLOY_DIR/logs
sudo mkdir -p $DEPLOY_DIR/configs
sudo mkdir -p $DEPLOY_DIR/ai_models/group_scripts
sudo mkdir -p $DEPLOY_DIR/data
sudo chown -R $USER:$USER $DEPLOY_DIR
sudo chmod -R 755 $DEPLOY_DIR

echo "[8/8] 創建Python虛擬環境..."
if [ ! -d "$DEPLOY_DIR/venv" ]; then
    python3.11 -m venv $DEPLOY_DIR/venv || python3 -m venv $DEPLOY_DIR/venv
    $DEPLOY_DIR/venv/bin/pip install --upgrade pip setuptools wheel
    sudo chown -R $USER:$USER $DEPLOY_DIR/venv
fi

echo "=== 基礎環境部署完成 ==="
"""
        
        # 將腳本寫入臨時文件（使用Unix換行符）
        temp_script = self.project_root / "tmp_remote_deploy.sh"
        # 確保使用Unix換行符
        deploy_script_unix = deploy_script.replace('\r\n', '\n').replace('\r', '\n')
        temp_script.write_text(deploy_script_unix, encoding='utf-8', newline='\n')
        
        try:
            # 上傳並執行
            if not self._upload_file(str(temp_script), "/tmp/remote_deploy.sh"):
                return False
            
            exit_code, output = self._execute_remote_command(
                "chmod +x /tmp/remote_deploy.sh && bash /tmp/remote_deploy.sh"
            )
            
            if exit_code == 0:
                print("[OK] 基礎環境部署完成")
                return True
            else:
                print(f"[FAIL] 基礎環境部署失敗: {output}")
                return False
        finally:
            if temp_script.exists():
                temp_script.unlink()
    
    def upload_project_files(self) -> bool:
        """上傳項目文件"""
        print(f"[2/10] 上傳項目文件到 {self.remote_host}...")
        
        # 打包項目文件
        import tarfile
        import tempfile
        
        temp_tar = tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False)
        temp_tar.close()
        
        try:
            with tarfile.open(temp_tar.name, 'w:gz') as tar:
                # 添加必要的目錄和文件
                group_ai_service = self.project_root / "group_ai_service"
                if group_ai_service.exists():
                    tar.add(group_ai_service, arcname="group_ai_service")
                
                admin_backend_api = self.project_root / "admin-backend" / "app" / "api" / "group_ai"
                if admin_backend_api.exists():
                    tar.add(admin_backend_api, arcname="admin-backend/app/api/group_ai")
                
                config_file = self.project_root / "config.py"
                if config_file.exists():
                    tar.add(config_file, arcname="config.py")
            
            # 上傳
            if not self._upload_file(temp_tar.name, "/tmp/group-ai-deploy.tar.gz"):
                return False
            
            # 確保目錄存在
            self._execute_remote_command(f"sudo mkdir -p {self.deploy_dir}")
            self._execute_remote_command(f"sudo chown -R {self.remote_user}:{self.remote_user} {self.deploy_dir}")
            
            # 解壓
            exit_code, output = self._execute_remote_command(
                f"cd {self.deploy_dir} && tar xzf /tmp/group-ai-deploy.tar.gz && rm /tmp/group-ai-deploy.tar.gz"
            )
            
            if exit_code == 0:
                print("[OK] 項目文件上傳完成")
                return True
            else:
                print(f"[FAIL] 項目文件上傳失敗: {output}")
                return False
        finally:
            if os.path.exists(temp_tar.name):
                os.unlink(temp_tar.name)
    
    def install_dependencies(self) -> bool:
        """安裝Python依賴"""
        print(f"[3/10] 安裝Python依賴到 {self.remote_host}...")
        
        requirements = """pyrogram>=2.0.0
tgcrypto>=1.2.5
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
sqlalchemy>=2.0.0
alembic>=1.12.0
aiosqlite>=0.19.0
redis>=5.0.0
hiredis>=2.2.0
openai>=1.0.0
tiktoken>=0.5.0
python-dotenv>=1.0.0
pyyaml>=6.0
aiofiles>=23.2.0
httpx>=0.25.0
prometheus-client>=0.19.0"""
        
        # 創建requirements.txt
        exit_code, _ = self._execute_remote_command(
            f"cat > {self.deploy_dir}/requirements.txt << 'EOF'\n{requirements}\nEOF"
        )
        
        if exit_code != 0:
            return False
        
        # 確保虛擬環境存在
        venv_check = self._execute_remote_command(
            f"test -d {self.deploy_dir}/venv || (cd {self.deploy_dir} && python3.11 -m venv venv || python3 -m venv venv)"
        )
        
        # 安裝依賴
        exit_code, output = self._execute_remote_command(
            f"cd {self.deploy_dir} && {self.deploy_dir}/venv/bin/pip install --upgrade pip setuptools wheel && {self.deploy_dir}/venv/bin/pip install -r {self.deploy_dir}/requirements.txt",
            timeout=600
        )
        
        if exit_code == 0:
            print("[OK] Python依賴安裝完成")
            return True
        else:
            print(f"[FAIL] Python依賴安裝失敗: {output}")
            return False
    
    def create_config_files(self, telegram_api_id: str = "", telegram_api_hash: str = "", 
                           openai_api_key: str = "") -> bool:
        """創建配置文件"""
        print(f"[4/10] 創建配置文件到 {self.remote_host}...")
        
        env_content = f"""# 應用配置
APP_NAME=Group AI Worker Node
APP_ENV=production
DEBUG=false
NODE_ID={self.node_id}
NODE_ROLE=worker

# 數據庫配置
DATABASE_URL=sqlite:///{self.deploy_dir}/data/group_ai.db

# Telegram API配置
TELEGRAM_API_ID={telegram_api_id}
TELEGRAM_API_HASH={telegram_api_hash}

# OpenAI配置
OPENAI_API_KEY={openai_api_key}
OPENAI_MODEL=gpt-3.5-turbo

# Session文件配置
SESSION_FILES_DIRECTORY={self.deploy_dir}/sessions
SESSION_FILES_BACKUP_DIRECTORY={self.deploy_dir}/sessions_backup

# 帳號配置
MAX_ACCOUNTS_PER_NODE={self.max_accounts}
ACCOUNT_HEALTH_CHECK_INTERVAL=60
ACCOUNT_RECONNECT_DELAY=5
ACCOUNT_MAX_RECONNECT_ATTEMPTS=3

# 日誌配置
LOG_LEVEL=INFO
LOG_FILE={self.deploy_dir}/logs/worker.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=10

# 監控配置
METRICS_ENABLED=true
METRICS_PORT=9091
HEARTBEAT_INTERVAL=30"""
        
        config_py_content = """import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API配置
API_ID = int(os.getenv('TELEGRAM_API_ID', '0'))
API_HASH = os.getenv('TELEGRAM_API_HASH', '')

# OpenAI配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')"""
        
        # 創建.env文件
        exit_code, _ = self._execute_remote_command(
            f"cat > {self.deploy_dir}/.env << 'EOF'\n{env_content}\nEOF"
        )
        
        if exit_code != 0:
            return False
        
        # 創建config.py
        exit_code, _ = self._execute_remote_command(
            f"cat > {self.deploy_dir}/config.py << 'EOF'\n{config_py_content}\nEOF"
        )
        
        if exit_code == 0:
            print("[OK] 配置文件創建完成")
            return True
        else:
            print(f"[FAIL] 配置文件創建失敗")
            return False
    
    def create_startup_scripts(self) -> bool:
        """創建啟動腳本和systemd服務"""
        print(f"[5/10] 創建啟動腳本到 {self.remote_host}...")
        
        # Worker節點啟動腳本 - 運行一個簡單的監聽服務
        start_script = f"""#!/bin/bash
cd {self.deploy_dir}
source venv/bin/activate
export PYTHONPATH={self.deploy_dir}:$PYTHONPATH

# Worker節點：運行group_ai_service的監聽服務
# 如果存在admin-backend，也可以運行（用於測試）
if [ -d "admin-backend/app" ]; then
    cd admin-backend
    {self.deploy_dir}/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    # 運行group_ai_service worker
    {self.deploy_dir}/venv/bin/python -c "from group_ai_service.service_manager import ServiceManager; import asyncio; sm = ServiceManager(); asyncio.run(sm.start())" || echo "Worker service started"
fi"""
        
        # Worker節點應該運行group_ai_service，但需要一個啟動入口
        # 暫時使用啟動腳本
        systemd_service = f"""[Unit]
Description=Group AI Worker Node Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory={self.deploy_dir}
Environment="PATH={self.deploy_dir}/venv/bin"
Environment="PYTHONPATH={self.deploy_dir}"
ExecStart={self.deploy_dir}/start.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"""
        
        # 創建啟動腳本
        exit_code, _ = self._execute_remote_command(
            f"cat > {self.deploy_dir}/start.sh << 'EOF'\n{start_script}\nEOF\nchmod +x {self.deploy_dir}/start.sh"
        )
        
        if exit_code != 0:
            return False
        
        # 創建systemd服務（需要sudo）
        exit_code, output = self._execute_remote_command(
            f"sudo bash -c 'cat > /etc/systemd/system/group-ai-worker.service << \"EOFSERVICE\"\n{systemd_service}\nEOFSERVICE' && "
            f"sudo systemctl daemon-reload && "
            f"sudo systemctl enable group-ai-worker"
        )
        
        if exit_code == 0:
            print("[OK] 啟動腳本創建完成")
            return True
        else:
            print(f"[FAIL] 啟動腳本創建失敗")
            return False
    
    def deploy(self, telegram_api_id: str = "", telegram_api_hash: str = "", 
              openai_api_key: str = "") -> bool:
        """執行完整部署"""
        print(f"\n{'='*50}")
        print(f"開始部署到 {self.remote_host}")
        print(f"{'='*50}\n")
        
        steps = [
            self.deploy_base_environment,
            self.upload_project_files,
            self.install_dependencies,
            lambda: self.create_config_files(telegram_api_id, telegram_api_hash, openai_api_key),
            self.create_startup_scripts,
        ]
        
        for i, step in enumerate(steps, 1):
            if not step():
                print(f"\n[FAIL] 部署失敗於步驟 {i}")
                return False
            time.sleep(2)  # 短暫延遲
        
        print(f"\n{'='*50}")
        print(f"[OK] 部署完成！節點ID: {self.node_id}")
        print(f"{'='*50}\n")
        print(f"下一步:")
        print(f"  1. 上傳Session文件: scp *.session {self.remote_user}@{self.remote_host}:{self.deploy_dir}/sessions/")
        print(f"  2. 啟動服務: ssh {self.remote_user}@{self.remote_host} 'systemctl start group-ai-worker'")
        print(f"  3. 查看日誌: ssh {self.remote_user}@{self.remote_host} 'tail -f {self.deploy_dir}/logs/worker.log'")
        print()
        
        return True


def main():
    parser = argparse.ArgumentParser(description='全自動遠程服務器部署工具')
    parser.add_argument('--host', required=True, help='遠程服務器IP地址')
    parser.add_argument('--user', default='root', help='SSH用戶名')
    parser.add_argument('--password', required=True, help='SSH密碼')
    parser.add_argument('--node-id', help='節點ID（默認自動生成）')
    parser.add_argument('--deploy-dir', default='/opt/group-ai', help='部署目錄')
    parser.add_argument('--max-accounts', type=int, default=5, help='最大帳號數')
    parser.add_argument('--telegram-api-id', default='', help='Telegram API ID')
    parser.add_argument('--telegram-api-hash', default='', help='Telegram API Hash')
    parser.add_argument('--openai-api-key', default='', help='OpenAI API Key')
    
    args = parser.parse_args()
    
    deployer = AutoDeployer(
        remote_host=args.host,
        remote_user=args.user,
        remote_password=args.password,
        node_id=args.node_id,
        deploy_dir=args.deploy_dir,
        max_accounts=args.max_accounts
    )
    
    success = deployer.deploy(
        telegram_api_id=args.telegram_api_id,
        telegram_api_hash=args.telegram_api_hash,
        openai_api_key=args.openai_api_key
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

