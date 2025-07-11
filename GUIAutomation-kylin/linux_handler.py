import os
import time
import subprocess
import pyautogui
from platform_handler import PlatformHandler
from element_locator import ElementLocator, parse_locator
import contextlib

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

"""X11显示连接的上下文管理器，确保X11连接能正确打开和关闭。"""
@contextlib.contextmanager
def x11_display_connection():
    if not XLIB_AVAILABLE:
        yield None, None
        return
        
    try:
        display = Xlib.display.Display()
        root = display.screen().root
        yield display, root
    finally:
        if 'display' in locals() and display:
            display.close()

class LinuxHandler(PlatformHandler):
    """kylin平台下的GUI自动化处理器实现，封装了窗口、应用、元素等自动化操作。"""
    
    def __init__(self):
        # 初始化元素定位器
        self.element_locator = ElementLocator()
        self.display = None
        self.root = None
        
        # 初始化AT-SPI接口（辅助技术接口）
        if ATSPI_AVAILABLE:
            try:
                Atspi.init()
            except Exception as e:
                print(f"LWARN: Atspi.init() failed: {e}. AT-SPI features may be limited.")
                # 即使Atspi.init()失败，ATSPI_AVAILABLE可能仍为True，但实际操作可能失败。
        
        self.app_cache = {}  # 应用程序缓存，记录已打开应用的pid
        self.window_cache = {}  # 窗口缓存，记录窗口ID
        self.element_cache = {}  # 元素缓存，记录已定位的元素
        self.ATSPI_AVAILABLE = ATSPI_AVAILABLE # 默认与全局一致，子类可覆盖
    
    def _get_display_connection(self):
        """获取一个新的 X11 display 连接。用于与X11窗口系统交互，返回display和root对象。"""
        if not XLIB_AVAILABLE:
            return None, None
        try:
            display = Xlib.display.Display()
            root = display.screen().root
            return display, root
        except Exception:
            return None, None
    
    def open_application(self, app_path):
        """打开应用程序。若已在缓存中且进程存活则直接返回，否则启动新进程并缓存其pid。"""
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
        """检查进程是否正在运行。通过os.kill发送0信号判断pid是否有效。"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def _find_window_by_title(self, window_title):
        """通过标题查找窗口。递归遍历窗口树，支持缓存，返回Xlib窗口对象。若缓存失效则重新查找。"""
        if not XLIB_AVAILABLE:
            raise Exception("Xlib不可用，无法查找窗口")
        
        # 操作必须在显示连接上下文中执行
        with x11_display_connection() as (display, root):
            if not display or not root:
                raise Exception("无法连接到X11显示服务器 (_find_window_by_title)")

            # 检查缓存（缓存存储窗口ID）
            if window_title in self.window_cache:
                window_id = self.window_cache[window_title]
                try:
                    # 用当前display和缓存ID创建窗口对象
                    cached_window_obj = display.create_resource_object('window', window_id)
                    cached_window_obj.get_attributes()  # 验证窗口是否存在
                    return cached_window_obj # 有效对象
                except Exception: # 缓存失效
                    del self.window_cache[window_title]
            
            # 递归查找窗口
            def search_window_recursive(current_window_obj, title_to_find):
                try:
                    wmname_prop = current_window_obj.get_wm_name() 
                    actual_wm_name = ""
                    if isinstance(wmname_prop, bytes):
                        try:
                            actual_wm_name = wmname_prop.decode('utf-8', 'replace')
                        except AttributeError: 
                             actual_wm_name = str(wmname_prop) if wmname_prop is not None else ""
                    elif wmname_prop is not None:
                        actual_wm_name = str(wmname_prop)

                    if title_to_find.lower() in actual_wm_name.lower():
                        return current_window_obj
                    
                    children = current_window_obj.query_tree().children
                    for child_obj in children:
                        found = search_window_recursive(child_obj, title_to_find)
                        if found:
                            return found
                except (Xlib.error.BadWindow, Xlib.error.IDChoiceError): 
                    pass
                except Exception: 
                    pass
                return None
            
            found_window_obj = search_window_recursive(root, window_title)
            
            if found_window_obj:
                self.window_cache[window_title] = found_window_obj.id # 缓存ID
                return found_window_obj # 有效对象
            
        raise Exception(f"找不到窗口: {window_title}")

    def close_window(self, window_obj, window_title):
        """关闭窗口。优先通过Xlib发送关闭事件，失败时尝试使用xdotool命令关闭。"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法关闭窗口")

            # 获取窗口ID，支持直接传对象或标题查找
            if window_obj and hasattr(window_obj, 'id'):
                window_id = window_obj.id
            elif window_title:
                temp_xlib_window = self._find_window_by_title(window_title)
                if not temp_xlib_window:
                    raise Exception(f"找不到窗口 (for close_window): {window_title}")
                window_id = temp_xlib_window.id
            else:
                raise Exception("无法确定要关闭的窗口: 需要 window_obj 或 window_title")

            # 在新display上下文中操作
            with x11_display_connection() as (display, root):
                if not display or not root:
                    raise Exception("无法连接到X11显示服务器 (close_window)")

                # 创建窗口对象
                window_to_act_on = display.create_resource_object('window', window_id)
            
                wm_delete = display.intern_atom('WM_DELETE_WINDOW')
                wm_protocols = display.intern_atom('WM_PROTOCOLS')
                
                # 构造关闭事件
                data = [wm_delete, Xlib.X.CurrentTime, 0, 0, 0]
                
                ev = event.ClientMessage(
                    window=window_to_act_on,
                    client_type=wm_protocols,
                    data=(32, data)
                )
                
                mask = Xlib.X.SubstructureRedirectMask | Xlib.X.SubstructureNotifyMask
                root.send_event(ev, event_mask=mask)
                display.flush()
            
            # 从缓存移除
            if window_title and window_title in self.window_cache:
                del self.window_cache[window_title]
            
            # 补充：尝试xdotool关闭
            try:
                print(f"LDEBUG: close_window - Attempting xdotool windowclose for title '{window_title}'")
                subprocess.run(['xdotool', 'search', '--name', str(window_title), 'windowclose', '%1'], 
                                 check=False, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, timeout=2)
            except Exception as xde:
                print(f"LWARN: close_window - xdotool windowclose attempt failed for '{window_title}': {xde}")
            
            return True
        except Exception as e:
            # 如果 Xlib 方法失败，尝试使用 xdotool 作为最后手段
            try:
                print(f"LWARN: close_window - Xlib close failed ('{e}'). Attempting xdotool fallback for title '{window_title}'.")
                subprocess.run(['xdotool', 'search', '--name', str(window_title), 'windowclose', '%1'], 
                                 check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, timeout=2)
                print(f"LINFO: close_window - xdotool windowclose fallback SUCCEEDED for '{window_title}'.")
                if window_title and window_title in self.window_cache:
                    del self.window_cache[window_title]
                return True
            except Exception as xde_fallback:
                print(f"LERROR: close_window - xdotool windowclose fallback also FAILED for '{window_title}': {xde_fallback}")
                raise Exception(f"关闭窗口失败 (Xlib and xdotool attempts failed): {e}")
    
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
            
            # 获取 window ID 
            temp_xlib_window_for_id = self._find_window_by_title(window_title)
            if not temp_xlib_window_for_id:
                raise Exception(f"找不到窗口 (for set_active_window): {window_title}")
            window_id_to_activate = temp_xlib_window_for_id.id

            with x11_display_connection() as (display, root):
                if not display or not root:
                    raise Exception("无法连接到X11显示服务器 (set_active_window)")
                

                window_to_activate_obj = display.create_resource_object('window', window_id_to_activate)

                active_atom = display.intern_atom('_NET_ACTIVE_WINDOW')

                ev = event.ClientMessage(
                    window=root, 
                    client_type=active_atom,
                    data=(32, [
                        1,       
                        Xlib.X.CurrentTime, 
                        window_to_activate_obj.id, 
                        0, 
                        0  
                    ])
                )
                
                
                mask = Xlib.X.SubstructureRedirectMask | Xlib.X.SubstructureNotifyMask
                root.send_event(ev, event_mask=mask)
                display.flush()
                
               
                window_to_activate_obj.map() 
                window_to_activate_obj.raise_window() 
                window_to_activate_obj.set_input_focus(Xlib.X.RevertToParent, Xlib.X.CurrentTime) 
                display.sync() 
                
                time.sleep(0.5) 
            
            return True
        except Exception as e:
            # If Xlib methods fail, try xdotool as a last resort
            print(f"LDEBUG: set_active_window Xlib failed for '{window_title}': {e}. Trying xdotool.")
            try:
                # 如果同名窗口多个，使用 '%1' 激活第一个匹配
                safe_title = str(window_title)
                # Use '%1' to activate the first match if multiple windows have the same name
                subprocess.run(['xdotool', 'search', '--name', safe_title, 'windowactivate', '%1'], 
                                 check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, timeout=3)
                print(f"LINFO: set_active_window succeeded with xdotool for '{window_title}'.")
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as xde:
                print(f"LWARN: set_active_window xdotool also failed for '{window_title}': {xde}")
                # 继续执行，以便抛出原始 Xlib 异常，该异常对主要方法更具信息量
            
            raise Exception(f"设置活动窗口失败 (Xlib primary and xdotool fallback failed): {e}")
    
    def change_window_state(self, window_title, state):
        """更改窗口状态"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法更改窗口状态")

            # 获取窗口 ID
            temp_window = self._find_window_by_title(window_title)
            if not temp_window:
                raise Exception(f"找不到窗口 (for change_window_state): {window_title}")
            window_id = temp_window.id

            # 在新的 X11 连接上下文中执行状态更改
            with x11_display_connection() as (display, root):
                if not display or not root:
                    raise Exception("无法连接到X11显示服务器 (change_window_state)")

                # 在当前 display 上创建窗口对象
                window = display.create_resource_object('window', window_id)
                wm_state_atom = display.intern_atom('_NET_WM_STATE')

                mask = Xlib.X.SubstructureRedirectMask | Xlib.X.SubstructureNotifyMask
                if state.lower() == 'maximize':
                    max_horz = display.intern_atom('_NET_WM_STATE_MAXIMIZED_HORZ')
                    max_vert = display.intern_atom('_NET_WM_STATE_MAXIMIZED_VERT')
                    ev = event.ClientMessage(
                        window=root,
                        client_type=wm_state_atom,
                        data=(32, [1, max_horz, max_vert, 0, 0])
                    )
                    root.send_event(ev, event_mask=mask)

                elif state.lower() == 'minimize':
                    change_state_atom = display.intern_atom('WM_CHANGE_STATE')
                    ev = event.ClientMessage(
                        window=root,
                        client_type=change_state_atom,
                        data=(32, [3, 0, 0, 0, 0])
                    )
                    root.send_event(ev, event_mask=mask)

                elif state.lower() == 'restore':
                    max_horz = display.intern_atom('_NET_WM_STATE_MAXIMIZED_HORZ')
                    max_vert = display.intern_atom('_NET_WM_STATE_MAXIMIZED_VERT')
                    ev = event.ClientMessage(
                        window=root,
                        client_type=wm_state_atom,
                        data=(32, [0, max_horz, max_vert, 0, 0])
                    )
                    root.send_event(ev, event_mask=mask)

                display.flush()
            return True
        except Exception as e:
            raise Exception(f"更改窗口状态失败: {e}")
    
    def check_window_exists(self, window_title):
        """检查窗口是否存在"""
        # 在检查前稍作延迟，以便窗口状态发生变化（例如关闭命令后）
        time.sleep(0.2) 
        try:
            if not XLIB_AVAILABLE:
                return False
            
            print(f"检查窗口是否存在：{window_title}...")
            
            # 尝试使用主要机制查找窗口
            # _find_window_by_title will raise an exception if not found after its search.
            self._find_window_by_title(window_title)
            return True
        except Exception:
            # If _find_window_by_title fails, it means it couldn't find it via Xlib directly.
            # Now, try xdotool as a fallback.
            pass # 继续执行，以使用 xdotool 回退

        try:
            # 确保 window_title 为适用于命令行的简单字符串
            safe_title = str(window_title)
            # xdotool search 返回码：找到时为 0，未找到时为 1
            # It also prints the window ID(s) to stdout.
            result = subprocess.run(['xdotool', 'search', '--name', safe_title], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=2)
            # Check if return code is 0 and stdout is not empty (i.e., at least one window ID was printed)
            return result.returncode == 0 and result.stdout.strip() != b''
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # xdotool failed or not found
            return False
        except Exception:
            # Any other exception during xdotool execution
            return False
    
    def get_window_size(self, window_title):
        """获取窗口大小"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法获取窗口大小")

            # 先获取窗口 ID
            temp_xlib_window = self._find_window_by_title(window_title)
            if not temp_xlib_window:
                 raise Exception(f"找不到窗口 (for get_window_size): {window_title}")
            window_id = temp_xlib_window.id

            # 现在在新的受管理显示连接上下文中操作
            with x11_display_connection() as (display, root):
                if not display or not root:
                    raise Exception("无法连接到X11显示服务器 (get_window_size)")

                window_on_current_display = display.create_resource_object('window', window_id)
                geometry = window_on_current_display.get_geometry()
            
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

            temp_xlib_window_for_id = self._find_window_by_title(window_title)
            if not temp_xlib_window_for_id:
                raise Exception(f"找不到窗口 (for resize_window): {window_title}")
            window_id_to_resize = temp_xlib_window_for_id.id

            with x11_display_connection() as (display, root):
                if not display or not root:
                    raise Exception("无法连接到X11显示服务器 (resize_window)")

                window_to_resize_obj = display.create_resource_object('window', window_id_to_resize)
                
                # Ensure width and height are integers
                w = int(width)
                h = int(height)

                window_to_resize_obj.configure(width=w, height=h)
                display.flush()
            return True
        except Exception as e:
            raise Exception(f"调整窗口大小失败: {e}")
    
    def move_window(self, window_title, x, y):
        """移动窗口位置"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法移动窗口位置")
            # 获取窗口 ID
            temp_window = self._find_window_by_title(window_title)
            if not temp_window:
                raise Exception(f"找不到窗口 (for move_window): {window_title}")
            window_id = temp_window.id

            # 在新的 X11 连接上下文中移动窗口
            with x11_display_connection() as (display, root):
                if not display or not root:
                    raise Exception("无法连接到X11显示服务器 (move_window)")
                window = display.create_resource_object('window', window_id)
                window.configure(x=x, y=y)
                display.flush()
            return True
        except Exception as e:
            raise Exception(f"移动窗口位置失败: {e}")
    
    def set_window_topmost(self, window_title, is_topmost):
        """设置窗口置顶"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法设置窗口置顶")

            # 获取窗口 ID
            temp_window = self._find_window_by_title(window_title)
            if not temp_window:
                raise Exception(f"找不到窗口 (for set_window_topmost): {window_title}")
            window_id = temp_window.id

            # 在新的 X11 连接上下文中执行置顶操作
            with x11_display_connection() as (display, root):
                if not display or not root:
                    raise Exception("无法连接到X11显示服务器 (set_window_topmost)")

                # 创建窗口资源对象
                # client message 通常发送到 root 窗口
                wm_state = display.intern_atom('_NET_WM_STATE')
                above_atom = display.intern_atom('_NET_WM_STATE_ABOVE')
                action = 1 if is_topmost else 0
                ev = event.ClientMessage(
                    window=root,
                    client_type=wm_state,
                    data=(32, [action, above_atom, 0, 0, 0])
                )
                mask = Xlib.X.SubstructureRedirectMask | Xlib.X.SubstructureNotifyMask
                root.send_event(ev, event_mask=mask)
                display.flush()
            return True
        except Exception as e:
            raise Exception(f"设置窗口置顶失败: {e}")
    
    def get_window_class_name(self, window_title):
        """获取窗口类名"""
        try:
            if not XLIB_AVAILABLE:
                raise Exception("Xlib不可用，无法获取窗口类名")
            # 获取窗口 ID
            temp_window = self._find_window_by_title(window_title)
            if not temp_window:
                raise Exception(f"找不到窗口 (for get_window_class_name): {window_title}")
            window_id = temp_window.id

            # 在新的 X11 连接上下文中获取类名
            with x11_display_connection() as (display, root):
                if not display or not root:
                    raise Exception("无法连接到X11显示服务器 (get_window_class_name)")
                window = display.create_resource_object('window', window_id)
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
            # 在新的 X11 连接上下文中获取 PID
            with x11_display_connection() as (display, root):
                if not display or not root:
                    return None
                pid_atom = display.intern_atom('_NET_WM_PID')
                window_obj = display.create_resource_object('window', window.id)
                pid_prop = window_obj.get_property(pid_atom, Xlib.X.AnyPropertyType, 0, 1)
                if pid_prop and pid_prop.value:
                    return pid_prop.value[0]
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
        if not self.ATSPI_AVAILABLE: # 检查此实例是否应使用AT-SPI
            print("LINFO: AT-SPI support is explicitly disabled in this handler instance. Cannot use AT-SPI for element finding.")
            raise Exception("AT-SPI_DISABLED_BY_HANDLER")

        if not ATSPI_AVAILABLE: # 这是全局Python绑定的可用性检查
            print("LERROR: AT-SPI Python bindings (gi.repository.Atspi) are not imported/available.")
            raise Exception("AT-SPI_BINDINGS_NOT_AVAILABLE")
        
        # 检查桌面是否可访问，这可以更早地捕获AT-SPI总线问题
        try:
            desktop = Atspi.get_desktop(0)
            if not desktop:
                print("LERROR: Failed to get AT-SPI desktop (desktop is None). Accessibility bus may not be running.")
                raise Exception("AT-SPI_DESKTOP_UNAVAILABLE")
            # 如果可行且快速，可添加 child_count 或 应用程序名称检查
        except Exception as e:
            print(f"LERROR: Critical AT-SPI error during desktop access: {e}. Accessibility bus may not be running or accessible.")
            raise Exception(f"AT-SPI_BUS_ERROR: {e}")

        cache_key = f"{locator}_{timeout}"
        if cache_key in self.element_cache:
            element = self.element_cache[cache_key]
            try:
                element.get_name() # Simple validation
                return element
            except Exception:
                del self.element_cache[cache_key]
        
        locator_type, locator_value = parse_locator(locator)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Re-fetch desktop in loop in case it becomes available, though initial check is better
                current_desktop = Atspi.get_desktop(0) 
                if not current_desktop:
                    time.sleep(0.5)
                    continue

                for app_index in range(current_desktop.get_child_count()):
                    app = current_desktop.get_child_at_index(app_index)
                    if not app: continue
                    for window_index in range(app.get_child_count()):
                        window = app.get_child_at_index(window_index)
                        if not window: continue
                        element = self._find_element_recursive(window, locator_type, locator_value)
                        if element:
                            self.element_cache[cache_key] = element
                            return element
            except Exception as e_inner_loop:
                # 记录循环中的小错误，但不立即使整个搜索失败
                # print(f"LDEBUG: AT-SPI search inner loop exception: {e_inner_loop}")
                pass 
            
            time.sleep(0.5)
        
        print(f"LWARN: Element not found via AT-SPI within {timeout}s: {locator}")
        raise Exception(f"AT-SPI_ELEMENT_NOT_FOUND: {locator}")
    
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
            if activate_window:
                # 获取元素所在窗口
                window_title = self._get_window_title_from_locator(locator)
                if window_title:
                    self.set_active_window(window_title)
            
            # 首先尝试使用AT-SPI点击
            if self.ATSPI_AVAILABLE:
                try:
                    element = self._find_accessible_element(locator, time_out)
                    if element:
                        # 获取元素的屏幕坐标
                        bbox = element.get_extents(Atspi.CoordType.SCREEN)
                        x, y = self._calculate_click_coords(bbox.x, bbox.y, bbox.width, bbox.height, cursor_position, x_offset, y_offset)
                        
                        # 点击元素
                        self._perform_mouse_click(x, y, mouse_button, click_type, modifier_keys, smooth_move)
                        return True
                except Exception as e:
                    print(f"AT-SPI点击失败: {e}，尝试备用方法")
            
            # 备用方法：使用元素边界进行点击
            try:
                # 获取元素边界
                bounds = self.get_element_bounds(locator, "screen", time_out)
                if bounds:
                    x, y = self._calculate_click_coords(bounds["x"], bounds["y"], bounds["width"], bounds["height"], cursor_position, x_offset, y_offset)
                    
                    # 点击元素
                    self._perform_mouse_click(x, y, mouse_button, click_type, modifier_keys, smooth_move)
                    return True
            except Exception as e:
                print(f"边界点击失败: {e}，尝试xdotool方法")
            
            # 最后尝试使用xdotool定位并点击
            try:
                parsed_locator = parse_locator(locator)
                locator_type, locator_value = parsed_locator
                
                # 仅对某些类型的定位器尝试xdotool
                if locator_type in ["name", "class", "id"]:
                    cmd = ["xdotool", "search", "--name", locator_value, "click", "1"]
                    if mouse_button == "right":
                        cmd[-1] = "3"
                    elif mouse_button == "middle":
                        cmd[-1] = "2"
                    
                    subprocess.run(cmd, check=False, stderr=subprocess.DEVNULL)
                    return True
            except Exception:
                pass
                
            raise Exception(f"点击元素失败: 无法找到或点击元素 {locator}")
        except Exception as e:
            raise Exception(f"点击元素失败: {e}")
            
    def _get_window_title_from_locator(self, locator):
        """从定位器获取窗口标题"""
        # 尝试从locator中提取窗口信息
        try:
            parsed_locator = parse_locator(locator)
            if parsed_locator[0] == "window":
                return parsed_locator[1]
        except Exception:
            pass
        return None
        
    def _calculate_click_coords(self, x, y, width, height, cursor_position, x_offset, y_offset):
        """计算点击坐标"""
        if cursor_position == "center":
            click_x = x + width // 2
            click_y = y + height // 2
        elif cursor_position == "top-left":
            click_x = x
            click_y = y
        elif cursor_position == "top-right":
            click_x = x + width
            click_y = y
        elif cursor_position == "bottom-left":
            click_x = x
            click_y = y + height
        elif cursor_position == "bottom-right":
            click_x = x + width
            click_y = y + height
        else:
            click_x = x + width // 2
            click_y = y + height // 2
        
        return click_x + x_offset, click_y + y_offset
        
    def _perform_mouse_click(self, x, y, mouse_button, click_type, modifier_keys, smooth_move):
        """执行鼠标点击"""
        # 准备修饰键
        mods = []
        if modifier_keys:
            for key in modifier_keys:
                pyautogui.keyDown(key)
                mods.append(key)
        
        try:
            # 移动鼠标
            if smooth_move:
                pyautogui.moveTo(x, y, duration=0.5)
            else:
                pyautogui.moveTo(x, y)
            
            # 执行点击
            button = mouse_button
            if button == "left":
                button = "left"
            elif button == "right":
                button = "right"
            elif button == "middle":
                button = "middle"
            
            if click_type == "double":
                pyautogui.doubleClick(button=button)
            elif click_type == "right":
                pyautogui.rightClick()
            else:
                pyautogui.click(button=button)
        finally:
            # 释放修饰键
            for key in reversed(mods):
                pyautogui.keyUp(key)
    
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
        """获取元素 - 尝试AT-SPI，如果禁用或失败，尝试非AT-SPI回退。"""
        try:
            # 优先尝试 AT-SPI (如果在此handler实例中启用)
            # _find_accessible_element 会在 self.ATSPI_AVAILABLE 为 False 时抛出 AT-SPI_DISABLED_BY_HANDLER
            element_atspi = self._find_accessible_element(locator, time_out) 
            
            # 如果上面的调用没有因为AT-SPI禁用而抛出异常，说明AT-SPI被尝试了
            coords = element_atspi.get_extents(Atspi.CoordType.SCREEN)
            return {
                "name": element_atspi.get_name(),
                "role": element_atspi.get_role_name(),
                "text": element_atspi.get_text(0, -1) if hasattr(element_atspi, 'get_text') else "",
                "rectangle": {
                    "x": coords.x,
                    "y": coords.y,
                    "width": coords.width,
                    "height": coords.height
                },
                "states": [state.name for state in element_atspi.get_state_set()]
            }
        except Exception as e:
            exception_type = str(e)
            non_atspi_fallback_possible = True

            if exception_type == "AT-SPI_DISABLED_BY_HANDLER":
                print(f"LINFO: get_element - AT-SPI is disabled by handler. Will attempt non-AT-SPI methods for locator: {locator}")
            elif exception_type in ["AT-SPI_BINDINGS_NOT_AVAILABLE", "AT-SPI_DESKTOP_UNAVAILABLE", "AT-SPI_BUS_ERROR"]:
                print(f"LWARN: get_element - AT-SPI system issue ({exception_type}). Will attempt non-AT-SPI methods for locator: {locator}")
            elif exception_type.startswith("AT-SPI_ELEMENT_NOT_FOUND"):
                print(f"LINFO: get_element - Element not found via AT-SPI. Will attempt non-AT-SPI methods for locator: {locator}")
            else:
                # 对于其他未知AT-SPI错误或完全无关的错误，可能不适合回退
                print(f"LERROR: get_element - Unexpected error during AT-SPI attempt: {e}. Non-AT-SPI fallback may not be attempted or may fail.")
                non_atspi_fallback_possible = False # Or decide based on error type

            if non_atspi_fallback_possible:
                print(f"LINFO: get_element - Attempting non-AT-SPI fallback for: {locator}")
                # 非AT-SPI后备逻辑：
                # 这部分非常具有挑战性，因为不通过可访问性接口获取通用元素信息很困难。
                # 这里的实现将非常基础，主要依赖xdotool（如果可用）进行窗口级的操作或非常简单的名称匹配。
                try:
                    parsed_locator = parse_locator(locator)
                    locator_type, locator_value = parsed_locator

                    if locator_type == "window" or locator_type == "title": # 针对窗口标题
                        # 尝试用 xdotool 找到窗口并获取其 geometry
                        # 这需要系统中安装了 xdotool
                        cmd = ['xdotool', 'search', '--name', locator_value, 'getwindowgeometry', '%w %h %x %y']
                        process = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=2)
                        if process.returncode == 0 and process.stdout:
                            lines = process.stdout.strip().split('\\n') # xdotool might give multiple if names match
                            # For simplicity, take the first one, or implement more robust parsing
                            if lines:
                                parts = lines[0].split() # Expecting W H X Y
                                if len(parts) == 4:
                                    return {
                                        "name": locator_value, # Best guess
                                        "role": "window",    # Assumption
                                        "text": locator_value,
                                        "rectangle": {"x": int(parts[2]), "y": int(parts[3]), "width": int(parts[0]), "height": int(parts[1])},
                                        "states": ["visible"] # Assumption
                                    }
                    # 其他类型的定位器 (name, class, id for non-window elements) 
                    # 在没有 AT-SPI 的情况下很难可靠地获取。
                    # 可以尝试基于图像识别 (pyautogui) 或非常具体的 xdotool 命令，但通用性差。
                    print(f"LWARN: get_element - Non-AT-SPI fallback for locator type '{locator_type}' is very limited or not implemented.")
                except FileNotFoundError:
                    print("LERROR: get_element non-AT-SPI fallback - xdotool not found.")
                except subprocess.TimeoutExpired:
                    print("LWARN: get_element non-AT-SPI fallback - xdotool command timed out.")
                except Exception as ne:
                    print(f"LERROR: get_element non-AT-SPI fallback failed for '{locator}': {ne}")
            
            # 如果AT-SPI尝试失败（无论何种原因），并且非AT-SPI后备也失败或不适用
            raise Exception(f"获取元素失败 (get_element最终失败): {locator}. Original AT-SPI error (if any): {e if 'element_atspi' not in locals() else 'AT-SPI path attempted but failed differently'}")
    
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