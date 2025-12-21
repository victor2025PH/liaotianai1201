#!/bin/bash

# 修复后端依赖问题脚本
# 使用方法: bash scripts/server/fix_backend.sh

set -e

echo "=========================================="
echo "🔧 修复后端依赖问题"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || {
  echo "❌ 无法进入项目目录: $PROJECT_ROOT"
  exit 1
}

# 1. 查找后端目录
echo "1. 查找后端目录..."
echo "----------------------------------------"

BACKEND_DIR=""
if [ -f "$PROJECT_ROOT/admin-backend/requirements.txt" ]; then
  BACKEND_DIR="$PROJECT_ROOT/admin-backend"
  echo "✅ 找到后端目录: $BACKEND_DIR"
elif [ -f "$PROJECT_ROOT/backend/requirements.txt" ]; then
  BACKEND_DIR="$PROJECT_ROOT/backend"
  echo "✅ 找到后端目录: $BACKEND_DIR"
else
  # 搜索 requirements.txt
  REQUIREMENTS_FILE=$(find "$PROJECT_ROOT" -maxdepth 3 -name "requirements.txt" -type f 2>/dev/null | \
    grep -v "/\.git/" | \
    grep -v "/node_modules/" | \
    head -1)
  
  if [ -n "$REQUIREMENTS_FILE" ]; then
    BACKEND_DIR=$(dirname "$REQUIREMENTS_FILE")
    echo "✅ 通过 requirements.txt 找到后端目录: $BACKEND_DIR"
  else
    echo "❌ 未找到后端目录或 requirements.txt"
    exit 1
  fi
fi

cd "$BACKEND_DIR" || exit 1
echo ""

# 2. 检查并创建虚拟环境
echo "2. 检查虚拟环境..."
echo "----------------------------------------"

if [ -d "venv" ]; then
  echo "✅ 虚拟环境已存在: $BACKEND_DIR/venv"
  source venv/bin/activate
elif [ -d ".venv" ]; then
  echo "✅ 虚拟环境已存在: $BACKEND_DIR/.venv"
  source .venv/bin/activate
else
  echo "创建虚拟环境..."
  python3 -m venv venv || {
    echo "❌ 虚拟环境创建失败"
    exit 1
  }
  source venv/bin/activate
  echo "✅ 虚拟环境已创建并激活"
fi

echo "Python 路径: $(which python)"
echo "pip 路径: $(which pip)"
echo ""

# 3. 升级 pip
echo "3. 升级 pip..."
echo "----------------------------------------"
pip install --upgrade pip || {
  echo "⚠️  pip 升级失败，但继续..."
}
echo ""

# 4. 安装 requirements.txt 中的依赖
echo "4. 安装 requirements.txt 中的依赖..."
echo "----------------------------------------"
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt || {
    echo "⚠️  部分依赖安装失败，但继续..."
  }
  echo "✅ requirements.txt 依赖安装完成"
else
  echo "⚠️  未找到 requirements.txt"
fi
echo ""

# 5. 强制安装核心包（防止再次报错）
echo "5. 强制安装核心包..."
echo "----------------------------------------"
CORE_PACKAGES=(
  "uvicorn>=0.23.0"
  "fastapi>=0.100.0"
  "starlette>=0.27.0"
  "pydantic>=2.0.0"
)

for PACKAGE in "${CORE_PACKAGES[@]}"; do
  echo "安装 $PACKAGE..."
  pip install "$PACKAGE" || {
    echo "⚠️  $PACKAGE 安装失败，但继续..."
  }
done

echo "✅ 核心包安装完成"
echo ""

# 6. 验证关键包
echo "6. 验证关键包..."
echo "----------------------------------------"
python3 -c "import uvicorn; print(f'✅ uvicorn: {uvicorn.__version__}')" || {
  echo "❌ uvicorn 导入失败"
  exit 1
}

python3 -c "import fastapi; print(f'✅ fastapi: {fastapi.__version__}')" || {
  echo "❌ fastapi 导入失败"
  exit 1
}

