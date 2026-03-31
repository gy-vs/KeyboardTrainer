@echo off
chcp 65001 >nul
title 键盘训练器

cd /d "%~dp0"

if not exist ".venv" (
    echo 📦 创建虚拟环境...
    python -m venv .venv
)

echo 📥 激活虚拟环境...
call .venv\Scripts\activate.bat

echo 📥 检查依赖...
pip install -q -e .

echo 🚀 启动键盘训练器...
keyboard-trainer

pause
