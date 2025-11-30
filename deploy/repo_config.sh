#!/bin/bash
# 倉庫配置 - 所有部署腳本使用此配置
# 更新日期: 2025-11-30

# GitHub 倉庫配置
export GITHUB_REPO_URL="https://github.com/victor2025PH/liaotianai1201.git"
export GITHUB_REPO_NAME="liaotianai1201"
export GITHUB_OWNER="victor2025PH"

# 分支配置
export DEFAULT_BRANCH="main"
export FALLBACK_BRANCHES="main master develop"

# 服務器部署路徑
export SERVER_DEPLOY_PATH="~/liaotian"

# 克隆命令（用於新倉庫初始化）
export GIT_CLONE_CMD="git clone ${GITHUB_REPO_URL} ."
