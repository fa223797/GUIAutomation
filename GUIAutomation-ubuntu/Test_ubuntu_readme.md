# GUIAutomation Ubuntu 安装与环境配置指南

## 一键环境搭建

```bash
chmod +x Test_ubuntu_setup_venv.sh
./setup_venv.sh
```

## 手动搭建流程（如脚本无法正确运行）

1. 安装必要系统包：

```bash
sudo apt update
sudo apt install -y python3-full python3-pip python3-venv python3-xlib python3-gi gir1.2-atspi-2.0 xdotool libcairo2-dev pkg-config
sudo apt install -y xcalc x11-apps
# 安装至少一种文本编辑器（按优先级排序）
sudo apt install -y xedit mousepad leafpad gedit pluma kate
```

2. 创建并激活虚拟环境：

```bash
python3 -m venv venv
source venv/bin/activate
```

3. 安装 Python 依赖：

```bash
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt

# 如果Xlib相关操作报错，请在终端执行：
xhost +local:
```

## 测试说明

### Test_ubuntu_GUI.py
测试了以下GUI自动化功能：
1. **应用程序操作**：打开和关闭应用程序（xcalc计算器）
2. **窗口操作**：设置活动窗口、调整窗口大小、窗口状态更改（最大化、最小化、还原）
3. **元素操作**：对计算器的按钮进行点击操作，模拟计算过程
4. **文本输入**：在文本编辑器中输入文本并验证
5. **元素属性**：获取和验证GUI元素的存在性、边界和属性

### Test_ubuntu_text.py
针对文本编辑器进行的专项测试：
1. **动态适配编辑器**：自动检测系统中可用的文本编辑器（xedit、pluma、kate、leafpad、mousepad、gedit）
2. **窗口操作**：获取窗口大小、调整窗口大小、最大化和还原窗口
3. **文本输入**：使用不同的定位策略查找文本区域，输入和验证文本内容

## 常见问题解决

1. **资源警告（ResourceWarning）**：测试过程中可能出现资源警告，这通常不影响测试结果
2. **窗口大小调整失败**：某些编辑器（如xedit）可能不支持通过GUI自动化调整窗口大小
3. **窗口状态更改异常**：当遇到"Xlib.X.IconicState属性不存在"错误时，表明系统Xlib版本与代码不兼容

