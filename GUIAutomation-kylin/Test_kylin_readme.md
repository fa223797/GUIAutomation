# GUIAutomation 麒麟系统安装与环境配置指南

## 一键环境搭建

```bash
chmod +x Test_kylin_setup_venv.sh
./Test_kylin_setup_venv.sh
```

如果脚本执行出现 `Permission denied by kysec` 错误，请参考下面的"kysec权限问题解决方案"部分。

## 手动搭建流程（如脚本无法运行）

1. 安装必要系统包：

```bash
sudo apt update
# 分步安装依赖包，避免单个包安装失败影响整体安装
sudo apt install -y python3-pip
sudo apt install -y python3-xlib python3-gi gir1.2-atspi-2.0 
sudo apt install -y xdotool libcairo2-dev pkg-config x11-apps
sudo apt-get install python3-tk python3-dev
sudo apt-get install scrot
# 安装计算器
sudo apt install -y ukui-calculator || sudo apt install -y mate-calc || sudo apt install -y gnome-calculator
# 安装文本编辑器
sudo apt install -y ukui-notebook || sudo apt install -y featherpad || sudo apt install -y gedit || sudo apt install -y pluma
```

2. 安装 Python 依赖：

```bash
sudo pip3 install --upgrade pip wheel setuptools

sudo pip3 install selenium pynput python-xlib pytest bs4 
sudo pip3 install pyperclip
sudo pip3 install pyautogui
```

## 测试文件说明

测试模块已拆分为独立文件，以提高稳定性和可维护性：

### 1. Test_kylin_calc.py
麒麟系统下计算器应用的GUI自动化测试：
- **应用程序操作**：自动检测并启动系统内已安装的计算器（如ukui-calculator、mate-calc等），支持多种主流计算器。
- **窗口查找与适配**：支持中英文窗口标题自动回退，关键字模糊查找，适配不同桌面环境。
- **元素交互**：自动定位并点击计算器按钮，模拟加减乘除等常用操作。
- **元素属性获取**：验证按钮存在性、边界、窗口属性等。
- **资源管理**：测试结束后自动关闭进程，释放系统资源。

### 2. Test_kylin_editor.py
麒麟系统下文本编辑器的GUI自动化测试：
- **多编辑器支持**：自动检测并依次测试ukui-notebook、featherpad、gedit、pluma等多种编辑器。
- **窗口操作**：设置活动窗口、调整窗口大小、最大化/还原等。
- **文本输入与验证**：在文本编辑器中输入中文、英文、特殊字符并校验显示正确。
- **窗口标题适配**：支持中英文窗口名自动切换，提升兼容性。
- **资源管理**：每轮测试后自动关闭编辑器进程，防止资源泄漏。

### 3. Test_kylin_RemainingMethods.py
麒麟系统下窗口操作与信息获取等补充测试用例：
- **窗口移动与置顶**：测试窗口移动、置顶/取消置顶等功能。
- **窗口信息获取**：获取窗口类名、进程ID、可执行路径等。
- **通用窗口应用适配**：支持xterm、xcalc、mate-calc等常见窗口应用。
- **资源清理**：测试后自动关闭相关进程，确保环境整洁。

### 4. 运行测试方法
分别运行各个测试文件以验证对应功能：
```bash
# 测试计算器功能
python3 Test_kylin_calc.py

# 测试文本编辑器功能
python3 Test_kylin_editor.py

# 测试窗口操作与信息获取等补充功能
python3 Test_kylin_RemainingMethods.py
```

## 测试改进与稳定性优化

为解决之前测试中遇到的资源泄漏和崩溃问题，进行了以下优化：

1. **分离测试文件**：
   - `Test_kylin_calc.py`：仅包含计算器相关测试
   - `Test_kylin_editor.py`：仅包含文本编辑器相关测试

2. **资源管理改进**：
   - 使用上下文管理器（`with open_app_context() as app`）确保应用正确关闭
   - 添加垃圾回收（GC）机制释放Xlib资源
   - 更可靠的进程清理，使用多种方法确保测试应用完全终止
   - 禁用AT-SPI以避免相关错误（在麒麟系统上的兼容性更好）

3. **资源跟踪与诊断**：
   - 使用`tracemalloc`跟踪内存分配，便于诊断内存泄漏
   - 测试完成后显示内存使用情况统计
   - 过滤不必要的警告，提高日志可读性

4. **改进后的窗口查找机制**：
   - 动态尝试多种可能的窗口标题
   - 使用关键字匹配找到类似窗口
   - 增强的窗口标题回退机制，支持中英文窗口名

5. **增强可靠性**：
   - 多次尝试启动应用，确保应用程序正确运行
   - 延长等待时间，适应麒麟系统上较慢的窗口加载
   - 备用点击方法，当元素定位失败时尝试坐标点击

