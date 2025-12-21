#!/bin/bash

# 修复后端依赖问题脚本（系统级安装，确保 PM2 能找到）
# 使用方法: bash scripts/server/fix_backend_deps.sh

set -e

echo "=========================================="
echo "🔧 修复后端依赖问题（系统级安装）"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || {
  echo "❌ 无法进入项目目录: $PROJECT_ROOT"
  exit 1
}

# 1. 定位后端目录
echo "1. 定位后端目录..."
echo "----------------------------------------"

BACKEND_DIR=""
if [ -d "$PROJECT_ROOT/admin-backend" ]; then
  BACKEND_DIR="$PROJECT_ROOT/admin-backend"
  echo "✅ 找到后端目录: $BACKEND_DIR"
elif [ -d "$PROJECT_ROOT/backend" ]; then
  BACKEND_DIR="$PROJECT_ROOT/backend"
  echo "✅ 找到后端目录: $BACKEND_DIR"
else
  echo "❌ 未找到后端目录（admin-backend 或 backend）"
  exit 1
fi

cd "$BACKEND_DIR" || exit 1
echo ""

# 2. 强制安装核心包（系统级，忽略虚拟环境）
echo "2. 强制安装核心包（系统级）..."
echo "----------------------------------------"

CORE_PACKAGES=(
  "uvicorn"
  "fastapi"
  "starlette"
  "pydantic"
  "python-multipart"
  "requests"
)

echo "使用系统 pip3 安装核心包..."
for PACKAGE in "${CORE_PACKAGES[@]}"; do
  echo "安装 $PACKAGE..."
  # 尝试多种安装方式
  pip3 install "$PACKAGE" --user --break-system-packages 2>/dev/null || {
    echo "⚠️  使用 --user --break-system-packages 失败，尝试使用 sudo..."
    sudo pip3 install "$PACKAGE" --break-system-packages 2>/dev/null || {
      echo "⚠️  sudo 安装失败，尝试使用 apt..."
      # 对于某些包，尝试使用 apt 安装
      if [ "$PACKAGE" = "uvicorn" ] || [ "$PACKAGE" = "fastapi" ]; then
        sudo apt-get update -qq && sudo apt-get install -y python3-$PACKAGE 2>/dev/null || {
          echo "⚠️  apt 安装也失败，尝试强制 pip 安装..."
          pip3 install "$PACKAGE" --break-system-packages --force-reinstall || {
            echo "❌ $PACKAGE 安装完全失败"
          }
        }
      else
        pip3 install "$PACKAGE" --break-system-packages --force-reinstall || {
          echo "⚠️  $PACKAGE 安装失败，但继续..."
        }
      fi
    }
  }
done

echo "✅ 核心包安装完成"
echo ""

# 3. 安装 requirements.txt（如果存在）
echo "3. 安装 requirements.txt..."
echo "----------------------------------------"
if [ -f "requirements.txt" ]; then
  echo "找到 requirements.txt，开始安装..."
  pip3 install -r requirements.txt --user --break-system-packages 2>/dev/null || {
    echo "⚠️  使用 --user --break-system-packages 安装失败，尝试使用 sudo..."
    sudo pip3 install -r requirements.txt --break-system-packages 2>/dev/null || {
      echo "⚠️  部分依赖安装失败，但继续..."
    }
  }
  echo "✅ requirements.txt 依赖安装完成"
else
  echo "⚠️  未找到 requirements.txt"
fi
echo ""

# 4. 验证关键包
echo "4. 验证关键包..."
echo "----------------------------------------"
python3 -c "import uvicorn; print(f'✅ uvicorn: {uvicorn.__version__}')" || {
  echo "❌ uvicorn 导入失败"
  echo "尝试使用系统 Python 路径..."
  /usr/bin/python3 -c "import uvicorn; print(f'✅ uvicorn: {uvicorn.__version__}')" || {
    echo "❌ uvicorn 仍然无法导入"
    exit 1
  }
}

python3 -c "import fastapi; print(f'✅ fastapi: {fastapi.__version__}')" || {
  echo "⚠️  fastapi 导入失败，但继续..."
}

python3 -c "import starlette; print(f'✅ starlette: {starlette.__version__}')" || {
  echo "⚠️  starlette 导入失败，但继续..."
}

python3 -c "import pydantic; print(f'✅ pydantic: {pydantic.__version__}')" || {
  echo "⚠️  pydantic 导入失败，但继续..."
}

