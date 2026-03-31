#!/bin/bash
# 键盘训练器 - 快速启动脚本

cd "$(dirname "$0")"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
echo "📥 检查依赖..."
pip install -q -e .

# 启动应用
echo "🚀 启动键盘训练器..."
keyboard-trainer
