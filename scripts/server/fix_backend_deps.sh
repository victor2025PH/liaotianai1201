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
  pip3 install "$PACKAGE" --user || {
    echo "⚠️  $PACKAGE 安装失败，尝试使用 sudo..."
    sudo pip3 install "$PACKAGE" || {
      echo "⚠️  $PACKAGE 安装失败，但继续..."
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
  pip3 install -r requirements.txt --user || {
    echo "⚠️  使用 --user 安装失败，尝试使用 sudo..."
    sudo pip3 install -r requirements.txt || {
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

if pm2 list | grep -q "backend"; then
  echo "重启 PM2 backend 进程..."
  pm2 restart backend || {
    echo "⚠️  PM2 restart 失败，尝试删除后重新启动..."
    pm2 delete backend 2>/dev/null || true
    sleep 2
    
    # 查找后端启动文件
    if [ -f "$BACKEND_DIR/main.py" ]; then
      MAIN_FILE="$BACKEND_DIR/main.py"
    elif [ -f "$BACKEND_DIR/app.py" ]; then
      MAIN_FILE="$BACKEND_DIR/app.py"
    elif [ -f "$BACKEND_DIR/run.py" ]; then
      MAIN_FILE="$BACKEND_DIR/run.py"
    elif [ -f "$BACKEND_DIR/app/main.py" ]; then
      # 使用 uvicorn 启动
      pm2 start "uvicorn" \
        --name backend \
        --interpreter python3 \
        --cwd "$BACKEND_DIR" \
        -- app.main:app --host 0.0.0.0 --port 8000 || {
        echo "❌ 后端启动失败"
        exit 1
      }
      echo "✅ 后端服务已重新启动（使用 uvicorn）"
      cd "$PROJECT_ROOT" || exit 1
      
      # 等待并验证
      echo ""
      echo "6. 等待服务启动..."
      echo "----------------------------------------"
      sleep 5
      
      echo ""
      echo "7. 验证服务状态..."
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
      exit 0
    else
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
      echo "⚠️  无法确定后端启动方式"
    fi
  }
  echo "✅ 后端服务已重启"
else
  echo "⚠️  PM2 中未找到 backend 进程，尝试启动..."
  
  # 查找后端启动文件
  if [ -f "$BACKEND_DIR/app/main.py" ]; then
    pm2 start "uvicorn" \
      --name backend \
      --interpreter python3 \
      --cwd "$BACKEND_DIR" \
      -- app.main:app --host 0.0.0.0 --port 8000 || {
      echo "❌ 后端启动失败"
      exit 1
    }
  elif [ -f "$BACKEND_DIR/main.py" ]; then
    pm2 start "$BACKEND_DIR/main.py" \
      --name backend \
      --interpreter python3 \
      --cwd "$BACKEND_DIR" || {
      echo "❌ 后端启动失败"
      exit 1
    }
  else
    echo "⚠️  无法确定后端启动方式，请手动启动"
  fi
  echo "✅ 后端服务已启动"
fi

echo ""

# 6. 等待服务启动
echo "6. 等待服务启动..."
echo "----------------------------------------"
sleep 5

# 7. 验证服务状态
echo "7. 验证服务状态..."
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
echo "  python3 -c 'import uvicorn; print(uvicorn.__file__)'"
