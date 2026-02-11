import sys
import asyncio
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QMenu
from PyQt6.QtCore import Qt, QTimer, QPoint, QSharedMemory, pyqtSignal
from PyQt6.QtGui import QFont, QAction
import qtawesome as qta

import os
import json
from bluetooth_engine import BluetoothEngine
from PyQt6.QtCore import QSettings

class YuBudsWidget(QWidget):
    # 定义跨线程信号：接口连接状态(bool), 电量数值(object)
    data_signal = pyqtSignal(bool, object)

    def __init__(self):
        super().__init__()
        print("[V2.1-Live] 正在启动 UI (支持位置记忆)...")
        if getattr(sys, 'frozen', False):
            # 打包后的 .exe 目录
            base_dir = os.path.dirname(sys.executable)
        else:
            # 原始脚本目录
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.config_path = os.path.join(base_dir, "config.json")
        self.engine = BluetoothEngine(target_name="Mijia Glasses Lite")
        self.init_ui()
        
        # 加载记忆位置
        self.load_settings()
        
        self.data_signal.connect(self.update_ui_safe)
        self.drag_position = QPoint()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.trigger_refresh)
        self.timer.start(5000)
        self.trigger_refresh()

    def init_ui(self):
        # 1. 窗口基础设置
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 2. 胶囊形状容器
        self.container = QWidget()
        self.container.setObjectName("capsule")
        self.container.setFixedSize(110, 36)
        # 修复点：确保样式表语法严谨，移除无效的 border_radius 警告
        self.container.setStyleSheet("""
            #capsule {
                background-color: rgba(30, 30, 30, 200);
                border-radius: 18px;
                border: 1px solid rgba(255, 255, 255, 40);
            }
        """)
        
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        
        # 3. 图标
        self.icon_label = QLabel()
        self.icon_label.setPixmap(qta.icon('fa5s.headset', color='white').pixmap(16, 16))
        self.icon_label.setStyleSheet("background: transparent; border: none;")
        
        # 4. 电量文本
        self.battery_text = QLabel("--%")
        self.battery_text.setFont(QFont("微软雅黑", 10, QFont.Weight.Bold))
        self.battery_text.setStyleSheet("color: white; background: transparent; border: none;")
        
        # 5. 用户关注的“小圆点”
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet("background-color: #555555; border-radius: 4px; border: none;")
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.battery_text, 1)
        layout.addWidget(self.status_dot)
        
        main_layout.addWidget(self.container)
        self.setFixedSize(120, 46)

    def trigger_refresh(self):
        """在后台线程池中运行扫描逻辑，防止 UI 卡死"""
        if event_loop and event_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.async_scan_task(), event_loop)

    async def async_scan_task(self):
        """后台异步任务：获取电量并发送信号"""
        try:
            res = await self.engine.get_device_info()
            print(f"[V2.1-Live] 扫描结果: {res}")
            
            # 策略：只要抓到了电量，就认为是在线
            is_active = res.get("battery") is not None
            battery_val = res.get("battery")
            
            # 发射信号，安全回传给主线程 UI
            self.data_signal.emit(is_active, battery_val)
        except Exception as e:
            print(f"[V2.1-Live] 扫描出错: {e}")

    def update_ui_safe(self, is_active, battery):
        """【主线程执行】安全更新 UI 元素"""
        print(f"[V2.1-Live] UI 正在更新... 在线={is_active}, 电量={battery}")
        if is_active:
            # 状态灯变绿 (2ECC71 是漂亮的亮绿色)
            self.status_dot.setStyleSheet("background-color: #2ECC71; border-radius: 4px; border: none;")
            self.battery_text.setText(f"{battery}%")
            self.battery_text.setStyleSheet("color: #FFFFFF; background: transparent;")
        else:
            # 状态灯变红
            self.status_dot.setStyleSheet("background-color: #E74C3C; border-radius: 4px; border: none;")
            self.battery_text.setText("Off")
            self.battery_text.setStyleSheet("color: #888888; background: transparent;")

    # --- 交互事件 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.save_settings()

    def save_settings(self):
        """保存当前位置到本地"""
        try:
            config = {"x": self.x(), "y": self.y()}
            with open(self.config_path, "w") as f:
                json.dump(config, f)
        except: pass

    def load_settings(self):
        """加载记忆的位置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    self.move(config.get("x", 100), config.get("y", 100))
            else:
                # 默认初始位置
                geom = QApplication.primaryScreen().geometry()
                self.move(geom.width() - 140, geom.height() - 120)
        except: pass

    def toggle_autostart(self, checked):
        """控制开机自启动"""
        settings = QSettings(r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run", QSettings.Format.NativeFormat)
        
        # 优化点：如果有 VBS 脚本，自启动就关联 VBS，这样开机就没有黑框
        vbs_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "启动_YuBuds(无黑框).vbs")
        
        if checked:
            if os.path.exists(vbs_path):
                # 关联脚本
                target = f'wscript.exe "{vbs_path}"'
            else:
                # 关联原程序 (作为兜底)
                target = f'"{os.path.abspath(sys.argv[0])}"'
            settings.setValue("YuBuds", target)
        else:
            settings.remove("YuBuds")

    def is_autostart_enabled(self):
        settings = QSettings(r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run", QSettings.Format.NativeFormat)
        return settings.contains("YuBuds")

    def show_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { 
                background: #222; 
                color: white; 
                border: 1px solid #444; 
                border-radius: 5px;
            } 
            QMenu::item:selected { 
                background: #444; 
            }
        """)
        
        # 蓝牙设置
        act_set = QAction(" 蓝牙设置", self)
        act_set.triggered.connect(lambda: asyncio.run_coroutine_threadsafe(self.engine.open_bluetooth_settings(), event_loop))
        
        # --- 麦克风相关功能 ---
        act_mic_set = QAction(" 麦克风设置", self)
        act_mic_set.triggered.connect(lambda: asyncio.run_coroutine_threadsafe(self.engine.open_mic_settings(), event_loop))
        
        # 自启动选项
        act_auto = QAction(" 随开机启动", self)
        act_auto.setCheckable(True)
        act_auto.setChecked(self.is_autostart_enabled())
        act_auto.triggered.connect(self.toggle_autostart)

        # 刷新与退出
        act_ref = QAction(" 立即刷新", self)
        act_ref.triggered.connect(self.trigger_refresh)
        
        act_exit = QAction(" 退出程序", self)
        act_exit.triggered.connect(QApplication.instance().quit)
        
        menu.addAction(act_set)
        menu.addSeparator()
        menu.addAction(act_mic_set)
        menu.addAction(act_auto)
        menu.addSeparator()
        menu.addAction(act_ref)
        menu.addAction(act_exit)
        menu.exec(pos)

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 防止重复启动 (使用 V3 锁隔离旧版)
    lock = QSharedMemory("YuBuds_V3_FINAL_LOCK")
    if not lock.create(1):
        if not lock.attach():
            print("="*50)
            print("【强力警告】旧版 YuBuds 进程仍在后台！")
            print("请按 Ctrl+C 关闭当前窗口，并手动结束任务管理器中的 python 进程。")
            print("="*50)
            sys.exit(0)
    
    print("="*50)
    print("    YuBuds V3.0 (最终强力修复版) 已就绪")
    print("    实时电量同步已激活")
    print("="*50)
            
    # 初始化异步循环
    event_loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_loop, args=(event_loop,), daemon=True)
    t.start()
    
    # 启动 UI (位置加载已在 YuBudsWidget 内部处理)
    widget = YuBudsWidget()
    widget.show()
    
    sys.exit(app.exec())
