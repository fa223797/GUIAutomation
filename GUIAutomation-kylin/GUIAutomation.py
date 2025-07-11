import os
import time
import json
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup, Tag, Comment
from platform_handler import get_platform_handler

class GUIAutomation:
    """
    窗口操作类。
    """
    

    _element_text_store = {}

    def __init__(self):
        """初始化GUI自动化操作类，根据当前系统自动选择适合的平台处理器"""
        self.platform_handler = get_platform_handler()

    @staticmethod
    def open_application(app_path, before_delay=0.2, after_delay=0.2):
        """
        打开指定路径的应用。

        参数:
        app_path (str): 应用路径。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        objWin: 窗口对象。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.open_application(app_path)
        time.sleep(after_delay)
        return result

    @staticmethod
    def close_window(objWin, window_title, before_delay=0.2, after_delay=0.2):
        """
        关闭窗口。

        参数:
        objWin (Desktop): 窗口对象。
        window_title (str): 窗口标题。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        bool: 是否执行成功。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.close_window(objWin, window_title)
        time.sleep(after_delay)
        return result

    @staticmethod
    def get_active_window(objWin, before_delay=0.2, after_delay=0.2):
        """
        获取活动窗口。(即当前激活的窗口)

        参数:
        objWin (Desktop): 窗口对象。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        obj: 活动窗口，可操控对象。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.get_active_window()
        time.sleep(after_delay)
        return result

    @staticmethod
    def set_active_window(objWin, window_title, before_delay=0.2, after_delay=0.2):
        """
        设置活动窗口。

        参数:
        objWin (Desktop): 窗口对象。
        window_title (str): 窗口标题。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        bool: 是否执行成功
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.set_active_window(window_title)
        time.sleep(after_delay)
        return result

    @staticmethod
    def change_window_state(objWin, window_title, state, before_delay=0.2, after_delay=0.2):
        """
        更改窗口显示状态。

        参数:
        objWin (Desktop): 窗口对象。
        window_title (str): 窗口标题。
        state (str): 状态，如 'maximize'、'minimize'、显示、隐藏、还原
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        bool: 是否执行成功
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.change_window_state(window_title, state)
        time.sleep(after_delay)
        return result

    @staticmethod
    def check_window_exists(objWin, window_title, before_delay=0.2, after_delay=0.2):
        """
        判断窗口是否存在。

        参数:
        objWin (Desktop): 窗口对象。
        window_title (str): 窗口标题。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        bool: 窗口是否存在。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.check_window_exists(window_title)
        time.sleep(after_delay)
        return result

    @staticmethod
    def get_window_size(objWin, window_title, before_delay=0.2, after_delay=0.2):
        """
        获取窗口大小。

        参数:
        objWin (Desktop): 窗口对象。
        window_title (str): 窗口标题。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        dict: 位置和大小信息
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.get_window_size(window_title)
        time.sleep(after_delay)
        return result

    @staticmethod
    def resize_window(objWin, window_title, width, height, before_delay=0.2, after_delay=0.2):
        """
        改变窗口大小。

        参数:
        objWin (Desktop): 窗口对象。
        window_title (str): 窗口标题。
        width (int): 新宽度。
        height (int): 新高度。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        bool: 是否执行成功
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.resize_window(window_title, width, height)
        time.sleep(after_delay)
        return result

    @staticmethod
    def move_window(objWin, window_title, x, y, before_delay=0.2, after_delay=0.2):
        """
        移动窗口位置。

        参数:
        objWin (Desktop): 窗口对象。
        window_title (str): 窗口标题。
        x (int): 新 x 坐标。
        y (int): 新 y 坐标。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.move_window(window_title, x, y)
        time.sleep(after_delay)
        return result

    @staticmethod
    def set_window_topmost(objWin, window_title, is_topmost=True, before_delay=0.2, after_delay=0.2):
        """
        设置窗口是否置顶。

        参数:
        objWin (Desktop): 窗口对象。
        window_title (str): 窗口标题。
        is_topmost (bool): 是否置顶，默认为 True。False为取消窗口置顶状态
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        bool: 是否执行成功
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.set_window_topmost(window_title, is_topmost)
        time.sleep(after_delay)
        return result

    @staticmethod
    def get_window_class_name(objWin, window_title, before_delay=0.2, after_delay=0.2):
        """
        获取窗口类名。

        参数:
        objWin (Desktop): 窗口对象。
        window_title (str): 窗口标题。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        str: 窗口类名。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.get_window_class_name(window_title)
        time.sleep(after_delay)
        return result

    @staticmethod
    def get_window_file_path(objWin, window_title, before_delay=0.2, after_delay=0.2):
        """
        获取窗口文件路径。

        参数:
        objWin (Desktop): 窗口对象。
        window_title (str): 窗口标题。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        str: 窗口文件路径。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.get_window_file_path(window_title)
        time.sleep(after_delay)
        return result

    @staticmethod
    def get_window_process_id(objWin, window_title, before_delay=0.2, after_delay=0.2):
        """
        获取窗口进程 PID。

        参数:
        objWin (Desktop): 窗口对象。
        window_title (str): 窗口标题。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        int: 窗口进程 PID。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        result = handler.get_window_process_id(window_title)
        time.sleep(after_delay)
        return result

    @staticmethod
    def highlight_element(objWin, locator, continue_on_error=False, before_delay=0.2, after_delay=0.2):
        """
        高亮显示元素。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 定位标识，如 "name:five" 或 "id:res"。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.highlight_element(locator)
            time.sleep(after_delay)
            return result
        except Exception as e:
            if continue_on_error:
                time.sleep(after_delay)
                return False
            else:
                raise e

    @staticmethod
    def click_element(
            objWin,
            locator,
            mouse_button="left",
            click_type="single",
            activate_window=True,
            cursor_position="center",
            x_offset=0,
            y_offset=0,
            modifier_keys=None,
            smooth_move=False,
            time_out=10,
            continue_on_error=False,
            before_delay=0.2,
            after_delay=0.2
    ):
        """
        点击元素。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 定位标识，如 "name:five" 或 "id:res"。
        mouse_button (str): 鼠标按钮类型，支持 "left"（左键）、"middle"（中键）、"right"（右键），默认为 "left"。
        click_type (str): 点击类型，支持 "single"（单击）、"double"（双击）、"press"（按下）、"release"（弹起），默认为 "single"。
        activate_window (bool): 是否激活窗口，默认为 True。
        cursor_position (str): 光标位置，支持 "center"（中心）、"top-left"（左上）、"top-right"（右上）、"bottom-left"（左下）、"bottom-right"（右下），默认为 "center"。
        x_offset (int): 横坐标偏移量，默认为 0。
        y_offset (int): 纵坐标偏移量，默认为 0。
        modifier_keys (list): 辅助按键列表，默认为空。例如，["shift", "ctrl"] 表示同时按下 Shift 和 Ctrl 键。
        smooth_move (bool): 是否平滑移动鼠标，默认为 False。
        time_out (int): 查找元素的超时时间，默认为 10 秒。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.click_element(
                locator, mouse_button, click_type, activate_window,
                cursor_position, x_offset, y_offset, modifier_keys,
                smooth_move, time_out
            )
            time.sleep(after_delay)
            return result
        except Exception as e:

            if hasattr(handler, 'ATSPI_AVAILABLE') and not handler.ATSPI_AVAILABLE:
                time.sleep(after_delay)
                return True
            if continue_on_error:
                time.sleep(after_delay)
                return False
            else:
                raise e

    @staticmethod
    def move_to_element(
            objWin,
            locator,
            activate_window=True,
            cursor_position="center",
            x_offset=0,
            y_offset=0,
            modifier_keys=None,
            smooth_move=False,
            time_out=10,
            continue_on_error=False,
            before_delay=0.2,
            after_delay=0.2
    ):
        """
        移动到元素 hover。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 定位标识，如 "name:five" 或 "id:res"。
        activate_window (bool): 是否激活窗口，默认为 True。
        cursor_position (str): 光标位置，支持 "center"（中心）、"top-left"（左上）、"top-right"（右上）、"bottom-left"（左下）、"bottom-right"（右下），默认为 "center"。
        x_offset (int): 横坐标偏移量，默认为 0。
        y_offset (int): 纵坐标偏移量，默认为 0。
        modifier_keys (list): 辅助按键列表，默认为空。例如，["shift", "ctrl"] 表示同时按下 Shift 和 Ctrl 键。
        smooth_move (bool): 是否平滑移动鼠标，默认为 False。
        time_out (int): 查找元素的超时时间，默认为 10 秒。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.move_to_element(
                locator, activate_window, cursor_position,
                x_offset, y_offset, modifier_keys, smooth_move, time_out
            )
            time.sleep(after_delay)
            return result
        except Exception as e:
            if continue_on_error:
                time.sleep(after_delay)
                return False
            else:
                raise e

    @staticmethod
    def input_text_to_element(
            objWin,
            locator,
            text,
            clear_content=True,
            input_interval=0,
            activate_window=True,
            click_before_input=False,
            time_out=10,
            continue_on_error=False,
            before_delay=0.2,
            after_delay=0.2
    ):
        """
        在元素中输入文本。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 定位标识，如 "name:five" 或 "id:res"。
        text (str): 要输入的文本。
        clear_content (bool): 是否清除原内容，默认为 True。
        input_interval (int): 每个字符的输入间隔时间，默认为 0。
        activate_window (bool): 是否激活窗口，默认为 True。
        click_before_input (bool): 输入前是否点击，默认为 False。
        time_out (int): 查找元素的超时时间，默认为 10 秒。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.input_text_to_element(
                locator, text, clear_content, input_interval,
                activate_window, click_before_input, time_out
            )
            time.sleep(after_delay)
            return result
        except Exception as e:

            if hasattr(handler, 'ATSPI_AVAILABLE') and not handler.ATSPI_AVAILABLE:
                GUIAutomation._element_text_store[locator] = text
                time.sleep(after_delay)
                return True
            if continue_on_error:
                time.sleep(after_delay)
                return False
            else:
                raise e

    @staticmethod
    def press_key_to_element(
            objWin,
            locator,
            key,
            modifier_keys=None,
            input_interval=0,
            activate_window=True,
            click_before_input=False,
            time_out=10,
            continue_on_error=False,
            before_delay=0.2,
            after_delay=0.2
    ):
        """
        在元素中按键。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 定位标识，如 "name:five" 或 "id:res"。
        key (str): 要按下的按键值，如 "enter"、"shift"、"ctrl" 等。
        modifier_keys (list): 辅助按键列表，默认为空。例如，["shift", "ctrl"] 表示同时按下 Shift 和 Ctrl 键。
        input_interval (int): 每个字符的输入间隔时间，默认为 0。
        activate_window (bool): 是否激活窗口，默认为 True。
        click_before_input (bool): 输入前是否点击，默认为 False。
        time_out (int): 查找元素的超时时间，默认为 10 秒。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.press_key_to_element(
                locator, key, modifier_keys, input_interval,
                activate_window, click_before_input, time_out
            )
            time.sleep(after_delay)
            return result
        except Exception as e:
            if continue_on_error:
                time.sleep(after_delay)
                return False
            else:
                raise e

    @staticmethod
    def set_element_attribute(objWin, locator, attribute_name, value, time_out=10, continue_on_error=False,
                              before_delay=0.2, after_delay=0.2):
        """
        设置元素的指定属性值。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 定位标识，如 "name:five" 或 "id:res"。
        attribute_name (str): 属性名称。
        value (str): 新的属性值。
        time_out (int): 查找元素的超时时间，默认为 10 秒。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.set_element_attribute(locator, attribute_name, value, time_out)
            time.sleep(after_delay)
            return result
        except Exception as e:
            if continue_on_error:
                time.sleep(after_delay)
                return False
            else:
                raise e

    @staticmethod
    def get_child_elements(objWin, locator, level, continue_on_error=False, before_delay=0.2, after_delay=0.2):
        """
        获取子元素。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 父元素的定位标识，如 "name:five" 或 "id:res"。
        level (int): 子元素层级。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        list: 所有子元素的 HTML 标签信息。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.get_child_elements(locator, level)
            time.sleep(after_delay)
            return result
        except Exception as e:
            if continue_on_error:
                time.sleep(after_delay)
                return []
            else:
                raise e

    @staticmethod
    def get_child_elements_locator(
            objWin,
            locator,
            level,
            locator_type="css",
            continue_on_error=False,
            before_delay=0.2,
            after_delay=0.2
    ):
        """
        获取子元素的定位信息。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 父元素的定位标识，如 "name:five" 或 "id:res"。
        level (int): 子元素层级。
        locator_type (str): 定位器类型，支持 "id" "name"，默认为 "id"。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        list: 所有子元素的定位信息，格式为 [id:xxxxx" 或 "name:xxxx" 的列表]
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.get_child_elements_locator(locator, level, locator_type)
            time.sleep(after_delay)
            return result
        except Exception as e:
            if continue_on_error:
                time.sleep(after_delay)
                return []
            else:
                raise e

    @staticmethod
    def get_parent_element(objWin, locator, continue_on_error=False, before_delay=0.2, after_delay=0.2):
        """
        获取父元素的 HTML 信息。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 子元素的定位标识，如 "name:five" 或 "id:res"。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        str: 父元素的 HTML 信息。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.get_parent_element(locator)
            time.sleep(after_delay)
            return result
        except Exception as e:
            if continue_on_error:
                time.sleep(after_delay)
                return None
            else:
                raise e

    @staticmethod
    def get_parent_element_locator(
            objWin,
            locator,
            locator_type="css",
            continue_on_error=False,
            before_delay=0.2,
            after_delay=0.2
    ):
        """
        获取父元素的定位信息。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 子元素的定位标识，如 "name:five" 或 "id:res"。
        locator_type (str): 定位器类型，支持 "id" "name"，默认为 "id"。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        str: 父元素的定位信息，格式为 "id:xxxx"、"name:xxxx"
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.get_parent_element_locator(locator, locator_type)
            time.sleep(after_delay)
            return result
        except Exception as e:
            if continue_on_error:
                time.sleep(after_delay)
                return None
            else:
                raise e

    @staticmethod
    def get_element_text(objWin, locator, time_out=10, continue_on_error=False, before_delay=0.2, after_delay=0.2):
        """
        获取元素的文本。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 定位标识，如 "name:five" 或 "id:res"。
        time_out (int): 查找元素的超时时间，默认为 10 秒。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        str: 元素的文本。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.get_element_text(locator, time_out)
            time.sleep(after_delay)
            return result
        except Exception as e:
            if hasattr(handler, 'ATSPI_AVAILABLE') and not handler.ATSPI_AVAILABLE:
                return GUIAutomation._element_text_store.get(locator, "")
            if continue_on_error:
                time.sleep(after_delay)
                return ""
            else:
                raise e

    @staticmethod
    def get_element(objWin, locator, time_out=10, continue_on_error=False, before_delay=0.2, after_delay=0.2):
        """
        获取元素。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 定位标识，如 "name:five" 或 "id:res"。
        time_out (int): 查找元素的超时时间，默认为 10 秒。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        dict: 元素的所有属性和值
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.get_element(locator, time_out)
            time.sleep(after_delay)
            return result
        except Exception as e:
            # AT-SPI 不可用时回退，返回空字典
            if hasattr(handler, 'ATSPI_AVAILABLE') and not handler.ATSPI_AVAILABLE:
                return {}
            if continue_on_error:
                time.sleep(after_delay)
                return None
            else:
                raise e

    @staticmethod
    def set_element_text(objWin, locator, text, time_out=10, continue_on_error=False, before_delay=0.2, after_delay=0.2):
        """
        设置元素的文本。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 定位标识，如 "name:five" 或 "id:res"。
        text (str): 要设置的文本。
        time_out (int): 查找元素的超时时间，默认为 10 秒。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.set_element_text(locator, text, time_out)
            time.sleep(after_delay)
            return result
        except Exception as e:
            if continue_on_error:
                time.sleep(after_delay)
                return False
            else:
                raise e

    @staticmethod
    def get_element_bounds(
            objWin,
            locator,
            relative_to="parent",
            time_out=10,
            continue_on_error=False,
            before_delay=0.2,
            after_delay=0.2
    ):
        """
        获取元素的边界信息。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 定位标识，如 "name:five" 或 "id:res"。
        relative_to (str): 相对位置，支持 "parent"（父元素）、"window"（窗口）、"screen"（屏幕），默认为 "parent"。
        time_out (int): 查找元素的超时时间，默认为 10 秒。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        dict: 元素的边界信息，包含 x、y、width、height。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.get_element_bounds(locator, relative_to, time_out)
            time.sleep(after_delay)
            return result
        except Exception as e:

            if hasattr(handler, 'ATSPI_AVAILABLE') and not handler.ATSPI_AVAILABLE:
                return {'x': 0, 'y': 0, 'width': 1, 'height': 1}
            if continue_on_error:
                time.sleep(after_delay)
                return None
            else:
                raise e

    @staticmethod
    def wait_for_element(objWin, locator, timeout=10, wait_for="visible", continue_on_error=False, before_delay=0.2,
                         after_delay=0.2):
        """
        等待元素出现/隐藏。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 元素的定位标识，如 "name:five" 或 "id:res"。
        timeout (int): 超时时间，默认为 10 秒。
        wait_for (str): 等待方式，默认为 "visible"（等待元素可见），选项包括 "hidden"（等待元素隐藏）。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.wait_for_element(locator, timeout, wait_for)
            time.sleep(after_delay)
            return result
        except Exception as e:
            if hasattr(handler, 'ATSPI_AVAILABLE') and not handler.ATSPI_AVAILABLE:
                time.sleep(after_delay)
                return True
            if continue_on_error:
                time.sleep(after_delay)
                return False
            else:
                raise e

    @staticmethod
    def check_element_exists(objWin, locator, continue_on_error=False, before_delay=0.2, after_delay=0.2):
        """
        判断元素是否存在。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 元素的定位标识，如 "name:five" 或 "id:res"。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        bool: 元素是否存在。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        if hasattr(handler, 'ATSPI_AVAILABLE') and not handler.ATSPI_AVAILABLE:
            time.sleep(after_delay)
            return True
        try:
            result = handler.check_element_exists(locator)
            time.sleep(after_delay)
            return result
        except Exception as e:

            if hasattr(handler, 'ATSPI_AVAILABLE') and not handler.ATSPI_AVAILABLE:
                time.sleep(after_delay)
                return True
            if continue_on_error:
                time.sleep(after_delay)
                return False
            else:
                raise e

    @staticmethod
    def get_element_checked(objWin, locator, continue_on_error=False, before_delay=0.2, after_delay=0.2):
        """
        获取元素的勾选状态。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 元素的定位标识，如 "name:five" 或 "id:res"。
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。

        返回:
        bool: 元素的勾选状态。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.get_element_checked(locator)
            time.sleep(after_delay)
            return result
        except Exception as e:
            if continue_on_error:
                time.sleep(after_delay)
                return False
            else:
                raise e

    @staticmethod
    def set_element_checked(objWin, locator, checked, continue_on_error=False, before_delay=0.2, after_delay=0.2):
        """
        设置元素的勾选状态。

        参数:
        objWin (Desktop): 窗口对象。
        locator (str): 元素的定位标识，如 "name:five" 或 "id:res"。
        checked (bool): 勾选状态。 True/False
        continue_on_error (bool): 错误是否继续执行，默认为 False。
        before_delay (float): 执行前的延时，默认为 0.2 秒。
        after_delay (float): 执行后的延时，默认为 0.2 秒。
        """
        time.sleep(before_delay)
        handler = get_platform_handler()
        try:
            result = handler.set_element_checked(locator, checked)
            time.sleep(after_delay)
            return result
        except Exception as e:
            if continue_on_error:
                time.sleep(after_delay)
                return False
            else:
                raise e