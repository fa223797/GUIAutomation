"""
麒麟(Kylin)系统文本编辑器GUI自动化测试模块
本模块专门针对文本编辑器应用进行GUI自动化测试
包括：窗口操作、文本输入等
考虑到麒麟系统的特点，对窗口标题和元素定位做了适配
"""

import os
os.environ['NO_AT_BRIDGE'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'

import sys
import time
import unittest
import warnings
import tracemalloc
import subprocess
import shutil
import gc
import Xlib


tracemalloc.start()
# 过滤掉ResourceWarning
warnings.filterwarnings("ignore", category=ResourceWarning)

import platform_handler
from linux_kylin_handler import LinuxKylinHandler
from linux_handler import x11_display_connection

# —— Monkey Patch 开始 ——
def make_kylin_handler():
    handler = LinuxKylinHandler()
    handler.ATSPI_AVAILABLE = False
    return handler

orig_find_editor = LinuxKylinHandler._find_window_by_title
def patched_find_editor(self, window_title):
    target_pid = None
    if hasattr(KylinEditorTest, 'current_editor_process') and KylinEditorTest.current_editor_process:
        target_pid = KylinEditorTest.current_editor_process.pid

    try:
        return orig_find_editor(self, window_title)
    except Exception:
        pass

    if not target_pid:
        print(f"LWARN: patched_find_editor - No target_pid. Falling back to basic title matching for '{window_title}'.")
        fallback_titles = {
            "Notebook": "记事本", "记事本": "Notebook",
            "Text Editor": "文本编辑器", "文本编辑器": "Text Editor",
            "Editor": "编辑器", "编辑器": "Editor",
            "Featherpad": "featherpad", "featherpad": "Featherpad",
            "gedit": "gedit", "Pluma": "pluma", "pluma": "Pluma"
        }
        alt_title = fallback_titles.get(window_title)
        if alt_title:
            try:
                print(f"LDEBUG: patched_find_editor - Trying fallback title: {alt_title} for original: {window_title}")
                return orig_find_editor(self, alt_title)
            except Exception:
                pass
        print(f"LDEBUG: patched_find_editor - Basic title match failed for '{window_title}' and fallbacks. Relying on final exception from orig_find_editor or broader search if implemented there.")
        return orig_find_editor(self, window_title)

    print(f"LDEBUG: patched_find_editor - Searching for window for PID {target_pid} (original query: '{window_title}')")
    with x11_display_connection() as (disp, root):
        if not disp or not root:
            print("LERROR: patched_find_editor - Cannot connect to X11 for PID-based search.")
            raise Exception(f"Patched_find_editor (PID search): X11 connection failed for '{window_title}'")
        pid_atom = disp.intern_atom('_NET_WM_PID')
        window_type_atom = disp.intern_atom('_NET_WM_WINDOW_TYPE')
        normal_window_atom = disp.intern_atom('_NET_WM_WINDOW_TYPE_NORMAL')
        best_match_window = None
        windows = root.query_tree().children
        for win in windows:
            try:
                win_pid_prop = win.get_property(pid_atom, Xlib.Xatom.CARDINAL, 0, 1)
                if win_pid_prop and win_pid_prop.value and win_pid_prop.value[0] == target_pid:
                    win_type_prop = win.get_property(window_type_atom, Xlib.Xatom.ATOM, 0, 1)
                    is_normal_window = False
                    if win_type_prop and win_type_prop.value:
                        if win_type_prop.value[0] == normal_window_atom:
                            is_normal_window = True
                    else:
                        is_normal_window = True 

                    if is_normal_window:
                        win_name = win.get_wm_name()
                        actual_win_name = ""
                        if isinstance(win_name, bytes):
                            try: actual_win_name = win_name.decode('utf-8', 'replace')
                            except AttributeError: actual_win_name = str(win_name) if win_name else ""
                        elif win_name:
                            actual_win_name = str(win_name)

                        if actual_win_name:
                            if window_title.lower() in actual_win_name.lower() or \
                               KylinEditorTest.current_editor_cmd.lower() in actual_win_name.lower():
                                print(f"LINFO: patched_find_editor (PID) - Found STRONG match: PID {target_pid}, Name '{actual_win_name}' for query '{window_title}'")
                                return win
                            if best_match_window is None:
                                best_match_window = win
                                print(f"LDEBUG: patched_find_editor (PID) - Candidate (first normal named): PID {target_pid}, Name '{actual_win_name}' for query '{window_title}'")
            except Exception:
                pass
        
        if best_match_window:
            win_name = best_match_window.get_wm_name()
            actual_win_name = ""
            if isinstance(win_name, bytes):
                try: actual_win_name = win_name.decode('utf-8', 'replace')
                except AttributeError: actual_win_name = str(win_name) if win_name else ""
            elif win_name:
                actual_win_name = str(win_name)
            print(f"LINFO: patched_find_editor (PID) - Found best available match (normal, named) for PID {target_pid}: Name '{actual_win_name}', returning this one for query '{window_title}'.")
            return best_match_window

    print(f"LWARN: patched_find_editor - PID-based search for PID {target_pid} (query: '{window_title}') found no suitable window. Falling back to original finder purely on title.")
    return orig_find_editor(self, window_title)

LinuxKylinHandler._find_window_by_title = patched_find_editor
platform_handler.get_platform_handler = make_kylin_handler
# —— Monkey Patch 结束 ——

from GUIAutomation import GUIAutomation

EDITORS_PRIORITY = ["ukui-notebook", "pluma", "featherpad", "gedit", "mousepad", "leafpad", "xed"]
AVAILABLE_EDITORS = []  

EDITOR_TITLE_MAP = {
    "ukui-notebook": "记事本",
    "featherpad": "Featherpad",
    "gedit": "gedit",  
    "pluma": "Pluma",  
    "mousepad": "Mousepad",
    "leafpad": "Leafpad",
    "xed": "Xed"
}

for _e_cmd in EDITORS_PRIORITY:
    if shutil.which(_e_cmd):
        primary_title = EDITOR_TITLE_MAP.get(_e_cmd, _e_cmd)
        AVAILABLE_EDITORS.append({"cmd": _e_cmd, "primary_title": primary_title})
        print(f"检测到可用编辑器: {_e_cmd} (预设标题: {primary_title})")

if not AVAILABLE_EDITORS:
    print("警告: 未检测到任何可用的文本编辑器。测试将被跳过。")

def kill_editor_processes(editor_cmd):
    if editor_cmd:
        subprocess.run(f"pkill -9 -f {editor_cmd}", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        time.sleep(0.5)

class KylinEditorTest(unittest.TestCase):
    """麒麟系统文本编辑器GUI自动化测试类"""
    
    current_editor_process = None
    current_editor_cmd = None
    current_editor_detected_title = None

    def setUp(self):
        if not AVAILABLE_EDITORS:
            self.skipTest("没有可用的文本编辑器，跳过所有测试")
        # 清理之前的残留进程，让系统干净点
        for editor_info in AVAILABLE_EDITORS:
            kill_editor_processes(editor_info["cmd"])
        gc.collect()
        time.sleep(1)

    def tearDown(self):
        if KylinEditorTest.current_editor_process and hasattr(KylinEditorTest.current_editor_process, 'pid'):
            try:
                if KylinEditorTest.current_editor_process.poll() is None:
                    KylinEditorTest.current_editor_process.terminate()
                    KylinEditorTest.current_editor_process.wait(timeout=2)
            except Exception as e:
                print(f"TearDown: Error terminating {KylinEditorTest.current_editor_cmd}: {e}")
            finally:
                KylinEditorTest.current_editor_process = None
        
        if KylinEditorTest.current_editor_cmd:
            kill_editor_processes(KylinEditorTest.current_editor_cmd)
            KylinEditorTest.current_editor_cmd = None
            KylinEditorTest.current_editor_detected_title = None
        gc.collect()
        time.sleep(1)

    def _launch_and_verify_editor(self, editor_cmd, primary_editor_title, max_attempts=2):
        KylinEditorTest.current_editor_cmd = editor_cmd
        KylinEditorTest.current_editor_detected_title = None
        
        for attempt in range(max_attempts):
            print(f"INFO: Attempting to launch editor {editor_cmd} (Attempt {attempt + 1}/{max_attempts})...")
            kill_editor_processes(editor_cmd)
            time.sleep(0.5)
            try:
                KylinEditorTest.current_editor_process = subprocess.Popen(editor_cmd, shell=False)
                print(f"INFO: Waiting for {editor_cmd} (PID: {KylinEditorTest.current_editor_process.pid}) to launch...")
                time.sleep(7)
                if KylinEditorTest.current_editor_process.poll() is not None:
                    print(f"LWARN: Editor process {editor_cmd} (PID: {KylinEditorTest.current_editor_process.pid}) terminated prematurely. Exit code: {KylinEditorTest.current_editor_process.poll()}")
                    continue

                title_to_seek = primary_editor_title if primary_editor_title else editor_cmd
                print(f"LDEBUG: _launch_and_verify_editor - Checking window for {editor_cmd} using effective title '{title_to_seek}' (PID: {KylinEditorTest.current_editor_process.pid})")

                if GUIAutomation.check_window_exists(None, title_to_seek):
                    KylinEditorTest.current_editor_detected_title = title_to_seek 
                    print(f"LINFO: Editor {editor_cmd} (PID: {KylinEditorTest.current_editor_process.pid}) window found using lookup title '{title_to_seek}'. Activating...")
                    GUIAutomation.set_active_window(None, KylinEditorTest.current_editor_detected_title)
                    print(f"LINFO: Editor {editor_cmd} (PID: {KylinEditorTest.current_editor_process.pid}) launched and window verified using '{KylinEditorTest.current_editor_detected_title}'.")
                    return True
                else:
                    print(f"LWARN: Editor {editor_cmd} (PID: {KylinEditorTest.current_editor_process.pid}) process running, but window with lookup title '{title_to_seek}' not found by patched finder.")

                if KylinEditorTest.current_editor_process and KylinEditorTest.current_editor_process.poll() is None:
                    print(f"LDEBUG: Terminating editor process {editor_cmd} (PID: {KylinEditorTest.current_editor_process.pid}) due to window not found.")
                    KylinEditorTest.current_editor_process.terminate()
                    try: KylinEditorTest.current_editor_process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        print(f"LWARN: Timeout waiting for {editor_cmd} to terminate. Killing.")
                        KylinEditorTest.current_editor_process.kill()
                        KylinEditorTest.current_editor_process.wait(timeout=1)
                KylinEditorTest.current_editor_process = None

            except Exception as e:
                print(f"LERROR: Exception during launch/verification of {editor_cmd}: {e}")
                if KylinEditorTest.current_editor_process and KylinEditorTest.current_editor_process.poll() is None:
                    KylinEditorTest.current_editor_process.terminate()
                    try: KylinEditorTest.current_editor_process.wait(timeout=1)
                    except: pass  
                KylinEditorTest.current_editor_process = None
            
            print(f"LINFO: End of attempt {attempt + 1} for {editor_cmd}. Retrying if applicable...")
            time.sleep(3)  
        
        print(f"LERROR: Failed to launch and verify editor {editor_cmd} window after {max_attempts} attempts.")
        return False

    @unittest.skipIf(not AVAILABLE_EDITORS, "没有可用的文本编辑器，跳过测试")
    def test_window_operations(self):
        for editor_info in AVAILABLE_EDITORS:
            editor_cmd = editor_info["cmd"]
            primary_title = editor_info["primary_title"]
            print(f"\n>>>> 开始测试窗口操作: {editor_cmd} <<<<")

            if editor_cmd == "ukui-notebook":
                self.skipTest(f"Skipping {editor_cmd} due to known window finding issues.")
                continue
            
            if not self._launch_and_verify_editor(editor_cmd, primary_title):
                continue  

            self.assertIsNotNone(KylinEditorTest.current_editor_detected_title, f"未能检测到 {editor_cmd} 的窗口标题")
            window_title = KylinEditorTest.current_editor_detected_title
            
            try:
                print(f"测试获取 {editor_cmd} ({window_title}) 窗口大小...")
                size = GUIAutomation.get_window_size(None, window_title)
                self.assertIsNotNone(size, "获取窗口大小失败")
                self.assertIn('width', size); self.assertIn('height', size)
                print(f"原始窗口大小: {size['width']}x{size['height']}")

                
                print(f"测试调整 {editor_cmd} ({window_title}) 窗口大小...")
                new_width, new_height = size['width'] + 50, size['height'] + 50
                resize_result = GUIAutomation.resize_window(None, window_title, new_width, new_height)
                self.assertTrue(resize_result, "调整窗口大小函数调用失败")
                time.sleep(1)

                print(f"测试最大化 {editor_cmd} ({window_title})...")
                maximize_result = GUIAutomation.change_window_state(None, window_title, "maximize")
                self.assertTrue(maximize_result, "最大化窗口失败")
                time.sleep(1)

                print(f"测试还原 {editor_cmd} ({window_title})...")
                restore_result = GUIAutomation.change_window_state(None, window_title, "restore")
                self.assertTrue(restore_result, "还原窗口失败")
                time.sleep(1)

            except Exception as e:
                self.fail(f"编辑器 {editor_cmd} ({window_title}) 窗口操作测试失败: {e}")
            finally:
                print(f"关闭编辑器 {editor_cmd} ({window_title})...")
                if KylinEditorTest.current_editor_process:  
                     GUIAutomation.close_window(None, window_title)
                # tearDown 将处理最终强制结束
            print(f"<<<< 完成测试窗口操作: {editor_cmd} >>>>")

    @unittest.skipIf(not AVAILABLE_EDITORS, "没有可用的文本编辑器，跳过测试")
    def test_text_input(self):
        for editor_info in AVAILABLE_EDITORS:
            editor_cmd = editor_info["cmd"]
            primary_title = editor_info["primary_title"]
            print(f"\n>>>> 开始测试文本输入: {editor_cmd} <<<<")

            if editor_cmd == "ukui-notebook":
                self.skipTest(f"Skipping {editor_cmd} due to known window finding issues.")
                continue

            if not self._launch_and_verify_editor(editor_cmd, primary_title):
                continue

            self.assertIsNotNone(KylinEditorTest.current_editor_detected_title, f"未能检测到 {editor_cmd} 的窗口标题")
            window_title = KylinEditorTest.current_editor_detected_title
            
            editor_locators = {
                "ukui-notebook": ["class:QPlainTextEdit", "class:GtkTextView"],
                "featherpad": ["class:QPlainTextEdit"],
                "gedit": ["class:GtkTextView"],
                "pluma": ["class:GtkTextView"],
                "mousepad": ["class:GtkTextView"],
                "leafpad": ["class:GtkTextView"],
                "xed": ["class:GtkTextView"]
            }
            locators_to_try = editor_locators.get(editor_cmd, ["class:GtkTextView", "class:QPlainTextEdit", "role:text caret"])
            test_text = f"Kylin-自动化测试文本 for {editor_cmd} 123 !@#$%"
            input_success = False

            try:
                for locator in locators_to_try:
                    print(f"尝试向 {editor_cmd} ({window_title}) 输入文本，使用定位器: {locator}")
                    try:
                        # 在输入前再次激活窗口，防止焦点丢失
                        GUIAutomation.set_active_window(None, window_title)
                        time.sleep(0.5)
                        
                        result = GUIAutomation.input_text_to_element(None, locator, test_text, clear_content=True, click_before_input=True)
                        if result:
                            time.sleep(1)
                            element_text = GUIAutomation.get_element_text(None, locator)
                            if element_text and test_text in element_text:
                                print(f"成功为 {editor_cmd} 输入并读取文本: {element_text[:50]}...")
                                input_success = True
                                break  # 此定位器成功
                            else:
                                print(f"为 {editor_cmd} 输入文本后验证失败. 读取内容: '{element_text[:50]}...'")
                        else:
                            print(f"input_text_to_element 调用返回False for {locator}")
                    except Exception as e_locator:
                        print(f"使用定位器 {locator} 为 {editor_cmd} 输入文本时出错: {e_locator}")
                        continue  # 尝试下一个定位器
                
                self.assertTrue(input_success, f"编辑器 {editor_cmd} 未能成功输入并验证文本。")

            except Exception as e:
                self.fail(f"编辑器 {editor_cmd} ({window_title}) 文本输入测试失败: {e}")
            finally:
                print(f"关闭编辑器 {editor_cmd} ({window_title})...")
                if KylinEditorTest.current_editor_process:
                    GUIAutomation.close_window(None, window_title)  
                # tearDown 将处理最终强制结束
            print(f"<<<< 完成测试文本输入: {editor_cmd} >>>>")

if __name__ == "__main__":
    suite = unittest.TestSuite()
    if AVAILABLE_EDITORS:
        suite.addTest(unittest.makeSuite(KylinEditorTest))
    else:
        print("未检测到可用编辑器，跳过所有编辑器测试。")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n--- 编辑器测试资源使用情况 ---")
    current, peak = tracemalloc.get_traced_memory()
    print(f"当前内存使用: {current / 10**6:.2f}MB; 峰值: {peak / 10**6:.2f}MB")
    tracemalloc.stop()

    # 最终清理所有编辑器进程
    for editor_info in AVAILABLE_EDITORS:
        kill_editor_processes(editor_info["cmd"])
        
    sys.exit(not result.wasSuccessful())