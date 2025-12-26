#!/bin/bash
# 诊断部署问题：路径不匹配、Git 配置、GitHub Actions 配置

echo "=========================================="
echo "诊断部署问题"
echo "=========================================="
echo ""

# 1. 检查项目目录
echo "1. 检查项目目录"
echo "----------------------------------------"
EXPECTED_DIR="/home/ubuntu/telegram-ai-system"
ACTUAL_DIR="/opt/web3-sites"

echo "GitHub Actions 期望的路径: $EXPECTED_DIR"
if [ -d "$EXPECTED_DIR" ]; then
    echo "✅ $EXPECTED_DIR 存在"
    echo "   内容:"
    ls -la "$EXPECTED_DIR" | head -10
else
    echo "❌ $EXPECTED_DIR 不存在"
fi

echo ""
echo "服务器实际路径: $ACTUAL_DIR"
if [ -d "$ACTUAL_DIR" ]; then
    echo "✅ $ACTUAL_DIR 存在"
    echo "   内容:"
    ls -la "$ACTUAL_DIR" | head -10
else
    echo "❌ $ACTUAL_DIR 不存在"
fi

# 2. 检查 Git 仓库状态
echo ""
echo "2. 检查 Git 仓库状态"
echo "----------------------------------------"

if [ -d "$ACTUAL_DIR" ]; then
    cd "$ACTUAL_DIR" || exit 1
    echo "检查 $ACTUAL_DIR 的 Git 状态："
    
    if [ -d ".git" ]; then
        echo "✅ .git 目录存在"
        echo ""
        echo "Git 远程仓库："
        git remote -v 2>/dev/null || echo "无法获取远程仓库信息"
        echo ""
        echo "当前分支："
        git branch --show-current 2>/dev/null || echo "无法获取分支信息"
        echo ""
        echo "Git 状态："
        git status --short 2>/dev/null | head -10 || echo "无法获取 Git 状态"
    else
        echo "❌ .git 目录不存在，这不是一个 Git 仓库"
        echo ""
        echo "检查是否有 scripts 目录："
        if [ -d "scripts" ]; then
            echo "✅ scripts 目录存在"
            echo "scripts 目录内容："
            ls -la scripts/ | head -10
        else
            echo "❌ scripts 目录不存在"
        fi
    fi
else
    echo "无法检查，目录不存在"
fi

# 3. 检查 GitHub Actions 工作流配置
echo ""
echo "3. 检查 GitHub Actions 工作流配置"
echo "----------------------------------------"

if [ -d "$ACTUAL_DIR" ] && [ -d "$ACTUAL_DIR/.github/workflows" ]; then
    echo "检查工作流文件："
    ls -la "$ACTUAL_DIR/.github/workflows/" 2>/dev/null || echo "无法列出工作流文件"
    
    echo ""
    echo "检查 deploy-three-sites.yml 中的路径配置："
    if [ -f "$ACTUAL_DIR/.github/workflows/deploy-three-sites.yml" ]; then
        echo "找到 deploy-three-sites.yml，检查 PROJECT_DIR 配置："
        grep -n "PROJECT_DIR" "$ACTUAL_DIR/.github/workflows/deploy-three-sites.yml" || echo "未找到 PROJECT_DIR"
    else
        echo "❌ deploy-three-sites.yml 不存在"
    fi
else
    echo "⚠️  工作流目录不存在或不在 $ACTUAL_DIR"
fi

# 4. 检查诊断脚本是否存在
echo ""
echo "4. 检查诊断脚本是否存在"
echo "----------------------------------------"

if [ -d "$ACTUAL_DIR" ]; then
    DIAG_SCRIPT_PY="$ACTUAL_DIR/scripts/diagnose_aiadmin_redirect.py"
    DIAG_SCRIPT_SH="$ACTUAL_DIR/scripts/diagnose_aiadmin_redirect.sh"
    
    if [ -f "$DIAG_SCRIPT_PY" ]; then
        echo "✅ $DIAG_SCRIPT_PY 存在"
    else
        echo "❌ $DIAG_SCRIPT_PY 不存在"
    fi
    
    if [ -f "$DIAG_SCRIPT_SH" ]; then
        echo "✅ $DIAG_SCRIPT_SH 存在"
    else
        echo "❌ $DIAG_SCRIPT_SH 不存在"
    fi
fi

# 5. 总结问题
echo ""
echo "=========================================="
echo "问题总结"
echo "=========================================="
echo ""
echo "发现的问题："
echo ""
echo "1. 路径不匹配问题："
echo "   - GitHub Actions 工作流使用: $EXPECTED_DIR"
echo "   - 服务器实际路径: $ACTUAL_DIR"
echo "   - 这会导致 GitHub Actions 部署失败"
echo ""
echo "2. 解决方案："
echo "   方案 A: 修改 GitHub Actions 工作流，使用正确的路径 $ACTUAL_DIR"
echo "   方案 B: 将项目移动到 $EXPECTED_DIR（需要迁移数据）"
echo ""
echo "3. 文件同步问题："
if [ -d "$ACTUAL_DIR" ] && [ ! -f "$ACTUAL_DIR/scripts/diagnose_aiadmin_redirect.py" ]; then
    echo "   - 诊断脚本未同步到服务器"
    echo "   - 需要手动复制或通过 Git 拉取"
fi

