@echo off
chcp 65001 >nul
cd /d "e:\002-工作文件\重要程序\聊天AI群聊程序"

echo ====================================
echo Git Deployment Script
echo ====================================
echo.

echo [1/4] Checking git status...
git status > deploy_log.txt 2>&1
type deploy_log.txt
echo.

echo [2/4] Adding all files...
git add -A >> deploy_log.txt 2>&1
echo Done.
echo.

echo [3/4] Creating commit...
git commit -m "feat: Add advanced chat features - TTS, image gen, cross-group, alerts, templates, user lists, multi-lang, webhooks, private funnel" >> deploy_log.txt 2>&1
echo Done.
echo.

echo [4/4] Pushing to GitHub...
git push origin master >> deploy_log.txt 2>&1
echo Done.
echo.

echo ====================================
echo Deployment Complete!
echo ====================================
echo.
echo Check deploy_log.txt for details.
echo.

type deploy_log.txt
pause
