import re

def parse_locator(locator):
    """
    解析定位字符串，返回定位类型和值
    例如: "id:button1" -> ("id", "button1")
    """
    if not locator or ":" not in locator:
        raise ValueError(f"无效的定位表达式: {locator}，格式应为 'type:value'")
    
    locator_type, locator_value = locator.split(":", 1)
    locator_type = locator_type.lower().strip()
    locator_value = locator_value.strip()
    
    return locator_type, locator_value

class ElementLocator:
    """元素定位引擎，支持多种定位策略"""
    
    def __init__(self):
        # 支持的定位类型
        self.supported_locators = {
            "id": self._find_by_id,
            "name": self._find_by_name,
            "class": self._find_by_class,
            "xpath": self._find_by_xpath,
            "css": self._find_by_css,
            "text": self._find_by_text,
            "tag": self._find_by_tag,
            "control_type": self._find_by_control_type
        }
    
    def find_element(self, context, locator):
        """
        在给定上下文中查找元素
        
        参数:
        context: 元素查找的上下文
        locator: 定位表达式，格式为 "type:value"
        
        返回:
        找到的元素对象
        """
        locator_type, locator_value = parse_locator(locator)
        
        if locator_type not in self.supported_locators:
            raise ValueError(f"不支持的定位类型: {locator_type}")
        
        # 调用相应的定位方法
        finder = self.supported_locators[locator_type]
        return finder(context, locator_value)
    
    def _find_by_id(self, context, value):
        """通过ID查找元素"""
        # 具体实现取决于上下文的类型，这里提供一个通用模板
        try:
            if hasattr(context, 'find_element_by_id'):
                # Selenium 风格
                return context.find_element_by_id(value)
            elif hasattr(context, 'child_window'):
                # Pywinauto 风格
                return context.child_window(auto_id=value)
            elif hasattr(context, 'findById'):
                # 自定义接口
                return context.findById(value)
            else:
                raise NotImplementedError("当前上下文不支持通过ID查找")
        except Exception as e:
            raise Exception(f"通过ID '{value}' 查找元素失败: {e}")
    
    def _find_by_name(self, context, value):
        """通过名称查找元素"""
        try:
            if hasattr(context, 'find_element_by_name'):
                # Selenium 风格
                return context.find_element_by_name(value)
            elif hasattr(context, 'child_window'):
                # Pywinauto 风格
                return context.child_window(name=value)
            elif hasattr(context, 'findByName'):
                # 自定义接口
                return context.findByName(value)
            else:
                raise NotImplementedError("当前上下文不支持通过名称查找")
        except Exception as e:
            raise Exception(f"通过名称 '{value}' 查找元素失败: {e}")
    
    def _find_by_class(self, context, value):
        """通过类名查找元素"""
        try:
            if hasattr(context, 'find_element_by_class_name'):
                # Selenium 风格
                return context.find_element_by_class_name(value)
            elif hasattr(context, 'child_window'):
                # Pywinauto 风格
                return context.child_window(class_name=value)
            elif hasattr(context, 'findByClass'):
                # 自定义接口
                return context.findByClass(value)
            else:
                raise NotImplementedError("当前上下文不支持通过类名查找")
        except Exception as e:
            raise Exception(f"通过类名 '{value}' 查找元素失败: {e}")
    
    def _find_by_xpath(self, context, value):
        """通过XPath查找元素"""
        try:
            if hasattr(context, 'find_element_by_xpath'):
                # Selenium 风格
                return context.find_element_by_xpath(value)
            elif hasattr(context, 'findByXPath'):
                # 自定义接口
                return context.findByXPath(value)
            else:
                raise NotImplementedError("当前上下文不支持通过XPath查找")
        except Exception as e:
            raise Exception(f"通过XPath '{value}' 查找元素失败: {e}")
    
    def _find_by_css(self, context, value):
        """通过CSS选择器查找元素"""
        try:
            if hasattr(context, 'find_element_by_css_selector'):
                # Selenium 风格
                return context.find_element_by_css_selector(value)
            elif hasattr(context, 'findByCss'):
                # 自定义接口
                return context.findByCss(value)
            else:
                raise NotImplementedError("当前上下文不支持通过CSS选择器查找")
        except Exception as e:
            raise Exception(f"通过CSS选择器 '{value}' 查找元素失败: {e}")
    
    def _find_by_text(self, context, value):
        """通过文本内容查找元素"""
        try:
            if hasattr(context, 'find_element_by_link_text'):
                # Selenium 风格
                return context.find_element_by_link_text(value)
            elif hasattr(context, 'child_window'):
                # Pywinauto 风格
                return context.child_window(title=value)
            elif hasattr(context, 'findByText'):
                # 自定义接口
                return context.findByText(value)
            else:
                raise NotImplementedError("当前上下文不支持通过文本内容查找")
        except Exception as e:
            raise Exception(f"通过文本内容 '{value}' 查找元素失败: {e}")
    
    def _find_by_tag(self, context, value):
        """通过标签名查找元素"""
        try:
            if hasattr(context, 'find_element_by_tag_name'):
                # Selenium 风格
                return context.find_element_by_tag_name(value)
            elif hasattr(context, 'findByTag'):
                # 自定义接口
                return context.findByTag(value)
            else:
                raise NotImplementedError("当前上下文不支持通过标签名查找")
        except Exception as e:
            raise Exception(f"通过标签名 '{value}' 查找元素失败: {e}")
    
    def _find_by_control_type(self, context, value):
        """通过控件类型查找元素"""
        try:
            if hasattr(context, 'child_window'):
                # Pywinauto 风格
                return context.child_window(control_type=value)
            elif hasattr(context, 'findByControlType'):
                # 自定义接口
                return context.findByControlType(value)
            else:
                raise NotImplementedError("当前上下文不支持通过控件类型查找")
        except Exception as e:
            raise Exception(f"通过控件类型 '{value}' 查找元素失败: {e}") 