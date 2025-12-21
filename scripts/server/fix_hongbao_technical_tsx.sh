#!/bin/bash

# 修复红包项目 Technical.tsx JSX 语法错误脚本
# 使用方法: bash scripts/server/fix_hongbao_technical_tsx.sh

set -e

echo "=========================================="
echo "🔧 修复红包项目 Technical.tsx 构建错误"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || {
  echo "❌ 无法进入项目目录: $PROJECT_ROOT"
  exit 1
}

# 1. 定位红包项目目录
echo "1. 定位红包项目目录..."
echo "----------------------------------------"

HONGBAO_DIR="$PROJECT_ROOT/react-vite-template/hbwy20251220"

if [ ! -d "$HONGBAO_DIR" ]; then
  echo "❌ 未找到红包项目目录: $HONGBAO_DIR"
  exit 1
fi

if [ ! -f "$HONGBAO_DIR/package.json" ]; then
  echo "❌ 未找到 package.json: $HONGBAO_DIR/package.json"
  exit 1
fi

echo "✅ 找到红包项目目录: $HONGBAO_DIR"
cd "$HONGBAO_DIR" || exit 1
echo ""

# 2. 读取并修复 Technical.tsx
echo "2. 读取并修复 Technical.tsx..."
echo "----------------------------------------"

TECHNICAL_FILE="$HONGBAO_DIR/components/Technical.tsx"

if [ ! -f "$TECHNICAL_FILE" ]; then
  echo "❌ 未找到文件: $TECHNICAL_FILE"
  exit 1
fi

echo "找到文件: $TECHNICAL_FILE"

# 备份原文件
cp "$TECHNICAL_FILE" "$TECHNICAL_FILE.bak"
echo "✅ 已备份原文件: $TECHNICAL_FILE.bak"

# 读取文件内容
FILE_CONTENT=$(cat "$TECHNICAL_FILE")

# 检查第 72 行附近的内容
echo ""
echo "检查第 72 行附近的内容..."
LINE_72=$(sed -n '72p' "$TECHNICAL_FILE")
echo "第 72 行: $LINE_72"

# 修复 JSX 语法错误
# 问题：第 72 行第 93 个字符有无效的 > 符号
# 需要将字符串中的 > 替换为 &gt; 或者用 JSX 表达式包裹

echo ""
echo "修复 JSX 语法错误..."

# 方法 1: 将字符串中的 > 替换为 &gt;
sed -i 's/remainingAmount > 0/remainingAmount \&gt; 0/g' "$TECHNICAL_FILE"

# 方法 2: 修复其他可能的 > 符号问题（在 JSX 表达式中）
sed -i "s/{'>'}/{'\&gt;'}/g" "$TECHNICAL_FILE"

# 方法 3: 检查是否有其他未转义的 > 符号在 JSX 元素中
# 使用 Python 脚本进行更精确的修复
python3 << 'PYTHON_SCRIPT'
import re
import sys

file_path = sys.argv[1]

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复第 72 行的问题：在 JSX 字符串中的 > 需要转义
# 查找类似 require(<span className="text-yellow-400">{'remainingAmount > 0'}</span> 的模式
# 将 > 替换为 &gt;

# 修复模式1: {'remainingAmount > 0'} -> {'remainingAmount &gt; 0'}
content = re.sub(
    r"(\{'remainingAmount\s+)>(\s+0'\})",
    r"\1&gt;\2",
    content
)

# 修复模式2: 在 JSX 属性值中的 > 符号
# 查找 className="text-yellow-400">{'...>...'} 的模式
content = re.sub(
    r"(className=\"text-yellow-400\">\{'[^']*)\s+>\s+([^']*'\})",
    r"\1 &gt; \2",
    content
)

# 修复模式3: 确保所有在 JSX 表达式中的 > 都被正确处理
# 查找 {'...>...'} 模式，将 > 替换为 &gt;
def fix_gt_in_jsx_expr(match):
    expr = match.group(1)
    # 如果包含 > 且不在引号中，替换为 &gt;
    if '>' in expr and not ('"' in expr or "'" in expr):
        expr = expr.replace('>', '&gt;')
    return "{'" + expr + "'}"

