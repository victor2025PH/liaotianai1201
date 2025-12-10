import paramiko
import os
from scp import SCPClient
import sys

# 配置
HOST = "165.154.235.170"
PASSWORD = "Along2025!!!"
# 先尝试 ubuntu，失败则 root
USERS = ["ubuntu", "root"]

def create_client(user):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Trying to connect as {user}...")
        client.connect(HOST, username=user, password=PASSWORD, timeout=10)
        return client
    except Exception as e:
        print(f"Failed to connect as {user}: {e}")
        return None

def run_cmd(client, cmd, desc):
    print(f"Executing: {desc}...")
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"❌ Error in {desc}: {stderr.read().decode()}")
        return False
    print(f"✅ {desc} success")
    return True

def main():
    client = None
    user = None
    for u in USERS:
        client = create_client(u)
        if client:
            user = u
            break
    
    if not client:
        print("❌ Could not connect to server.")
        return

    print(f"🚀 Connected as {user}")
    
    # 1. Install Dependencies
    print("📦 Installing system dependencies...")
    setup_cmds = [
        "export DEBIAN_FRONTEND=noninteractive",
        "apt-get update",
        "apt-get install -y curl wget git nginx python3-pip python3-venv unzip",
        # Install Node 20
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs"
    ]
    
    prefix = "sudo " if user != "root" else ""
    full_cmd = " && ".join([f"{prefix}{cmd}" for cmd in setup_cmds])
    
    # Check if node exists to avoid slow re-install
    stdin, stdout, stderr = client.exec_command("node -v")
    if stdout.channel.recv_exit_status() != 0:
        if not run_cmd(client, full_cmd, "Install Environment"):
            return
    else:
        print("✅ Environment already installed")

    # 2. Prepare Directory
    remote_dir = f"/home/{user}/telegram-ai-system" if user == "ubuntu" else "/root/telegram-ai-system"
    run_cmd(client, f"mkdir -p {remote_dir}", "Create project dir")
    run_cmd(client, f"{prefix}chown -R {user}:{user} {remote_dir}", "Fix permissions")

    # 3. Upload Code (Manual Step Simulation)
    # Since we can't easily upload folders recursively with basic paramiko without scp library (which might be missing),
    # we will use tar to package local code and upload one file.
    
    print("📦 Packaging local code...")
    local_tar = "deploy_package.tar.gz"
    # Tar command excluding node_modules, .next, .git, venv
    # We use python to create tar to be cross-platform compatible
    import tarfile
    
    with tarfile.open(local_tar, "w:gz") as tar:
        for root, dirs, files in os.walk("."):
            # Exclude dirs
            dirs[:] = [d for d in dirs if d not in ["node_modules", ".next", ".git", "venv", "__pycache__"]]
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".tsx", ".json", ".md", ".sh", ".conf", ".css", ".html", "Dockerfile", "requirements.txt", ".env.example")):
                     tar.add(os.path.join(root, file))
    
    print("📤 Uploading code...")
    sftp = client.open_sftp()
    sftp.put(local_tar, f"{remote_dir}/{local_tar}")
    sftp.close()
    
    print("📦 Extracting code...")
    run_cmd(client, f"cd {remote_dir} && tar -xzf {local_tar} && rm {local_tar}", "Extract code")
    
    # 4. Backend Setup
    print("🐍 Setting up Backend...")
    backend_cmds = [
        f"cd {remote_dir}/admin-backend",
        "python3 -m venv venv",
        f"{remote_dir}/admin-backend/venv/bin/pip install -r requirements.txt"
    ]
    run_cmd(client, " && ".join(backend_cmds), "Setup Backend")
    
    # 5. Frontend Setup
    print("⚛️ Setting up Frontend...")
    frontend_cmds = [
        f"cd {remote_dir}/saas-demo",
        "npm install",
        "npm run build",
        "mkdir -p .next/standalone/.next/static .next/standalone/public",
        "cp -r .next/static/* .next/standalone/.next/static/",
        "cp -r public/* .next/standalone/public/"
    ]
    run_cmd(client, " && ".join(frontend_cmds), "Setup Frontend")

    # 6. Configure Systemd
    print("⚙️ Configuring Services...")
    # Update service files with correct paths
    # We will upload a helper script to generate service files on the server
    
    service_script = f"""
cat > /etc/systemd/system/liaotian-backend.service <<EOF
[Unit]
Description=Backend
After=network.target

[Service]
User={user}
WorkingDirectory={remote_dir}/admin-backend
ExecStart={remote_dir}/admin-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/liaotian-frontend.service <<EOF
[Unit]
Description=Frontend
After=network.target

[Service]
User={user}
WorkingDirectory={remote_dir}/saas-demo/.next/standalone
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/usr/bin/node server.js
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable liaotian-backend liaotian-frontend
systemctl restart liaotian-backend liaotian-frontend
"""
    
    # Execute service setup as root
    if user != "root":
        # Write to tmp then sudo move
        run_cmd(client, f"echo '{service_script}' > /tmp/setup_services.sh && sudo bash /tmp/setup_services.sh", "Setup Systemd")
    else:
        run_cmd(client, f"echo '{service_script}' | bash", "Setup Systemd")

    # 7. Configure Nginx
    print("🌐 Configuring Nginx...")
    nginx_conf = """
server {
    listen 80;
    server_name _;  # Catch all

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }

    location ~* ^/api/v1/.*/ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    location /_next/static/ {
        proxy_pass http://127.0.0.1:3000;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
"""
    if user != "root":
         run_cmd(client, f"echo '{nginx_conf}' > /tmp/default && sudo mv /tmp/default /etc/nginx/sites-available/default && sudo systemctl reload nginx", "Setup Nginx")
    else:
         run_cmd(client, f"echo '{nginx_conf}' > /etc/nginx/sites-available/default && systemctl reload nginx", "Setup Nginx")

    print("✅ Deployment Complete! Visit http://" + HOST)
    client.close()

if __name__ == "__main__":
    main()