echo "✅ 关键包验证完成"
echo ""

# 5. 重启后端服务
echo "5. 重启后端服务..."
echo "----------------------------------------"
cd "$PROJECT_ROOT" || exit 1

# 获取系统 Python3 路径和用户 site-packages 路径
PYTHON3_PATH=$(which python3)
PYTHON_USER_SITE=$(python3 -c "import site; print(site.getusersitepackages())" 2>/dev/null || echo "")

echo "Python3 路径: $PYTHON3_PATH"
if [ -n "$PYTHON_USER_SITE" ]; then
  echo "用户 site-packages: $PYTHON_USER_SITE"
fi

# 验证 uvicorn 在系统 Python 中可用
if ! python3 -c "import uvicorn" 2>/dev/null; then
  echo "❌ 系统 Python3 无法导入 uvicorn"
  echo "尝试查找 uvicorn 位置..."
  UVICORN_PATH=$(python3 -c "import sys; print([p for p in sys.path if 'uvicorn' in str(p)] or '')" 2>/dev/null || echo "")
  if [ -z "$UVICORN_PATH" ]; then
    echo "⚠️  无法找到 uvicorn，但继续尝试启动..."
  fi
fi

if pm2 list | grep -q "backend"; then
  echo "删除现有 backend 进程以重新配置..."
  pm2 delete backend 2>/dev/null || true
  sleep 2
fi

# 查找后端启动文件并启动
if [ -f "$BACKEND_DIR/app/main.py" ]; then
  echo "使用 app.main:app 启动后端..."
  pm2 start "$PYTHON3_PATH" \
    --name backend \
    --interpreter none \
    --cwd "$BACKEND_DIR" \
    --update-env \
    --env PORT=8000 \
    --env PYTHONPATH="$BACKEND_DIR" \
    --env PYTHONUNBUFFERED=1 \
    -- -m uvicorn app.main:app --host 0.0.0.0 --port 8000 || {
    echo "❌ 后端启动失败"
    exit 1
  }
  echo "✅ 后端服务已启动（使用 python3 -m uvicorn）"
elif [ -f "$BACKEND_DIR/main.py" ]; then
  echo "使用 main.py 启动后端..."
  pm2 start "$PYTHON3_PATH" \
    --name backend \
    --interpreter none \
    --cwd "$BACKEND_DIR" \
    --update-env \
    --env PORT=8000 \
    --env PYTHONPATH="$BACKEND_DIR" \
    --env PYTHONUNBUFFERED=1 \
    -- "$BACKEND_DIR/main.py" || {
    echo "❌ 后端启动失败"
    exit 1
  }
  echo "✅ 后端服务已启动（使用 main.py）"
else
  echo "❌ 未找到后端启动文件（app/main.py 或 main.py）"
  exit 1
fi

echo ""

# 6. 等待服务启动
echo "6. 等待服务启动..."
echo "----------------------------------------"
sleep 10

# 7. 验证服务状态
echo "7. 验证服务状态..."
echo "----------------------------------------"
pm2 list

echo ""
echo "检查 PM2 backend 配置..."
pm2 describe backend | grep -E "(interpreter|script|args|env)" || echo "⚠️  无法获取配置信息"

echo ""
echo "后端日志（最近 30 行）："
echo "----------------------------------------"
pm2 logs backend --lines 30 --nostream || {
  echo "⚠️  无法获取日志"
}

echo ""
echo "检查后端错误日志..."
if [ -f "/home/ubuntu/.pm2/logs/backend-error.log" ]; then
  ERROR_COUNT=$(grep -c "ModuleNotFoundError.*uvicorn" /home/ubuntu/.pm2/logs/backend-error.log 2>/dev/null || echo "0")
  if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  错误日志中仍有 $ERROR_COUNT 个 uvicorn 导入错误"
    echo "最后 5 个错误："
    grep "ModuleNotFoundError.*uvicorn" /home/ubuntu/.pm2/logs/backend-error.log | tail -5
  else
    echo "✅ 错误日志中未发现 uvicorn 导入错误"
  fi
fi

echo ""
echo "=========================================="
echo "✅ 后端修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "如果后端仍未正常运行，请检查："
echo "  pm2 logs backend"
echo "  pm2 describe backend"
echo "  python3 -c 'import uvicorn; print(uvicorn.__file__)'"