# 更精确的修复：只修复在 JSX 元素属性中的问题
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if i == 72:  # 重点修复第 72 行
        # 查找 require(<span className="...">{'...>...'}</span> 模式
        if 'require(' in line and '>' in line and 'text-yellow-400' in line:
            # 将 {'remainingAmount > 0'} 替换为 {'remainingAmount &gt; 0'}
            lines[i-1] = re.sub(
                r"(\{'remainingAmount\s+)>(\s+0'\})",
                r"\1&gt;\2",
                line
            )

content = '\n'.join(lines)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ JSX 语法错误已修复")
PYTHON_SCRIPT
"$TECHNICAL_FILE"

echo "✅ Technical.tsx 已修复"
echo ""

# 显示修复后的第 72 行
echo "修复后的第 72 行:"
sed -n '72p' "$TECHNICAL_FILE"
echo ""

# 3. 清理旧的构建
echo "3. 清理旧的构建..."
echo "----------------------------------------"
rm -rf dist build .next node_modules/.vite 2>/dev/null || true
echo "✅ 清理完成"
echo ""

# 4. 重新构建
echo "4. 重新构建项目..."
echo "----------------------------------------"
npm run build || {
  echo "❌ 构建失败"
  echo ""
  echo "构建错误详情："
  npm run build 2>&1 | tail -50
  echo ""
  echo "如果构建仍然失败，请检查 Technical.tsx 文件："
  echo "  cat $TECHNICAL_FILE | grep -n '>'"
  exit 1
}

echo "✅ 构建完成"
echo ""

# 5. 重启服务
echo "5. 重启 hongbao-frontend 服务..."
echo "----------------------------------------"
cd "$PROJECT_ROOT" || exit 1

if pm2 list | grep -q "hongbao-frontend"; then
  pm2 restart hongbao-frontend || {
    echo "⚠️  PM2 restart 失败，尝试删除后重新启动..."
    pm2 delete hongbao-frontend 2>/dev/null || true
    sleep 2
    
    # 确定构建输出目录
    BUILD_DIR=""
    if [ -d "$HONGBAO_DIR/dist" ]; then
      BUILD_DIR="dist"
    elif [ -d "$HONGBAO_DIR/build" ]; then
      BUILD_DIR="build"
    fi
    
    if [ -n "$BUILD_DIR" ]; then
      pm2 start serve \
        --name hongbao-frontend \
        -- -s "$HONGBAO_DIR/$BUILD_DIR" -l 3002 || {
        echo "❌ 服务启动失败"
        exit 1
      }
      echo "✅ hongbao-frontend 已重新启动"
    else
      echo "❌ 未找到构建输出目录"
      exit 1
    fi
  }
  echo "✅ hongbao-frontend 已重启"
else
  echo "⚠️  PM2 中未找到 hongbao-frontend 进程，尝试启动..."
  
  BUILD_DIR=""
  if [ -d "$HONGBAO_DIR/dist" ]; then
    BUILD_DIR="dist"
  elif [ -d "$HONGBAO_DIR/build" ]; then
    BUILD_DIR="build"
  fi
  
  if [ -n "$BUILD_DIR" ]; then
    pm2 start serve \
      --name hongbao-frontend \
      -- -s "$HONGBAO_DIR/$BUILD_DIR" -l 3002 || {
      echo "❌ 服务启动失败"
      exit 1
    }
    echo "✅ hongbao-frontend 已启动"
  else
    echo "❌ 未找到构建输出目录"
    exit 1
  fi
fi

echo ""

# 6. 等待服务启动
echo "6. 等待服务启动..."
echo "----------------------------------------"
sleep 5

# 7. 验证服务状态
echo "7. 验证服务状态..."
echo "----------------------------------------"
pm2 list | grep hongbao-frontend || echo "⚠️  未找到 hongbao-frontend 进程"

echo ""
echo "服务日志（最近 20 行）："
echo "----------------------------------------"
pm2 logs hongbao-frontend --lines 20 --nostream || {
  echo "⚠️  无法获取日志"
}

echo ""
echo "测试端口 3002..."
echo "----------------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3002 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
  echo "✅ 端口 3002 HTTP 响应正常 (HTTP $HTTP_CODE)"
else
  echo "⚠️  端口 3002 HTTP 响应异常 (HTTP $HTTP_CODE)"
fi

echo ""
echo "=========================================="
echo "✅ 红包项目修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "如果仍有问题，请检查："
echo "  pm2 logs hongbao-frontend"
echo "  pm2 describe hongbao-frontend"
echo "  cat $TECHNICAL_FILE | head -80 | tail -15"
