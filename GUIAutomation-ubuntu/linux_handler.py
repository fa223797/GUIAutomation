import os
import time
import subprocess
import pyautogui
from platform_handler import PlatformHandler
from element_locator import ElementLocator, parse_locator

try:
    import Xlib.display
    import Xlib.X
    import Xlib.Xatom
    from Xlib import XK
    from Xlib.protocol import event
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False

try:
    import gi
    gi.require_version('Atspi', '2.0')
    from gi.repository import Atspi
    ATSPI_AVAILABLE = True
except (ImportError, ValueError):
    ATSPI_AVAILABLE = False

class LinuxHandler(PlatformHandler):
    """Linux平台下的GUI自动化处理器实现"""
    
    def __init__(self):
        self.element_locator = ElementLocator()
        self.display = None
        self.root = None
        if XLIB_AVAILABLE:
            self.display = Xlib.display.Display()
            self.root = self.display.screen().root
        
        # 初始化AT-SPI接口
        if ATSPI_AVAILABLE:
            Atspi.init()
        
        self.app_cache = {}  # 应用程序缓存
        self.window_cache = {}  # 窗口缓存
        self.element_cache = {}  # 元素缓存
        # 标志 AT-SPI 可用性
        self.ATSPI_AVAILABLE = ATSPI_AVAILABLE
    
    def open_application(self, app_path):
        """打开应用程序"""
        try:
            # 检查应用程序是否已在缓存中
            if app_path in self.app_cache and self._is_process_running(self.app_cache[app_path]):
                return self.app_cache[app_path]
            
            # 启动应用程序
            process = subprocess.Popen(app_path, shell=True)
            self.app_cache[app_path] = process.pid
            
            # 等待应用程序启动
            time.sleep(1)
            
            return process.pid
        except Exception as e:
            raise Exception(f"打开应用程序失败: {e}")
    
    def _is_process_running(self, pid):
        """检查进程是否正在运行"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def _find_window_by_title(self, window_title):
        """通过标题查找窗口"""
        if not XLIB_AVAILABLE:
            raise Exception("Xlib不可用，无法查找窗口")
        
        if window_title in self.window_cache:
            window = self.window_cache[window_title]
            try:
                window.get_attributes()  # 验证窗口是否仍然有效
                return window
            except Exception:
                # 从缓存中移除失效窗口
                del self.window_cache[window_title]
        
        def search_window(window, title):
            try:
                wmname = window.get_wm_name()
                # 不区分大小写匹配窗口标题
                if wmname is not None and title.lower() in wmname.lower():
                    return window
                
                children = window.query_tree().children
                for child in children:
                    found = search_window(child, title)
                    if found:
                        return found
            except Exception:
                pass
            return None
        
        window = search_window(self.root, window_title)
        if window:
            self.window_cache[window_title] = window
            return window
        
        raise Exception(f"找不到窗口: {window_title}")
    
    def close_window(self, window_obj, window_title):
        """关闭窗口"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法关闭窗口")
            
            if window_obj:
                window = window_obj
            else:
                window = self._find_window_by_title(window_title)
            
            # 发送关闭窗口事件
            wm_delete = self.display.intern_atom('WM_DELETE_WINDOW')
            wm_protocols = self.display.intern_atom('WM_PROTOCOLS')
            
            # Xlib ClientMessage 需要 5 个字段: [delete atom, timestamp, index, index, index]
            data = [wm_delete, Xlib.X.CurrentTime, 0, 0, 0]
            
            ev = event.ClientMessage(
                window=window,
                client_type=wm_protocols,
                data=(32, data)
            )
            
            mask = Xlib.X.SubstructureRedirectMask | Xlib.X.SubstructureNotifyMask
            self.root.send_event(ev, event_mask=mask)
            self.display.flush()
            
            # 从缓存中移除已关闭的窗口
            if window_title in self.window_cache:
                del self.window_cache[window_title]
            
            return True
        except Exception as e:
            raise Exception(f"关闭窗口失败: {e}")
    
    def get_active_window(self):
        """获取活动窗口"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法获取活动窗口")
            
            active_window_atom = self.display.intern_atom('_NET_ACTIVE_WINDOW')
            active_window = self.root.get_property(active_window_atom, Xlib.X.AnyPropertyType, 0, 1).value[0]
            return self.display.create_resource_object('window', active_window)
        except Exception as e:
            raise Exception(f"获取活动窗口失败: {e}")
    
    def set_active_window(self, window_title):
        """设置活动窗口"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法设置活动窗口")
            
            window = self._find_window_by_title(window_title)
            
            # 激活窗口
            active_atom = self.display.intern_atom('_NET_ACTIVE_WINDOW')
            # Xlib ClientMessage 需要 5 个字段: [add flag, timestamp, index, index, index]
            event_data = [1, Xlib.X.CurrentTime, 0, 0, 0]
            ev = event.ClientMessage(
                window=window,
                client_type=active_atom,
                data=(32, event_data)
            )
            
            mask = Xlib.X.SubstructureRedirectMask | Xlib.X.SubstructureNotifyMask
            self.root.send_event(ev, event_mask=mask)
            self.display.flush()
            
            return True
        except Exception as e:
            raise Exception(f"设置活动窗口失败: {e}")
    
    def change_window_state(self, window_title, state):
        """更改窗口状态"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法更改窗口状态")
            
            window = self._find_window_by_title(window_title)
            
            if state.lower() == 'maximize':
                # 最大化窗口
                wm_state = self.display.intern_atom('_NET_WM_STATE')
                max_horz = self.display.intern_atom('_NET_WM_STATE_MAXIMIZED_HORZ')
                max_vert = self.display.intern_atom('_NET_WM_STATE_MAXIMIZED_VERT')
                
                ev = event.ClientMessage(
                    window=window,
                    client_type=wm_state,
                    data=(32, [1, max_horz, max_vert, 0, 0])
                )
                
                mask = Xlib.X.SubstructureRedirectMask | Xlib.X.SubstructureNotifyMask
                self.root.send_event(ev, event_mask=mask)
            
            elif state.lower() == 'minimize':
                # 最小化窗口
                wm_change_state = self.display.intern_atom('WM_CHANGE_STATE')
                ev = event.ClientMessage(
                    window=window,
                    client_type=wm_change_state,
                    data=(32, [Xlib.X.IconicState, 0, 0, 0, 0])
                )
                
                mask = Xlib.X.SubstructureRedirectMask | Xlib.X.SubstructureNotifyMask
                self.root.send_event(ev, event_mask=mask)
            
            elif state.lower() == 'restore':
                # 还原窗口
                wm_state = self.display.intern_atom('_NET_WM_STATE')
                max_horz = self.display.intern_atom('_NET_WM_STATE_MAXIMIZED_HORZ')
                max_vert = self.display.intern_atom('_NET_WM_STATE_MAXIMIZED_VERT')
                
                ev = event.ClientMessage(
                    window=window,
                    client_type=wm_state,
                    data=(32, [0, max_horz, max_vert, 0, 0])
                )
                
                mask = Xlib.X.SubstructureRedirectMask | Xlib.X.SubstructureNotifyMask
                self.root.send_event(ev, event_mask=mask)
            
            self.display.flush()
            return True
        except Exception as e:
            raise Exception(f"更改窗口状态失败: {e}")
    
    def check_window_exists(self, window_title):
        """检查窗口是否存在"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法检查窗口是否存在")
            
            try:
                self._find_window_by_title(window_title)
                return True
            except Exception:
                return False
        except Exception:
            return False
    
    def get_window_size(self, window_title):
        """获取窗口大小"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法获取窗口大小")
            
            window = self._find_window_by_title(window_title)
            geometry = window.get_geometry()
            
            return {
                'x': geometry.x,
                'y': geometry.y,
                'width': geometry.width,
                'height': geometry.height
            }
        except Exception as e:
            raise Exception(f"获取窗口大小失败: {e}")
    
    def resize_window(self, window_title, width, height):
        """调整窗口大小"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法调整窗口大小")
            
            window = self._find_window_by_title(window_title)
            window.configure(width=width, height=height)
            self.display.flush()
            return True
        except Exception as e:
            raise Exception(f"调整窗口大小失败: {e}")
    
    def move_window(self, window_title, x, y):
        """移动窗口位置"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法移动窗口位置")
            
            window = self._find_window_by_title(window_title)
            window.configure(x=x, y=y)
            self.display.flush()
            return True
        except Exception as e:
            raise Exception(f"移动窗口位置失败: {e}")
    
    def set_window_topmost(self, window_title, is_topmost):
        """设置窗口置顶"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法设置窗口置顶")
            
            window = self._find_window_by_title(window_title)
            
            wm_state = self.display.intern_atom('_NET_WM_STATE')
            above = self.display.intern_atom('_NET_WM_STATE_ABOVE')
            
            action = 1 if is_topmost else 0  # 1: add, 0: remove
            
            ev = event.ClientMessage(
                window=window,
                client_type=wm_state,
                data=(32, [action, above, 0, 0, 0])
            )
            
            mask = Xlib.X.SubstructureRedirectMask | Xlib.X.SubstructureNotifyMask
            self.root.send_event(ev, event_mask=mask)
            self.display.flush()
            
            return True
        except Exception as e:
            raise Exception(f"设置窗口置顶失败: {e}")
    
    def get_window_class_name(self, window_title):
        """获取窗口类名"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法获取窗口类名")
            
            window = self._find_window_by_title(window_title)
            wm_class = window.get_wm_class()
            
            if wm_class and len(wm_class) > 0:
                return wm_class[0]
            return ""
        except Exception as e:
            raise Exception(f"获取窗口类名失败: {e}")
    
    def get_window_file_path(self, window_title):
        """获取窗口文件路径"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法获取窗口文件路径")
            
            window = self._find_window_by_title(window_title)
            pid = self._get_window_pid(window)
            
            if pid:
                try:
                    path = os.readlink(f"/proc/{pid}/exe")
                    return path
                except Exception:
                    pass
            
            return ""
        except Exception as e:
            raise Exception(f"获取窗口文件路径失败: {e}")
    
    def _get_window_pid(self, window):
        """获取窗口的进程ID"""
        if not XLIB_AVAILABLE:
            return None
        
        try:
            pid_atom = self.display.intern_atom('_NET_WM_PID')
            pid = window.get_property(pid_atom, Xlib.X.AnyPropertyType, 0, 1)
            if pid:
                return pid.value[0]
        except Exception:
            pass
        
        return None
    
    def get_window_process_id(self, window_title):
        """获取窗口进程ID"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法获取窗口进程ID")
            
            window = self._find_window_by_title(window_title)
            pid = self._get_window_pid(window)
            
            if pid:
                return pid
            
            return -1
        except Exception as e:
            raise Exception(f"获取窗口进程ID失败: {e}")
    
    # AT-SPI辅助方法
    def _find_accessible_element(self, locator, timeout=10):
        """使用AT-SPI查找元素"""
        if not ATSPI_AVAILABLE:
            raise Exception("AT-SPI不可用，无法查找元素")
        
        cache_key = f"{locator}_{timeout}"
        
        # 检查缓存
        if cache_key in self.element_cache:
            element = self.element_cache[cache_key]
            try:
                # 简单验证元素是否有效
                element.get_name()
                return element
            except Exception:
                # 从缓存中移除无效元素
                del self.element_cache[cache_key]
        
        # 解析定位器
        locator_type, locator_value = parse_locator(locator)
        
        # 使用AT-SPI查找元素
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                desktop = Atspi.get_desktop(0)
                
                # 遍历所有应用程序
                for app_index in range(desktop.get_child_count()):
                    app = desktop.get_child_at_index(app_index)
                    
                    # 遍历应用程序的所有窗口
                    for window_index in range(app.get_child_count()):
                        window = app.get_child_at_index(window_index)
                        
                        # 递归查找元素
                        element = self._find_element_recursive(window, locator_type, locator_value)
                        if element:
                            # 缓存找到的元素
                            self.element_cache[cache_key] = element
                            return element
            except Exception:
                pass
            
            time.sleep(0.5)
        
        raise Exception(f"在{timeout}秒内未找到元素: {locator}")
    
    def _find_element_recursive(self, parent, locator_type, locator_value):
        """递归查找元素"""
        if not ATSPI_AVAILABLE:
            return None
        
        try:
            # 检查当前元素是否匹配
            if locator_type == "id" and parent.get_id() == locator_value:
                return parent
            elif locator_type == "name" and parent.get_name() == locator_value:
                return parent
            elif locator_type == "role" and parent.get_role_name() == locator_value:
                return parent
            elif locator_type == "text" and parent.get_text() == locator_value:
                return parent
            
            # 递归检查子元素
            for i in range(parent.get_child_count()):
                child = parent.get_child_at_index(i)
                if child:
                    element = self._find_element_recursive(child, locator_type, locator_value)
                    if element:
                        return element
        except Exception:
            pass
        
        return None
    
    def highlight_element(self, locator):
        """高亮元素"""
        try:
            element = self._find_accessible_element(locator)
            if element:
                # 获取元素位置和大小
                coords = element.get_extents(Atspi.CoordType.SCREEN)
                x, y, width, height = coords.x, coords.y, coords.width, coords.height
                
                # 使用pyautogui绘制矩形框模拟高亮
                current_x, current_y = pyautogui.position()
                
                # 绘制四条边
                pyautogui.moveTo(x, y)
                pyautogui.dragTo(x + width, y, duration=0.1)
                pyautogui.dragTo(x + width, y + height, duration=0.1)
                pyautogui.dragTo(x, y + height, duration=0.1)
                pyautogui.dragTo(x, y, duration=0.1)
                
                # 恢复鼠标位置
                pyautogui.moveTo(current_x, current_y)
                
                return True
            
            raise Exception(f"无法高亮元素: {locator}")
        except Exception as e:
            raise Exception(f"高亮元素失败: {e}")
    
    def click_element(self, locator, mouse_button="left", click_type="single", 
                     activate_window=True, cursor_position="center", 
                     x_offset=0, y_offset=0, modifier_keys=None, 
                     smooth_move=False, time_out=10):
        """点击元素"""
        try:
            element = self._find_accessible_element(locator, time_out)
            if element:
                # 获取元素位置和大小
                coords = element.get_extents(Atspi.CoordType.SCREEN)
                x, y, width, height = coords.x, coords.y, coords.width, coords.height
                
                # 计算点击位置
                if cursor_position == "center":
                    click_x = x + width // 2 + x_offset
                    click_y = y + height // 2 + y_offset
                elif cursor_position == "top-left":
                    click_x = x + x_offset
                    click_y = y + y_offset
                elif cursor_position == "top-right":
                    click_x = x + width + x_offset
                    click_y = y + y_offset
                elif cursor_position == "bottom-left":
                    click_x = x + x_offset
                    click_y = y + height + y_offset
                elif cursor_position == "bottom-right":
                    click_x = x + width + x_offset
                    click_y = y + height + y_offset
                
                # 应用修饰键
                if modifier_keys:
                    for key in modifier_keys:
                        pyautogui.keyDown(key)
                
                # 移动鼠标
                if smooth_move:
                    pyautogui.moveTo(click_x, click_y, duration=0.5)
                else:
                    pyautogui.moveTo(click_x, click_y)
                
                # 执行点击
                if click_type == "single":
                    if mouse_button == "left":
                        pyautogui.click(button='left')
                    elif mouse_button == "right":
                        pyautogui.click(button='right')
                    elif mouse_button == "middle":
                        pyautogui.click(button='middle')
                elif click_type == "double":
                    if mouse_button == "left":
                        pyautogui.doubleClick(button='left')
                    elif mouse_button == "right":
                        pyautogui.doubleClick(button='right')
                    elif mouse_button == "middle":
                        pyautogui.doubleClick(button='middle')
                elif click_type == "press":
                    if mouse_button == "left":
                        pyautogui.mouseDown(button='left')
                    elif mouse_button == "right":
                        pyautogui.mouseDown(button='right')
                    elif mouse_button == "middle":
                        pyautogui.mouseDown(button='middle')
                elif click_type == "release":
                    if mouse_button == "left":
                        pyautogui.mouseUp(button='left')
                    elif mouse_button == "right":
                        pyautogui.mouseUp(button='right')
                    elif mouse_button == "middle":
                        pyautogui.mouseUp(button='middle')
                
                # 释放修饰键
                if modifier_keys:
                    for key in reversed(modifier_keys):
                        pyautogui.keyUp(key)
                
                return True
            
            raise Exception(f"未找到元素: {locator}")
        except Exception as e:
            raise Exception(f"点击元素失败: {e}")
    
    # 以下方法按照相同的模式实现
    # 为了简化代码，实现其中几个关键方法，其余方法保持相同模式
    
    def move_to_element(self, locator, activate_window=True, cursor_position="center", 
                       x_offset=0, y_offset=0, modifier_keys=None, 
                       smooth_move=False, time_out=10):
        """移动到元素"""
        try:
            element = self._find_accessible_element(locator, time_out)
            if element:
                # 获取元素位置和大小
                coords = element.get_extents(Atspi.CoordType.SCREEN)
                x, y, width, height = coords.x, coords.y, coords.width, coords.height
                
                # 计算移动位置
                if cursor_position == "center":
                    move_x = x + width // 2 + x_offset
                    move_y = y + height // 2 + y_offset
                elif cursor_position == "top-left":
                    move_x = x + x_offset
                    move_y = y + y_offset
                elif cursor_position == "top-right":
                    move_x = x + width + x_offset
                    move_y = y + y_offset
                elif cursor_position == "bottom-left":
                    move_x = x + x_offset
                    move_y = y + height + y_offset
                elif cursor_position == "bottom-right":
                    move_x = x + width + x_offset
                    move_y = y + height + y_offset
                
                # 应用修饰键
                if modifier_keys:
                    for key in modifier_keys:
                        pyautogui.keyDown(key)
                
                # 移动鼠标
                if smooth_move:
                    pyautogui.moveTo(move_x, move_y, duration=0.5)
                else:
                    pyautogui.moveTo(move_x, move_y)
                
                # 释放修饰键
                if modifier_keys:
                    for key in reversed(modifier_keys):
                        pyautogui.keyUp(key)
                
                return True
            
            raise Exception(f"未找到元素: {locator}")
        except Exception as e:
            raise Exception(f"移动到元素失败: {e}")
    
    def input_text_to_element(self, locator, text, clear_content=True, 
                             input_interval=0, activate_window=True, 
                             click_before_input=False, time_out=10):
        """在元素中输入文本"""
        try:
            element = self._find_accessible_element(locator, time_out)
            if element:
                # 获取元素位置和大小
                coords = element.get_extents(Atspi.CoordType.SCREEN)
                x, y, width, height = coords.x, coords.y, coords.width, coords.height
                
                # 如果需要，先点击元素
                if click_before_input:
                    click_x = x + width // 2
                    click_y = y + height // 2
                    pyautogui.click(click_x, click_y)
                
                # 如果需要，清除原有内容
                if clear_content:
                    pyautogui.hotkey('ctrl', 'a')
                    pyautogui.press('delete')
                
                # 输入文本
                if input_interval > 0:
                    for char in text:
                        pyautogui.write(char)
                        time.sleep(input_interval)
                else:
                    pyautogui.write(text)
                
                return True
            
            raise Exception(f"未找到元素: {locator}")
        except Exception as e:
            raise Exception(f"在元素中输入文本失败: {e}")
    
    # 以下是剩余方法的简单实现，为了节省空间，它们的实现类似
    
    def press_key_to_element(self, locator, key, modifier_keys=None, 
                            input_interval=0, activate_window=True, 
                            click_before_input=False, time_out=10):
        """在元素中按键"""
        try:
            element = self._find_accessible_element(locator, time_out)
            if element:
                # 获取元素位置，如果需要先点击
                if click_before_input:
                    coords = element.get_extents(Atspi.CoordType.SCREEN)
                    x, y, width, height = coords.x, coords.y, coords.width, coords.height
                    click_x = x + width // 2
                    click_y = y + height // 2
                    pyautogui.click(click_x, click_y)
                
                # 应用修饰键并按键
                if modifier_keys:
                    keys = modifier_keys + [key]
                    pyautogui.hotkey(*keys)
                else:
                    pyautogui.press(key)
                
                if input_interval > 0:
                    time.sleep(input_interval)
                
                return True
            
            raise Exception(f"未找到元素: {locator}")
        except Exception as e:
            raise Exception(f"在元素中按键失败: {e}")
    
    # 其他方法的实现...
    # 为了简化，这里只提供了核心方法的实现
    # 实际使用时需要完善所有方法
    
    def set_element_attribute(self, locator, attribute_name, value, time_out=10):
        """设置元素属性 - 实现版"""
        try:
            element = self._find_accessible_element(locator, time_out)
            # 文本或名称属性，通过输入实现
            if attribute_name.lower() in ("text", "name"):
                return self.input_text_to_element(locator, value, clear_content=True, input_interval=0,
                                                  activate_window=True, click_before_input=True, time_out=time_out)
            # 聚焦属性，通过点击元素中心实现
            elif attribute_name.lower() == "focus":
                coords = element.get_extents(Atspi.CoordType.SCREEN)
                pyautogui.click(coords.x + coords.width//2, coords.y + coords.height//2)
                return True
            else:
                raise NotImplementedError(f"Linux下不支持设置属性: {attribute_name}")
        except Exception as e:
            raise Exception(f"设置元素属性失败: {e}")

    def get_child_elements(self, locator, level):
        """获取子元素 - 实现版"""
        try:
            parent = self._find_accessible_element(locator)
            # 递归收集指定层级的元素
            def collect(elem, curr, target):
                if curr == target:
                    return [elem]
                res = []
                for i in range(elem.get_child_count()):
                    child = elem.get_child_at_index(i)
                    res += collect(child, curr+1, target)
                return res
            elems = collect(parent, 1, level)
            result = []
            for e in elems:
                coords = e.get_extents(Atspi.CoordType.SCREEN)
                result.append({
                    "name": e.get_name(),
                    "role": e.get_role_name(),
                    "id": e.get_id(),
                    "text": e.get_text(0, -1) if hasattr(e, "get_text") else "",
                    "rectangle": {"x": coords.x, "y": coords.y, "width": coords.width, "height": coords.height},
                    "states": [s.name for s in e.get_state_set()]
                })
            return result
        except Exception as e:
            raise Exception(f"获取子元素失败: {e}")

    def get_child_elements_locator(self, locator, level, locator_type="id"):
        """获取子元素定位器 - 实现版"""
        try:
            parent = self._find_accessible_element(locator)
            def collect(elem, curr, target):
                if curr == target:
                    return [elem]
                res = []
                for i in range(elem.get_child_count()):
                    res += collect(elem.get_child_at_index(i), curr+1, target)
                return res
            elems = collect(parent, 1, level)
            locators = []
            for e in elems:
                if locator_type.lower() == "id" and e.get_id():
                    locators.append(f"id:{e.get_id()}")
                elif locator_type.lower() == "name" and e.get_name():
                    locators.append(f"name:{e.get_name()}")
                elif locator_type.lower() == "role" and e.get_role_name():
                    locators.append(f"role:{e.get_role_name()}")
            return locators
        except Exception as e:
            raise Exception(f"获取子元素定位器失败: {e}")

    def get_parent_element(self, locator):
        """获取父元素 - 实现版"""
        try:
            elem = self._find_accessible_element(locator)
            parent = elem.get_parent()
            if not parent:
                return None
            coords = parent.get_extents(Atspi.CoordType.SCREEN)
            return {
                "name": parent.get_name(),
                "role": parent.get_role_name(),
                "id": parent.get_id(),
                "text": parent.get_text(0, -1) if hasattr(parent, "get_text") else "",
                "rectangle": {"x": coords.x, "y": coords.y, "width": coords.width, "height": coords.height},
                "states": [s.name for s in parent.get_state_set()]
            }
        except Exception as e:
            raise Exception(f"获取父元素失败: {e}")

    def get_parent_element_locator(self, locator, locator_type="id"):
        """获取父元素定位器 - 实现版"""
        try:
            elem = self._find_accessible_element(locator)
            parent = elem.get_parent()
            if not parent:
                return None
            if locator_type.lower() == "id" and parent.get_id():
                return f"id:{parent.get_id()}"
            elif locator_type.lower() == "name" and parent.get_name():
                return f"name:{parent.get_name()}"
            elif locator_type.lower() == "role" and parent.get_role_name():
                return f"role:{parent.get_role_name()}"
            return None
        except Exception as e:
            raise Exception(f"获取父元素定位器失败: {e}")
    
    def get_element_text(self, locator, time_out=10):
        """获取元素文本 - 简化实现"""
        try:
            element = self._find_accessible_element(locator, time_out)
            if element:
                text = element.get_text(0, -1)
                if text:
                    return text
                return element.get_name()
            raise Exception(f"未找到元素: {locator}")
        except Exception as e:
            raise Exception(f"获取元素文本失败: {e}")
    
    def get_element(self, locator, time_out=10):
        """获取元素 - 简化实现"""
        try:
            element = self._find_accessible_element(locator, time_out)
            if element:
                coords = element.get_extents(Atspi.CoordType.SCREEN)
                return {
                    "name": element.get_name(),
                    "role": element.get_role_name(),
                    "text": element.get_text(0, -1) if hasattr(element, 'get_text') else "",
                    "rectangle": {
                        "x": coords.x,
                        "y": coords.y,
                        "width": coords.width,
                        "height": coords.height
                    },
                    "states": [state.name for state in element.get_state_set()]
                }
            raise Exception(f"未找到元素: {locator}")
        except Exception as e:
            raise Exception(f"获取元素失败: {e}")
    
    def set_element_text(self, locator, text, time_out=10):
        """设置元素文本 - 简化实现"""
        return self.input_text_to_element(locator, text, True, 0, True, True, time_out)
    
    def get_element_bounds(self, locator, relative_to="parent", time_out=10):
        """获取元素边界 - 简化实现"""
        try:
            element = self._find_accessible_element(locator, time_out)
            if element:
                coords = element.get_extents(Atspi.CoordType.SCREEN)
                
                if relative_to == "parent":
                    parent = element.get_parent()
                    if parent:
                        parent_coords = parent.get_extents(Atspi.CoordType.SCREEN)
                        return {
                            "x": coords.x - parent_coords.x,
                            "y": coords.y - parent_coords.y,
                            "width": coords.width,
                            "height": coords.height
                        }
                
                # 默认返回相对于屏幕的坐标
                return {
                    "x": coords.x,
                    "y": coords.y,
                    "width": coords.width,
                    "height": coords.height
                }
            
            raise Exception(f"未找到元素: {locator}")
        except Exception as e:
            raise Exception(f"获取元素边界失败: {e}")
    
    def wait_for_element(self, locator, timeout=10, wait_for="visible"):
        """等待元素 - 简化实现"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                element = self._find_accessible_element(locator, 1)
                
                if wait_for == "visible":
                    # 检查可见状态
                    states = element.get_state_set()
                    visible = Atspi.StateType.VISIBLE in states
                    if visible:
                        return True
                elif wait_for == "hidden":
                    # 检查隐藏状态
                    states = element.get_state_set()
                    visible = Atspi.StateType.VISIBLE in states
                    if not visible:
                        return True
            except Exception:
                if wait_for == "hidden":
                    return True
            
            time.sleep(0.5)
        
        raise Exception(f"等待元素超时: {locator}, 等待条件: {wait_for}")
    
    def check_element_exists(self, locator):
        """检查元素是否存在 - 简化实现"""
        try:
            element = self._find_accessible_element(locator, 1)
            return element is not None
        except Exception:
            return False
    
    def get_element_checked(self, locator):
        """获取元素选中状态 - 简化实现"""
        try:
            element = self._find_accessible_element(locator)
            if element:
                states = element.get_state_set()
                return Atspi.StateType.CHECKED in states
            return False
        except Exception as e:
            raise Exception(f"获取元素选中状态失败: {e}")
    
    def set_element_checked(self, locator, checked):
        """设置元素选中状态 - 简化实现"""
        try:
            element = self._find_accessible_element(locator)
            if element:
                current_state = Atspi.StateType.CHECKED in element.get_state_set()
                
                if (checked and not current_state) or (not checked and current_state):
                    # 点击元素切换状态
                    coords = element.get_extents(Atspi.CoordType.SCREEN)
                    x = coords.x + coords.width // 2
                    y = coords.y + coords.height // 2
                    pyautogui.click(x, y)
                
                return True
            
            raise Exception(f"未找到元素: {locator}")
        except Exception as e:
            raise Exception(f"设置元素选中状态失败: {e}") 