6. **文本编辑器多实例测试**：
   - 自动检测所有可用的文本编辑器
   - 在一次运行中依次测试所有编辑器
   - 适配不同编辑器的文本区域元素定位方式

## 麒麟系统适配特点：
1. **自动检测麒麟专用应用**：优先检测ukui-notebook、ukui-calculator等麒麟原生应用
2. **窗口标题本地化处理**：处理中文窗口标题（如"记事本"、"计算器"）
3. **多种编辑器兼容**：支持麒麟系统中常见的多种编辑器（ukui-notebook、pluma、featherpad等）
4. **元素定位适配**：针对不同GUI框架的应用提供不同的元素定位策略

## 最新测试结果

测试在麒麟系统上的运行表现已大幅改进：

1. **计算器测试**：
   - 成功启动多种计算器应用
   - 更可靠的窗口查找，解决了之前的"找不到窗口"错误
   - 能够在启动失败时自动重试

2. **文本编辑器测试**：
   - 成功在多个文本编辑器上执行相同测试
   - 避免了之前的核心转储崩溃
   - 即使某个编辑器测试失败，仍然能继续测试其他编辑器

3. **资源管理**：
   - 大幅减少了ResourceWarning警告
   - 每个测试后完全清理资源
   - 降低了内存占用峰值

## 常见问题解决

1. **资源警告（ResourceWarning）**：测试过程中可能出现资源警告，这通常不影响测试结果
2. **窗口大小调整失败**：某些编辑器可能不支持通过GUI自动化调整窗口大小
3. **窗口状态更改异常**：当遇到"Xlib.X.IconicState属性不存在"错误时，表明系统Xlib版本与代码不兼容
4. **中文输入问题**：如果中文输入测试失败，确保系统已安装中文输入法并正确配置
5. **应用程序路径问题**：如果应用程序启动失败，尝试使用`which 应用名称`命令确认正确路径
6. **Python权限问题**：如遇到kysec权限限制，请参考上方的"kysec权限问题解决方案"

## 麒麟系统特有配置

如果在麒麟系统上测试时遇到权限问题，可能需要以下额外配置：

1. **AT-SPI总线访问权限**：
```bash
gsettings set org.gnome.desktop.interface toolkit-accessibility true
```

2. **窗口管理器兼容性**：
```bash
# 对于UKUI桌面环境
gsettings set org.ukui.window-manager allow-automation true
``` 

3. **Python调用权限**：
```bash
# 允许Python执行
xhost +local:
# 如果使用kysec，添加Python到执行白名单
sudo kysec add -m exec_path -t /usr/bin/python3 -a exec
``` 

## Kylin系统特有问题排查

如果您在运行测试时遇到以下问题，请尝试以下解决方案：

1. **X11连接泄漏问题**

当看到类似以下错误：
```
ResourceWarning: unclosed <socket.socket fd=9, family=AddressFamily.AF_UNIX, type=SocketKind.SOCK_STREAM, proto=0, raddr=/tmp/.X11-unix/X0>
```

解决方法：
- 确保X11环境中无残留进程：`killall -9 ukui-notebook mate-calc gedit pluma featherpad`
- 重启X服务：`sudo systemctl restart lightdm` (可能会导致当前会话关闭)
- 检查X权限：`xhost +local:all`

2. **AT-SPI错误**

当看到类似以下错误：
```
AT-SPI: Error retrieving accessibility bus address: org.freedesktop.DBus.Error.ServiceUnknown
```

解决方法：
- 测试脚本已禁用AT-SPI功能，但服务仍存在于系统中
- 可以完全禁用AT-SPI: `gsettings set org.gnome.desktop.interface toolkit-accessibility false`
- 或导出变量禁用警告: `export NO_AT_BRIDGE=1`

3. **无法找到窗口问题**

如果测试报告"找不到窗口"，可以尝试：
- 手动确认窗口状态: `xwininfo -name 计算器` 或 `xwininfo -name Calculator`
- 使用通配符查找: `xdotool search --name ".*计算.*"` 
- 修改测试脚本中的等待时间，延长为至少5秒
- 确保WM支持X11协议: `gsettings set org.ukui.window-manager allow-x11-operations true`

4. **进程管理问题**

如果应用程序无法正常启动或关闭：
- 手动确认应用是否可启动: `mate-calc &` 或 `ukui-notebook &`
- 检查系统资源限制: `ulimit -a`
- 确保无kysec阻止: `sudo kysec list -a` 并根据需要调整
- 避免同时运行多个测试实例

5. **鼠标点击无反应**

如果测试无法正确点击元素：
- 确保显示服务器允许输入: `xhost +local:all`
- 尝试使用备用方法: `python3 Test_kylin_calc.py --use-xdotool`
- 在运行前清理环境: `killall -9 python3`

请在每次测试前确保系统处于干净状态，并在测试后清理残留进程。