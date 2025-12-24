# 本地构建指南

## 📋 关于文件位置

**重要说明**：我没有移动任何文件。文件还在原来的位置。

如果你创建了 `wxedge_storage` 文件夹并想在那里构建项目，请：
1. 将项目文件复制到 `wxedge_storage` 文件夹
2. 或者使用现有的位置（`D:\telegram-ai-system`）

## 🔍 当前项目位置

根据检测，当前找到的项目位置：

- **hbwy20251220**：`D:\telegram-ai-system\react-vite-template\hbwy20251220`
- **tgmini20251220**：未找到（可能在 `wxedge_storage` 或其他位置）
- **aizkw20251219**：未找到（可能在 `wxedge_storage` 或其他位置）

## 🚀 使用本地构建脚本

我已经创建了一个智能构建脚本，会自动查找项目位置（优先查找 `wxedge_storage`）：

```powershell
# 在 PowerShell 中执行
cd D:\telegram-ai-system
.\scripts\local\build_and_upload.ps1
```

这个脚本会：
1. 自动查找项目位置（优先 `wxedge_storage`，然后 `telegram-ai-system`）
2. 构建所有找到的项目
3. 生成上传命令

## 📁 如果你想使用 wxedge_storage

如果你想让项目在 `wxedge_storage` 文件夹中：

### 方法 1：复制项目到 wxedge_storage

```powershell
# 创建 wxedge_storage 文件夹（如果不存在）
New-Item -ItemType Directory -Force -Path "D:\wxedge_storage"

# 复制项目（根据实际情况调整源路径）
Copy-Item -Path "D:\telegram-ai-system\tgmini20251220" -Destination "D:\wxedge_storage\tgmini20251220" -Recurse
Copy-Item -Path "D:\telegram-ai-system\react-vite-template\hbwy20251220" -Destination "D:\wxedge_storage\hbwy20251220" -Recurse
Copy-Item -Path "D:\telegram-ai-system\aizkw20251219" -Destination "D:\wxedge_storage\aizkw20251219" -Recurse
```

### 方法 2：直接在现有位置构建

如果你不想移动文件，可以直接在现有位置构建：

```powershell
# 构建 hongbao（已找到）
cd D:\telegram-ai-system\react-vite-template\hbwy20251220
npm install
npm run build

# 构建其他项目（请根据实际路径调整）
# cd D:\wxedge_storage\tgmini20251220  # 或其他位置
# npm install
# npm run build
```

## 📤 上传到服务器

构建完成后，上传 `dist` 目录到服务器：

```powershell
# 上传 tgmini
scp -r "D:\wxedge_storage\tgmini20251220\dist" ubuntu@10.56.198.218:/opt/web3-sites/tgmini20251220/

# 上传 hongbao
scp -r "D:\telegram-ai-system\react-vite-template\hbwy20251220\dist" ubuntu@10.56.198.218:/opt/web3-sites/hbwy20251220/

# 上传 aizkw
scp -r "D:\wxedge_storage\aizkw20251219\dist" ubuntu@10.56.198.218:/opt/web3-sites/aizkw20251219/
```

## 🔧 在服务器上启动服务

```bash
# SSH 连接到服务器
ssh ubuntu@10.56.198.218

# 启动服务
cd /opt/web3-sites

# 启动 tgmini
pm2 start serve --name tgmini-frontend -- -s tgmini20251220/dist -l 3001

# 启动 hongbao
pm2 start serve --name hongbao-frontend -- -s hbwy20251220/dist -l 3002

# 启动 aizkw
pm2 start serve --name aizkw-frontend -- -s aizkw20251219/dist -l 3003

# 保存 PM2 配置
pm2 save
```

## ❓ 常见问题

### Q: 文件在哪里？
A: 文件还在原来的位置，我没有移动任何文件。如果你想在 `wxedge_storage` 中使用，需要手动复制。

### Q: 如何找到项目的实际位置？
A: 使用构建脚本会自动查找，或者手动检查：
- 查找 `package.json` 文件
- 查看项目名称匹配的文件夹

### Q: 构建脚本找不到项目怎么办？
A: 可以手动指定路径，或者将项目放在 `wxedge_storage` 或 `telegram-ai-system` 目录下。

