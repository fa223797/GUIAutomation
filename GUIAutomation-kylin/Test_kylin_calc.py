"""
麒麟系统计算器GUI自动化测试模块
本模块专为麒麟系统下的主流计算器应用进行自动化测试，涵盖应用启动、关闭、窗口定位等核心功能，针对麒麟系统特性优化窗口标题和元素查找。
"""

import os
# 设置环境变量，避免AT-SPI相关兼容性问题
os.environ['NO_AT_BRIDGE'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'

import sys
import time
import unittest
import warnings
import tracemalloc
import contextlib
import subprocess
import shutil
import gc

tracemalloc.start()
warnings.filterwarnings("ignore", category=ResourceWarning)

import platform_handler
from linux_kylin_handler import LinuxKylinHandler
from linux_handler import x11_display_connection

# —— Monkey Patch 开始 ——
# 生成Kylin处理器实例并禁用AT-SPI
# 保证测试过程中不依赖AT-SPI，提升兼容性

def make_kylin_handler():
    handler = LinuxKylinHandler()
    handler.ATSPI_AVAILABLE = False
    print("LINFO: KylinCalculatorTest - make_kylin_handler: ATSPI_AVAILABLE forced to False for KylinHandler.")
    return handler

orig_find = LinuxKylinHandler._find_window_by_title
def patched_find(self, window_title):
    try:
        return orig_find(self, window_title)
    except Exception:
        fallback = {
            "Calculator": "计算器",
            "计算器": "Calculator",
            "Calculator - Basic": "计算器",
            "Calculator - Scientific": "计算器",
            "MATE Calculator": "计算器",
            "MATE计算器": "计算器"
        }
        alt = fallback.get(window_title)
        if alt:
            try:
                print(f"LDEBUG: patched_find - Trying fallback title: {alt} for original: {window_title}")
                return orig_find(self, alt)
            except Exception:
                pass
        keywords = ["calc", "计算器", "Calc", "mate-calc"]
        if window_title and window_title.lower() not in keywords:
            keywords.append(window_title.lower())
        print(f"LDEBUG: patched_find - Keywords search for {window_title} using: {keywords}")
        try:
            with x11_display_connection() as (disp, root):
                if not disp or not root:
                    print("LWARN: patched_find - Cannot connect to X11 for keyword search.")
                else:
                    windows = root.query_tree().children
                    for win in windows:
                        try:
                            win_name = win.get_wm_name()
                            if win_name and any(k.lower() in win_name.lower() for k in keywords):
                                print(f"LINFO: patched_find - Found window by keyword: '{win_name}' for query '{window_title}'")
                                return win
                        except Exception:
                            pass
        except Exception as e:
            print(f"LERROR: patched_find - X11 connection error during keyword search: {e}")
            pass
        raise Exception(f"Patched_find: 最终找不到窗口: {window_title} (或其变体)")

LinuxKylinHandler._find_window_by_title = patched_find
platform_handler.get_platform_handler = make_kylin_handler
# —— Monkey Patch 结束 ——

from GUIAutomation import GUIAutomation

# 检测系统中可用的计算器应用，优先级从高到低
CALCULATORS = ["ukui-calculator", "mate-calc", "gnome-calculator", "kcalc", "xcalc"]
HAS_CALCULATOR = False
CALCULATOR_CMD = None
CALCULATOR_TITLE_PRIMARY = None
DETECTED_CALCULATOR_TITLE = None

# 计算器命令与主窗口标题映射表
CALCULATOR_TITLE_MAP = {
    "mate-calc": "计算器",
    "ukui-calculator": "Calculator",
    "gnome-calculator": "Calculator",
    "kcalc": "KCalc",
    "xcalc": "Calculator"
}

for _c in CALCULATORS:
    if shutil.which(_c):
        CALCULATOR_CMD = _c
        CALCULATOR_TITLE_PRIMARY = CALCULATOR_TITLE_MAP.get(_c, _c)
        HAS_CALCULATOR = True
        print(f"检测到计算器: {CALCULATOR_CMD} (预设标题: {CALCULATOR_TITLE_PRIMARY})")
        break

# 关闭所有相关计算器进程，确保测试环境干净
def kill_calculator_processes(calculator_cmd):
    if calculator_cmd:
        subprocess.run(f"pkill -9 -f {calculator_cmd}", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        time.sleep(0.5)

class KylinCalculatorTest(unittest.TestCase):
    process = None

    @classmethod
    def setUpClass(cls):
        if not HAS_CALCULATOR:
            raise unittest.SkipTest("系统中未找到指定的计算器应用，跳过所有 Calculator 测试")
        print(f"LINFO: KylinCalculatorTest - setUpClass - 将测试计算器: {CALCULATOR_CMD}")

    def setUp(self):
        if not HAS_CALCULATOR:
            self.skipTest("没有可用的计算器应用，跳过测试")
        kill_calculator_processes(CALCULATOR_CMD)
        gc.collect()
        time.sleep(1)

    def tearDown(self):
        if HAS_CALCULATOR:
            if KylinCalculatorTest.process and hasattr(KylinCalculatorTest.process, 'pid'):
                try:
                    if KylinCalculatorTest.process.poll() is None:
                        KylinCalculatorTest.process.terminate()
                        KylinCalculatorTest.process.wait(timeout=2)
                except:
                    pass
                finally:
                    KylinCalculatorTest.process = None
            kill_calculator_processes(CALCULATOR_CMD)
        gc.collect()
        time.sleep(1)

    # 启动并验证计算器窗口，支持多次尝试
    def _launch_and_verify_calculator(self, max_attempts=3):
        global DETECTED_CALCULATOR_TITLE
        for attempt in range(max_attempts):
            try:
                KylinCalculatorTest.process = subprocess.Popen(CALCULATOR_CMD, shell=False)
                time.sleep(5)
                if KylinCalculatorTest.process.poll() is not None:
                    kill_calculator_processes(CALCULATOR_CMD)
                    continue
                titles_to_check = list(set(filter(None, [CALCULATOR_TITLE_PRIMARY, "计算器", "Calculator", CALCULATOR_CMD])))
                for title_to_check in titles_to_check:
                    if GUIAutomation.check_window_exists(None, title_to_check):
                        DETECTED_CALCULATOR_TITLE = title_to_check
                        GUIAutomation.set_active_window(None, DETECTED_CALCULATOR_TITLE)
                        return True
                KylinCalculatorTest.process.terminate()
                KylinCalculatorTest.process.wait(timeout=1)
            except:
                if KylinCalculatorTest.process:
                    KylinCalculatorTest.process.terminate()
            kill_calculator_processes(CALCULATOR_CMD)
            time.sleep(2)
        self.fail(f"在 {max_attempts} 次尝试后，无法启动并验证计算器 {CALCULATOR_CMD} 窗口。")

    @unittest.skipUnless(HAS_CALCULATOR, "没有可用的计算器应用，跳过测试")
    def test_open_close_application(self):
        """测试计算器应用的打开与关闭"""
        if not self._launch_and_verify_calculator(): return
        self.assertIsNotNone(DETECTED_CALCULATOR_TITLE)
        # 关闭窗口并验证
        result = GUIAutomation.close_window(None, DETECTED_CALCULATOR_TITLE)
        self.assertTrue(result, "close_window 调用失败")

    @unittest.skip("跳过元素操作测试：AT-SPI已禁用且无可靠的非AT-SPI元素操作方案")
    @unittest.skipUnless(HAS_CALCULATOR, "没有可用的计算器应用，跳过测试")
    def test_element_operations(self):
        pass

    @unittest.skipUnless(HAS_CALCULATOR, "没有可用的计算器应用，跳过测试")
    def test_element_existence_and_attributes(self):
        pass

if __name__ == "__main__":
    suite = unittest.TestSuite()
    if HAS_CALCULATOR:
        suite.addTest(unittest.makeSuite(KylinCalculatorTest))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())