@echo off
chcp 65001 >nul
echo ========================================
echo 開始運行 E2E 測試
echo ========================================
echo.

cd /d "%~dp0"

echo 當前目錄: %CD%
echo.

echo 檢查 Playwright...
call npx playwright --version
echo.

echo 列出所有測試文件:
dir /b e2e\*.spec.ts
echo.

echo 開始運行測試...
echo 注意：這可能需要幾分鐘時間
echo.

call npx playwright test --reporter=list,html > test-results.txt 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✓ 所有測試通過！
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ✗ 部分測試失敗
    echo ========================================
)

echo.
echo 測試結果已保存到: test-results.txt
echo 查看 HTML 報告: npx playwright show-report
echo.

type test-results.txt

pause