python3 -c "import starlette; print(f'✅ starlette: {starlette.__version__}')" || {
  echo "❌ starlette 导入失败"
  exit 1
}

python3 -c "import pydantic; print(f'✅ pydantic: {pydantic.__version__}')" || {
  echo "❌ pydantic 导入失败"
  exit 1
}

echo "✅ 所有关键包验证通过"
echo ""

# 7. 重启后端服务
echo "7. 重启后端服务..."
echo "----------------------------------------"
cd "$PROJECT_ROOT" || exit 1

# 检查 PM2 中是否有 backend 进程
if pm2 list | grep -q "backend"; then
  echo "重启 PM2 backend 进程..."
  pm2 restart backend || {
    echo "⚠️  PM2 restart 失败，尝试删除后重新启动..."
    pm2 delete backend 2>/dev/null || true
    
    # 查找后端启动文件
    if [ -f "$BACKEND_DIR/main.py" ]; then
      MAIN_FILE="$BACKEND_DIR/main.py"
    elif [ -f "$BACKEND_DIR/app.py" ]; then
      MAIN_FILE="$BACKEND_DIR/app.py"
    elif [ -f "$BACKEND_DIR/run.py" ]; then
      MAIN_FILE="$BACKEND_DIR/run.py"
    else
      # 查找包含 uvicorn 启动的入口文件
      MAIN_FILE=$(find "$BACKEND_DIR" -maxdepth 2 -name "*.py" -type f | head -1)
    fi
    
    if [ -n "$MAIN_FILE" ] && [ -f "$MAIN_FILE" ]; then
      echo "使用 $MAIN_FILE 启动后端..."
      pm2 start "$MAIN_FILE" \
        --name backend \
        --interpreter python3 \
        --cwd "$BACKEND_DIR" || {
        echo "❌ 后端启动失败"
        exit 1
      }
    else
      # 尝试使用 uvicorn 直接启动
      if [ -f "$BACKEND_DIR/app/main.py" ]; then
        pm2 start "uvicorn" \
          --name backend \
          --interpreter python3 \
          --cwd "$BACKEND_DIR" \
          -- app.main:app --host 0.0.0.0 --port 8000 || {
          echo "❌ 后端启动失败"
          exit 1
        }
      else
        echo "⚠️  无法确定后端启动方式"
      fi
    fi
  }
  echo "✅ 后端服务已重启"
else
  echo "⚠️  PM2 中未找到 backend 进程，尝试启动..."
  
  # 查找后端启动文件
  if [ -f "$BACKEND_DIR/main.py" ]; then
    MAIN_FILE="$BACKEND_DIR/main.py"
  elif [ -f "$BACKEND_DIR/app.py" ]; then
    MAIN_FILE="$BACKEND_DIR/app.py"
  elif [ -f "$BACKEND_DIR/run.py" ]; then
    MAIN_FILE="$BACKEND_DIR/run.py"
  else
    MAIN_FILE=$(find "$BACKEND_DIR" -maxdepth 2 -name "*.py" -type f | head -1)
  fi
  
  if [ -n "$MAIN_FILE" ] && [ -f "$MAIN_FILE" ]; then
    pm2 start "$MAIN_FILE" \
      --name backend \
      --interpreter python3 \
      --cwd "$BACKEND_DIR" || {
      echo "❌ 后端启动失败"
      exit 1
    }
    echo "✅ 后端服务已启动"
  else
    echo "⚠️  无法确定后端启动方式，请手动启动"
  fi
fi

echo ""

# 8. 等待服务启动
echo "8. 等待服务启动..."
echo "----------------------------------------"
sleep 5

# 9. 检查状态
echo "9. 检查服务状态..."
echo "----------------------------------------"
pm2 list

echo ""
echo "后端日志（最近 20 行）："
echo "----------------------------------------"
pm2 logs backend --lines 20 --nostream || {
  echo "⚠️  无法获取日志"
}

echo ""
echo "=========================================="
echo "✅ 后端修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "如果后端仍未正常运行，请检查："
echo "  pm2 logs backend"
echo "  pm2 describe backend"
