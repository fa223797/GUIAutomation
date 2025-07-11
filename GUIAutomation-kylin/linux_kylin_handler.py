import os
import time
from linux_handler import LinuxHandler

class LinuxKylinHandler(LinuxHandler):
    
    def __init__(self):
        """初始化麒麟kylin，加载专属配置并检查辅助功能服务"""
        super().__init__()
        # 麒麟系统专属配置
        self.kylin_specific_config = {
            "accessibility_service": "/usr/bin/kylin-accessibility"
        }
        
        # 检查麒麟系统辅助功能是否已启用
        self._check_kylin_accessibility()
    
    def _check_kylin_accessibility(self):
        """检查麒麟特有的辅助功能是否启用"""
        try:
            if os.path.exists(self.kylin_specific_config["accessibility_service"]):
                # 确保麒麟辅助功能服务处于运行状态
                os.system(f"{self.kylin_specific_config['accessibility_service']} --check > /dev/null 2>&1")
        except Exception:
            pass  # 忽略异常，自动回退到标准Linux处理方式
            
