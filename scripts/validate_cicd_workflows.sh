#!/bin/bash
# CI/CD 工作流驗證腳本

echo "=========================================="
echo "CI/CD 工作流配置驗證"
echo "=========================================="
echo ""

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKFLOWS_DIR="$PROJECT_ROOT/.github/workflows"

echo "步驟 1: 檢查工作流文件"
echo "----------------------------------------"

# 檢查所有工作流文件
for workflow_file in "$WORKFLOWS_DIR"/*.yml "$WORKFLOWS_DIR"/*.yaml; do
    if [ -f "$workflow_file" ]; then
        filename=$(basename "$workflow_file")
        echo "✅ $filename"
    fi
done

echo ""
echo "步驟 2: 檢查關鍵功能配置"
echo "----------------------------------------"

# 檢查 CI 工作流覆蓋率檢查
if grep -q "--cov-fail-under=70" "$WORKFLOWS_DIR/ci.yml" 2>/dev/null; then
    echo "✅ CI 工作流: 覆蓋率閾值檢查已配置"
else
    echo "❌ CI 工作流: 覆蓋率閾值檢查未配置"
fi

# 檢查綜合檢查
if grep -q "check-all" "$WORKFLOWS_DIR/ci.yml" 2>/dev/null; then
    echo "✅ CI 工作流: 綜合檢查已配置"
else
    echo "❌ CI 工作流: 綜合檢查未配置"
fi

# 檢查測試覆蓋率工作流
if grep -q "--cov-fail-under=70" "$WORKFLOWS_DIR/test-coverage.yml" 2>/dev/null; then
    echo "✅ 測試覆蓋率工作流: 覆蓋率閾值檢查已配置"
else
    echo "❌ 測試覆蓋率工作流: 覆蓋率閾值檢查未配置"
fi

echo ""
echo "步驟 3: 檢查新增工作流"
echo "----------------------------------------"

NEW_WORKFLOWS=("notification.yml" "performance-test.yml" "lint-and-fix.yml")

for workflow in "${NEW_WORKFLOWS[@]}"; do
    if [ -f "$WORKFLOWS_DIR/$workflow" ]; then
        echo "✅ $workflow - 已創建"
    else
        echo "❌ $workflow - 未找到"
    fi
done

echo ""
echo "步驟 4: 驗證工作流語法"
echo "----------------------------------------"

# 檢查 YAML 語法（需要 yamllint 或 python）
if command -v python3 &> /dev/null; then
    for workflow_file in "$WORKFLOWS_DIR"/*.yml "$WORKFLOWS_DIR"/*.yaml; do
        if [ -f "$workflow_file" ]; then
            filename=$(basename "$workflow_file")
            if python3 -c "import yaml; yaml.safe_load(open('$workflow_file'))" 2>/dev/null; then
                echo "✅ $filename - YAML 語法正確"
            else
                echo "❌ $filename - YAML 語法錯誤"
            fi
        fi
    done
else
    echo "⚠️  無法驗證 YAML 語法（需要 Python 3）"
fi

echo ""
echo "=========================================="
echo "驗證完成"
echo "=========================================="
