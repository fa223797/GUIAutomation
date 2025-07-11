import os
# 设置环境变量，避免AT-SPI相关兼容性问题
os.environ['NO_AT_BRIDGE'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'

import unittest
import time
import subprocess
import shutil
from GUIAutomation import GUIAutomation

class TestWindowExtraMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 动态选择可用的窗口应用，优先选择未被其他测试覆盖的应用
        candidates = ['xterm', 'xcalc', 'mate-calc']
        title_map = {'xterm':'xterm', 'xcalc':'Calculator', 'mate-calc':'mate-calc'}
        for cmd in candidates:
            if shutil.which(cmd):
                cls.app_cmd = cmd
                cls.window_title = title_map[cmd]
                break
        else:
            raise unittest.SkipTest('未检测到 xterm/xcalc/mate-calc，跳过额外窗口方法测试')

    def setUp(self):
        # 启动应用，准备测试环境
        self.proc = subprocess.Popen([self.__class__.app_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

    def tearDown(self):
        # 关闭应用，清理测试环境
        try:
            GUIAutomation.close_window(None, self.__class__.window_title)
        except:
            pass
        time.sleep(0.5)
        subprocess.run(['pkill', '-9', '-f', self.__class__.app_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)

    def test_move_window(self):
        # 验证窗口移动功能
        pid = GUIAutomation.open_application(self.__class__.app_cmd)
        self.assertTrue(GUIAutomation.check_window_exists(None, self.__class__.window_title))
        size = GUIAutomation.get_window_size(None, self.__class__.window_title)
        x0, y0 = size['x'], size['y']
        result = GUIAutomation.move_window(None, self.__class__.window_title, x0+10, y0+10)
        self.assertTrue(result, 'move_window 调用失败')

    def test_set_topmost_and_restore(self):
        # 验证窗口置顶与取消置顶功能
        GUIAutomation.open_application(self.__class__.app_cmd)
        self.assertTrue(GUIAutomation.check_window_exists(None, self.__class__.window_title))
        self.assertTrue(GUIAutomation.set_window_topmost(None, self.__class__.window_title, True), '设置置顶失败')
        self.assertTrue(GUIAutomation.set_window_topmost(None, self.__class__.window_title, False), '取消置顶失败')

    def test_window_info_methods(self):
        # 验证窗口信息获取相关方法
        GUIAutomation.open_application(self.__class__.app_cmd)
        self.assertTrue(GUIAutomation.check_window_exists(None, self.__class__.window_title))
        cls_name = GUIAutomation.get_window_class_name(None, self.__class__.window_title)
        self.assertIsInstance(cls_name, str)
        pid = GUIAutomation.get_window_process_id(None, self.__class__.window_title)
        self.assertIsInstance(pid, int)
        path = GUIAutomation.get_window_file_path(None, self.__class__.window_title)
        self.assertIsInstance(path, str)

if __name__ == '__main__':
    unittest.main(verbosity=2)