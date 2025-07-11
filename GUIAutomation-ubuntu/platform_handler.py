import os
import sys
from abc import ABC, abstractmethod

class PlatformHandler(ABC):
    """平台处理抽象基类，定义所有平台需要实现的接口"""
    
    @abstractmethod
    def open_application(self, app_path):
        """打开应用程序"""
        pass
        
    @abstractmethod
    def close_window(self, window_obj, window_title):
        """关闭窗口"""
        pass
        
    @abstractmethod
    def get_active_window(self):
        """获取活动窗口"""
        pass
        
    @abstractmethod
    def set_active_window(self, window_title):
        """设置活动窗口"""
        pass
        
    @abstractmethod
    def change_window_state(self, window_title, state):
        """更改窗口状态"""
        pass
        
    @abstractmethod
    def check_window_exists(self, window_title):
        """检查窗口是否存在"""
        pass
        
    @abstractmethod
    def get_window_size(self, window_title):
        """获取窗口大小"""
        pass
        
    @abstractmethod
    def resize_window(self, window_title, width, height):
        """调整窗口大小"""
        pass
        
    @abstractmethod
    def move_window(self, window_title, x, y):
        """移动窗口位置"""
        pass
        
    @abstractmethod
    def set_window_topmost(self, window_title, is_topmost):
        """设置窗口置顶"""
        pass
        
    @abstractmethod
    def get_window_class_name(self, window_title):
        """获取窗口类名"""
        pass
        
    @abstractmethod
    def get_window_file_path(self, window_title):
        """获取窗口文件路径"""
        pass
        
    @abstractmethod
    def get_window_process_id(self, window_title):
        """获取窗口进程ID"""
        pass
        
    @abstractmethod
    def highlight_element(self, locator):
        """高亮元素"""
        pass
        
    @abstractmethod
    def click_element(self, locator, mouse_button, click_type, activate_window, 
                     cursor_position, x_offset, y_offset, modifier_keys, smooth_move, time_out):
        """点击元素"""
        pass
        
    @abstractmethod
    def move_to_element(self, locator, activate_window, cursor_position, 
                       x_offset, y_offset, modifier_keys, smooth_move, time_out):
        """移动到元素"""
        pass
        
    @abstractmethod
    def input_text_to_element(self, locator, text, clear_content, input_interval, 
                             activate_window, click_before_input, time_out):
        """在元素中输入文本"""
        pass
        
    @abstractmethod
    def press_key_to_element(self, locator, key, modifier_keys, input_interval, 
                            activate_window, click_before_input, time_out):
        """在元素中按键"""
        pass
        
    @abstractmethod
    def set_element_attribute(self, locator, attribute_name, value, time_out):
        """设置元素属性"""
        pass
        
    @abstractmethod
    def get_child_elements(self, locator, level):
        """获取子元素"""
        pass
        
    @abstractmethod
    def get_child_elements_locator(self, locator, level, locator_type):
        """获取子元素定位器"""
        pass
        
    @abstractmethod
    def get_parent_element(self, locator):
        """获取父元素"""
        pass
        
    @abstractmethod
    def get_parent_element_locator(self, locator, locator_type):
        """获取父元素定位器"""
        pass
        
    @abstractmethod
    def get_element_text(self, locator, time_out):
        """获取元素文本"""
        pass
        
    @abstractmethod
    def get_element(self, locator, time_out):
        """获取元素"""
        pass
        
    @abstractmethod
    def set_element_text(self, locator, text, time_out):
        """设置元素文本"""
        pass
        
    @abstractmethod
    def get_element_bounds(self, locator, relative_to, time_out):
        """获取元素边界"""
        pass
        
    @abstractmethod
    def wait_for_element(self, locator, timeout, wait_for):
        """等待元素"""
        pass
        
    @abstractmethod
    def check_element_exists(self, locator):
        """检查元素是否存在"""
        pass
        
    @abstractmethod
    def get_element_checked(self, locator):
        """获取元素选中状态"""
        pass
        
    @abstractmethod
    def set_element_checked(self, locator, checked):
        """设置元素选中状态"""
        pass

def get_platform_handler():
    """根据当前操作系统返回相应的平台处理器"""
    if sys.platform.startswith('linux'):
        # 检测是否为麒麟或Ubuntu
        if os.path.exists('/etc/kylin-release'):
            from linux_kylin_handler import LinuxKylinHandler
            return LinuxKylinHandler()
        else:
            from linux_handler import LinuxHandler
            return LinuxHandler()
    else:
        raise NotImplementedError(f"不支持的平台: {sys.platform}") 