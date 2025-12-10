import paramiko
import os
import sys

# Configuration
HOST = "165.154.235.170"
USER = "ubuntu"
PASS = "Along2025!!!"
KEY_DIR = os.path.join("scripts", "local", "keys")
KEY_PATH = os.path.join(KEY_DIR, "server_key")

def setup_ssh():
    print(f"🚀 Setting up passwordless SSH for {USER}@{HOST}...")

    # 1. Generate Key Pair if missing
    if not os.path.exists(KEY_DIR):
        os.makedirs(KEY_DIR)
    
    if not os.path.exists(KEY_PATH):
        print("🔑 Generating new SSH key pair...")
        # Use ssh-keygen
        cmd = f'ssh-keygen -t rsa -b 4096 -f "{KEY_PATH}" -N "" -q'
        if os.system(cmd) != 0:
            print("❌ Failed to generate SSH key. Please ensure ssh-keygen is in your PATH.")
            return
        print("✅ Key pair generated.")
    else:
        print("✅ Using existing key pair.")

    # 2. Read Public Key
    try:
        with open(f"{KEY_PATH}.pub", "r") as f:
            pub_key = f.read().strip()
    except Exception as e:
        print(f"❌ Failed to read public key: {e}")
        return

    # 3. Upload to Server
    try:
        print("🔌 Connecting to server...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, username=USER, password=PASS)
        
        print("📤 Installing public key to ~/.ssh/authorized_keys...")
        # Check if key already exists to avoid duplicates
        check_cmd = f"grep -q '{pub_key}' ~/.ssh/authorized_keys 2>/dev/null"
        stdin, stdout, stderr = client.exec_command(check_cmd)
        
        if stdout.channel.recv_exit_status() == 0:
            print("✅ Key already authorized on server.")
        else:
            install_cmd = f"mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '{pub_key}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
            stdin, stdout, stderr = client.exec_command(install_cmd)
            if stdout.channel.recv_exit_status() == 0:
                print("✅ Key installed successfully!")
            else:
                print(f"❌ Server error: {stderr.read().decode()}")
                
        client.close()
        
    except ImportError:
        print("❌ 'paramiko' library not found. Please run: pip install paramiko")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    setup_ssh()

