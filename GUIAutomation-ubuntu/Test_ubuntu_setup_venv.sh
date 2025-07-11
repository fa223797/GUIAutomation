#!/bin/bash

# GUIAutomation 虚拟环境自动设置脚本
echo "=== 开始设置GUIAutomation虚拟环境 ==="

# 检查Python版本
if ! python3 -c 'import sys; exit(1) if sys.version_info < (3,7) else exit(0)'; then
    echo "错误：需要Python 3.7或更高版本"
    exit 1
fi

# 创建本地虚拟环境
echo "正在项目目录创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "正在激活虚拟环境..."
source venv/bin/activate

# 安装系统依赖
echo "正在安装系统依赖..."
sudo apt update && sudo apt install -y \
    python3-xlib python3-gi gir1.2-atspi-2.0 \
    xdotool libcairo2-dev pkg-config \
    xcalc x11-apps

# 安装至少一种文本编辑器（按优先级排序）
echo "正在安装文本编辑器..."
sudo apt install -y xedit mousepad leafpad gedit pluma kate

# 安装Python依赖
echo "正在安装Python依赖..."
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt

# 允许本地X11连接，解决Xlib权限问题
echo "配置X11权限..."
xhost +local:

echo "=== 设置完成 ==="
echo "激活虚拟环境命令：source venv/bin/activate"
echo "若测试过程中出现Xlib权限问题，请执行：xhost +local:"
echo "在VSCode中，选择 venv/bin/python 作为解释器即可"