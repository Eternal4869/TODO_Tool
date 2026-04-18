import sys
import socket
import datetime
import json
import os
import subprocess
import shutil
import difflib
from pathlib import Path
import psutil
import netifaces
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# ==================== IP 地址显示组件 ====================
class IPAddressWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_ip_addresses()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # 标题
        title_label = QLabel("🌐 本机 IP 地址")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #0078D7;")
        main_layout.addWidget(title_label)
        
        # IP 列表容器 - 使用 QHBoxLayout 代替 QFlowLayout
        self.ip_container = QWidget()
        self.ip_layout = QHBoxLayout(self.ip_container)
        self.ip_layout.setSpacing(5)
        self.ip_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.ip_container)
        
        self.setLayout(main_layout)
    
    def load_ip_addresses(self):
        # 清空现有 IP 标签
        while self.ip_layout.count():
            item = self.ip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        ip_list = self.get_all_ips()
        
        if not ip_list:
            label = QLabel("未找到可用 IP 地址")
            label.setStyleSheet("color: #999; padding: 5px;")
            self.ip_layout.addWidget(label)
            return
        
        for ip_info in ip_list:
            ip_btn = self.create_ip_button(ip_info)
            self.ip_layout.addWidget(ip_btn)
    
    def get_all_ips(self):
        """获取所有网络接口的 IP 地址"""
        ip_list = []
        try:
            # 使用 netifaces 获取所有网络接口
            interfaces = netifaces.interfaces()
            for iface in interfaces:
                try:
                    addrs = netifaces.ifaddresses(iface)
                    if netifaces.AF_INET in addrs:
                        for link in addrs[netifaces.AF_INET]:
                            ip = link.get('addr', '')
                            if ip and ip != '127.0.0.1':
                                ip_list.append({'ip': ip, 'interface': iface, 'type': 'IPv4'})
                    if netifaces.AF_INET6 in addrs:
                        for link in addrs[netifaces.AF_INET6]:
                            ip = link.get('addr', '')
                            if ip and ip != '::1' and '%' not in ip:
                                ip_list.append({'ip': ip, 'interface': iface, 'type': 'IPv6'})
                except Exception:
                    continue
            
            # 如果 netifaces 没有获取到，尝试使用 psutil
            if not ip_list:
                addrs = psutil.net_if_addrs()
                for interface_name, interface_addresses in addrs.items():
                    for addr in interface_addresses:
                        if addr.family == socket.AF_INET:
                            if addr.address and addr.address != '127.0.0.1':
                                ip_list.append({'ip': addr.address, 'interface': interface_name, 'type': 'IPv4'})
                        elif addr.family == socket.AF_INET6:
                            if addr.address and addr.address != '::1' and '%' not in addr.address:
                                ip_list.append({'ip': addr.address, 'interface': interface_name, 'type': 'IPv6'})
            
            # 最后尝试 socket 方法
            if not ip_list:
                host_name = socket.gethostname()
                addr_info = socket.getaddrinfo(host_name, None)
                for info in addr_info:
                    ip = info[4][0]
                    if ":" not in ip and ip != "127.0.0.1":
                        ip_list.append({'ip': ip, 'interface': 'default', 'type': 'IPv4'})
            
            # 如果还是没有，至少返回 localhost
            if not ip_list:
                ip_list.append({'ip': '127.0.0.1', 'interface': 'localhost', 'type': 'IPv4'})
                
        except Exception as e:
            ip_list.append({'ip': '127.0.0.1', 'interface': 'localhost', 'type': 'IPv4'})
        
        return ip_list
    
    def create_ip_button(self, ip_info):
        """创建 IP 地址按钮"""
        btn = QPushButton(f"{ip_info['ip']}")
        btn.setToolTip(f"接口：{ip_info['interface']}\n类型：{ip_info['type']}\n右键点击复制")
        btn.setStyleSheet("""
            QPushButton {
                background: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 4px;
                padding: 5px 10px;
                color: #1565c0;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #bbdefb;
                border: 1px solid #64b5f6;
            }
            QPushButton:pressed {
                background: #90caf9;
            }
        """)
        
        # 创建右键菜单
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(
            lambda pos, ip=ip_info['ip']: self.show_ip_context_menu(btn, ip, pos)
        )
        
        # 左键点击也复制
        btn.clicked.connect(lambda checked, ip=ip_info['ip']: self.copy_ip(ip))
        
        return btn
    
    def show_ip_context_menu(self, btn, ip, pos):
        """显示 IP 右键菜单"""
        menu = QMenu(self)
        copy_action = menu.addAction("📋 复制 IP 地址")
        copy_action.triggered.connect(lambda: self.copy_ip(ip))
        menu.exec_(btn.mapToGlobal(pos))
    
    def copy_ip(self, ip):
        """复制 IP 到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(ip)
        # 显示提示
        tip = QLabel(f"✓ 已复制：{ip}")
        tip.setStyleSheet("""
            background: #4CAF50;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
        """)
        tip.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        tip.show()
        QTimer.singleShot(1500, tip.close)


# ==================== 待办事项组件 ====================
class TodoItem(QWidget):
    def __init__(self, text, done, todo_id, seq, parent=None):
        super().__init__(parent)
        self.todo_id = todo_id
        self.is_done = done
        self.seq = seq
        self.setup_ui(text, done)
    
    def setup_ui(self, text, done):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        self.drag_label = QLabel("☰ ")
        self.drag_label.setCursor(Qt.OpenHandCursor)
        self.drag_label.setFixedSize(20, 20)
        self.drag_label.setAlignment(Qt.AlignCenter)
        self.drag_label.setStyleSheet("color: #666666; font-size: 16px; ")
        if done:
            self.drag_label.setText("🔒 ")
            self.drag_label.setStyleSheet("color: #cccccc; font-size: 14px; ")
            self.drag_label.setCursor(Qt.ArrowCursor)
        layout.addWidget(self.drag_label)
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(done)
        self.checkbox.setFixedSize(20, 20)
        layout.addWidget(self.checkbox)
        
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label.setStyleSheet("padding: 3px;")
        if done:
            self.label.setStyleSheet("color: #888888; text-decoration: line-through; padding: 3px;")
        layout.addWidget(self.label)
        
        # 编辑按钮
        self.edit_btn = QPushButton("✏️")
        self.edit_btn.setFixedSize(25, 25)
        self.edit_btn.setToolTip("编辑")
        self.edit_btn.setStyleSheet("""
            QPushButton { 
                background: #4fc3f7; 
                color: white; 
                border: none; 
                border-radius: 3px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #29b6f6;
            }
        """)
        layout.addWidget(self.edit_btn)
        
        self.del_btn = QPushButton("🗑️")
        self.del_btn.setFixedSize(25, 25)
        self.del_btn.setToolTip("删除")
        self.del_btn.setStyleSheet("""
            QPushButton { 
                background: #ff6b6b; 
                color: white; 
                border: none; 
                border-radius: 3px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #ee5a5a;
            }
        """)
        layout.addWidget(self.del_btn)
        
        # 设置整体样式
        self.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
            QWidget:hover {
                background: #f5f5f5;
                border: 1px solid #bdbdbd;
            }
        """)
        self.setLayout(layout)

# ==================== 快捷启动组件 ====================
class AppLauncherButton(QWidget):
    def __init__(self, name, path, icon="", parent=None):
        super().__init__(parent)
        self.name = name
        self.path = path
        self.setup_ui(icon)
    
    def setup_ui(self, icon):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignCenter)
        
        self.icon_label = QLabel("🚀 ")
        if icon and os.path.exists(icon):
            pixmap = QPixmap(icon).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
        else:
            self.icon_label.setStyleSheet("font-size: 48px; ")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(60, 60)
        layout.addWidget(self.icon_label)
        
        self.name_label = QLabel(self.name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumWidth(100)
        self.name_label.setStyleSheet("font-size: 12px; ")
        layout.addWidget(self.name_label)
        
        self.setStyleSheet("""
            QWidget {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            QWidget:hover {
                background: #e0e0e0;
                border: 1px solid #bbb;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.launch_app()
        super().mousePressEvent(event)

    def launch_app(self):
        try:
            if os.path.exists(self.path):
                subprocess.Popen([self.path])
            else:
                subprocess.Popen(self.path, shell=True)
        except Exception as e:
            QMessageBox.warning(self, "启动失败", f"无法启动 {self.name}\n\n错误：{e}")

# ==================== 文件抽取线程 ====================
class ExtractWorker(QThread):
    log_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int, int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, list_file, source_dir, dest_dir):
        super().__init__()
        self.list_file = list_file
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self._is_interrupted = False

    def run(self):
        try:
            if not os.path.exists(self.list_file):
                self.log_signal.emit(f"文件列表不存在：{self.list_file}", "ERROR")
                self.finished_signal.emit(False)
                return

            with open(self.list_file, 'r', encoding='utf-8') as f:
                file_list = [line.strip() for line in f if line.strip()]

            if not file_list:
                self.log_signal.emit("文件列表为空", "ERROR")
                self.finished_signal.emit(False)
                return

            total = len(file_list)
            success_count = 0
            fail_count = 0
            self.status_signal.emit(f"开始处理 {total} 个文件... ")

            for idx, relative_path in enumerate(file_list):
                if self._is_interrupted:
                    self.log_signal.emit("操作已中断", "INFO")
                    self.finished_signal.emit(False)
                    return

                src_path = os.path.join(self.source_dir, relative_path)
                dst_path = os.path.join(self.dest_dir, relative_path)
                self.progress_signal.emit(idx + 1, total)

                if not os.path.exists(src_path):
                    self.log_signal.emit(f"文件不存在：{relative_path}", "ERROR")
                    fail_count += 1
                    continue

                try:
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    shutil.copy2(src_path, dst_path)
                    self.log_signal.emit(f"✓ 成功：{relative_path}", "SUCCESS")
                    success_count += 1
                except Exception as e:
                    self.log_signal.emit(f"✗ 失败：{relative_path} - {str(e)}", "ERROR")
                    fail_count += 1

            self.status_signal.emit(f"完成！成功：{success_count}, 失败：{fail_count}")
            self.log_signal.emit(f"抽取完成！成功：{success_count}, 失败：{fail_count}", "INFO")
            self.finished_signal.emit(True)
        except Exception as e:
            self.log_signal.emit(f"发生错误：{str(e)}", "ERROR")
            self.finished_signal.emit(False)

    def stop(self):
        self._is_interrupted = True

# ==================== Git 日志查询线程 ====================
class GitLogWorker(QThread):
    """后台工作线程，执行 Git 命令，避免阻塞 UI"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, repo_path, author, start_time, end_time):
        super().__init__()
        self.repo_path = repo_path
        self.author = author
        self.start_time = start_time
        self.end_time = end_time

    def run(self):
        try:
            if not os.path.isdir(self.repo_path):
                raise FileNotFoundError(f"仓库路径不存在：{self.repo_path}")

            # 构建 git 命令
            cmd = [
                'git', 'log',
                f'--author={self.author}',
                f'--since={self.start_time}',
                f'--until={self.end_time}',
                '--name-only',
                '--format='
            ]

            # 执行命令
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )

            if result.returncode != 0:
                self.error.emit(f"Git 命令执行失败:\n{result.stderr}")
                return

            # 处理输出：模拟 sort | uniq
            files = result.stdout.splitlines()
            unique_files = sorted(list(set([f.strip() for f in files if f.strip()])))

            self.finished.emit(unique_files)

        except Exception as e:
            self.error.emit(str(e))

# ==================== Git 日志查询组件 ====================
class GitLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- 输入区域 ---
        input_group = QGroupBox("查询条件")
        input_layout = QVBoxLayout()

        # 1. 仓库路径
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("选择 Git 仓库根目录...")
        btn_browse = QPushButton("浏览")
        btn_browse.clicked.connect(self.browse_repo)
        path_layout.addWidget(QLabel("仓库路径:"))
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(btn_browse)
        input_layout.addLayout(path_layout)

        # 2. 用户名
        user_layout = QHBoxLayout()
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("例如：zhangsan 或 zhangsan@example.com")
        user_layout.addWidget(QLabel("作者用户名:"))
        user_layout.addWidget(self.user_input)
        input_layout.addLayout(user_layout)

        # 3. 时间范围
        time_layout = QHBoxLayout()
        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.start_time_edit.setDateTime(QDateTime.currentDateTime().addDays(-30))
        
        self.end_time_edit = QDateTimeEdit()
        self.end_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.end_time_edit.setDateTime(QDateTime.currentDateTime())

        time_layout.addWidget(QLabel("开始时间:"))
        time_layout.addWidget(self.start_time_edit)
        time_layout.addWidget(QLabel("结束时间:"))
        time_layout.addWidget(self.end_time_edit)
        input_layout.addLayout(time_layout)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # --- 按钮区域 ---
        btn_layout = QHBoxLayout()
        self.btn_search = QPushButton("开始查询")
        self.btn_search.clicked.connect(self.start_search)
        self.btn_search.setStyleSheet("font-weight: bold; padding: 8px 20px; background: #2196F3; color: white; border: none; border-radius: 4px;")
        
        self.btn_copy = QPushButton("一键复制结果")
        self.btn_copy.clicked.connect(self.copy_result)
        self.btn_copy.setStyleSheet("padding: 8px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px;")
        
        btn_layout.addWidget(self.btn_search)
        btn_layout.addWidget(self.btn_copy)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # --- 输出区域 ---
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setPlaceholderText("查询结果将显示在这里...")
        main_layout.addWidget(QLabel("文件列表:"))
        main_layout.addWidget(self.output_text)

        # --- 状态栏 ---
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: gray; font-size: 12px;")
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)

    def browse_repo(self):
        folder = QFileDialog.getExistingDirectory(self, "选择 Git 仓库目录")
        if folder:
            self.path_input.setText(folder)

    def start_search(self):
        repo_path = self.path_input.text().strip()
        author = self.user_input.text().strip()
        
        start_time = self.start_time_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end_time = self.end_time_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        if not repo_path:
            QMessageBox.warning(self, "警告", "请选择仓库路径")
            return
        if not author:
            QMessageBox.warning(self, "警告", "请输入作者用户名")
            return

        self.set_enabled(False)
        self.status_label.setText("正在查询中，请稍候...")
        self.output_text.clear()

        self.worker = GitLogWorker(repo_path, author, start_time, end_time)
        self.worker.finished.connect(self.on_search_finished)
        self.worker.error.connect(self.on_search_error)
        self.worker.start()

    def on_search_finished(self, files):
        self.set_enabled(True)
        if not files:
            self.status_label.setText("查询完成，未找到匹配的文件。")
            self.output_text.setPlainText("(无文件)")
        else:
            self.status_label.setText(f"查询完成，共找到 {len(files)} 个文件。")
            self.output_text.setPlainText("\n".join(files))

    def on_search_error(self, error_msg):
        self.set_enabled(True)
        self.status_label.setText("发生错误")
        QMessageBox.critical(self, "错误", error_msg)

    def copy_result(self):
        text = self.output_text.toPlainText()
        if not text or text == "(无文件)":
            QMessageBox.information(self, "提示", "没有可复制的内容")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.status_label.setText("已复制到剪贴板")
        QTimer.singleShot(2000, lambda: self.status_label.setText("就绪"))

    def set_enabled(self, enabled):
        self.btn_search.setEnabled(enabled)
        self.btn_copy.setEnabled(enabled)
        self.path_input.setEnabled(enabled)
        self.user_input.setEnabled(enabled)
        self.start_time_edit.setEnabled(enabled)
        self.end_time_edit.setEnabled(enabled)
        if enabled:
            QApplication.restoreOverrideCursor()
        else:
            QApplication.setOverrideCursor(Qt.WaitCursor)

# ==================== 文本对比组件（按行对比） ====================
class TextCompareWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lines1 = []
        self.lines2 = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 文件选择区
        file_layout = QHBoxLayout()
        
        file1_group = QGroupBox("文件 1")
        file1_layout = QHBoxLayout()
        self.file1_edit = QLineEdit()
        self.file1_edit.setPlaceholderText("选择第一个文件")
        btn_browse1 = QPushButton("浏览")
        btn_browse1.clicked.connect(lambda: self.browse_file(1))
        file1_layout.addWidget(self.file1_edit)
        file1_layout.addWidget(btn_browse1)
        file1_group.setLayout(file1_layout)
        
        file2_group = QGroupBox("文件 2")
        file2_layout = QHBoxLayout()
        self.file2_edit = QLineEdit()
        self.file2_edit.setPlaceholderText("选择第二个文件")
        btn_browse2 = QPushButton("浏览")
        btn_browse2.clicked.connect(lambda: self.browse_file(2))
        file2_layout.addWidget(self.file2_edit)
        file2_layout.addWidget(btn_browse2)
        file2_group.setLayout(file2_layout)
        
        file_layout.addWidget(file1_group)
        file_layout.addWidget(file2_group)
        layout.addLayout(file_layout)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        self.btn_compare = QPushButton("🔍 开始对比")
        self.btn_compare.clicked.connect(self.compare_files)
        self.btn_compare.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        control_layout.addWidget(self.btn_compare)
        
        self.btn_clear = QPushButton("🗑️ 清空")
        self.btn_clear.clicked.connect(self.clear_all)
        control_layout.addWidget(self.btn_clear)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 对比结果区
        result_group = QGroupBox("按行对比结果")
        result_layout = QVBoxLayout()
        
        compare_layout = QHBoxLayout()
        compare_layout.setSpacing(5)
        
        left_group = QGroupBox("文件 1")
        left_layout = QVBoxLayout()
        self.left_text = QTextEdit()
        self.left_text.setReadOnly(True)
        self.left_text.setFont(QFont("Consolas", 10))
        self.left_text.setStyleSheet("""
            QTextEdit {
                background: #ffffff;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        left_layout.addWidget(self.left_text)
        left_group.setLayout(left_layout)
        
        right_group = QGroupBox("文件 2")
        right_layout = QVBoxLayout()
        self.right_text = QTextEdit()
        self.right_text.setReadOnly(True)
        self.right_text.setFont(QFont("Consolas", 10))
        self.right_text.setStyleSheet("""
            QTextEdit {
                background: #ffffff;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        right_layout.addWidget(self.right_text)
        right_group.setLayout(right_layout)
        
        compare_layout.addWidget(left_group)
        compare_layout.addWidget(right_group)
        result_layout.addLayout(compare_layout)
        
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px; ")
        self.stats_label.setAlignment(Qt.AlignCenter)
        result_layout.addWidget(self.stats_label)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group) 
        
        legend_group = QGroupBox("图例说明")
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("🟦 <span style='color: #666;'>相同行</span>"))
        legend_layout.addWidget(QLabel("🟥 <span style='color: #666;'>文件 1 独有</span>"))
        legend_layout.addWidget(QLabel("🟩 <span style='color: #666;'>文件 2 独有</span>"))
        legend_layout.addStretch()
        legend_group.setLayout(legend_layout)
        layout.addWidget(legend_group)

    def browse_file(self, file_num):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文本文件", "", "文本文件 (*.txt);;所有文件 (*.*)")
        if file_path:
            if file_num == 1:
                self.file1_edit.setText(file_path)
            else:
                self.file2_edit.setText(file_path)

    def clear_all(self):
        self.file1_edit.clear()
        self.file2_edit.clear()
        self.left_text.clear()
        self.right_text.clear()
        self.stats_label.clear()
        self.lines1 = []
        self.lines2 = []

    def compare_files(self):
        file1 = self.file1_edit.text().strip()
        file2 = self.file2_edit.text().strip()
        
        if not file1 or not os.path.exists(file1):
            QMessageBox.warning(self, "错误", "请选择有效的文件 1！")
            return
        if not file2 or not os.path.exists(file2):
            QMessageBox.warning(self, "错误", "请选择有效的文件 2！")
            return
        
        try:
            with open(file1, 'r', encoding='utf-8') as f:
                self.lines1 = [line.rstrip('\n\r') for line in f.readlines()]
            with open(file2, 'r', encoding='utf-8') as f:
                self.lines2 = [line.rstrip('\n\r') for line in f.readlines()]
            
            diff = list(difflib.ndiff(self.lines1, self.lines2))
            
            same_count = 0
            remove_count = 0
            add_count = 0
            
            left_html = '<pre style="font-family: Consolas; font-size: 10px; line-height: 1.5;">'
            right_html = '<pre style="font-family: Consolas; font-size: 10px; line-height: 1.5;">'
            
            left_line_num = 0
            right_line_num = 0
            
            for line in diff:
                if line.startswith('  '):
                    content = self._escape_html(line[2:])
                    left_html += f'<span style="background: #e3f2fd;">{left_line_num + 1:4d} | {content}</span>\n'
                    right_html += f'<span style="background: #e3f2fd;">{right_line_num + 1:4d} | {content}</span>\n'
                    left_line_num += 1
                    right_line_num += 1
                    same_count += 1
                    
                elif line.startswith('- '):
                    content = self._escape_html(line[2:])
                    left_html += f'<span style="background: #ffcdd2; color: #c62828;">{left_line_num + 1:4d} | {content}</span>\n'
                    right_html += f'<span style="background: #f5f5f5; color: #999;">{" ":4s} |  </span>\n'
                    left_line_num += 1
                    remove_count += 1
                    
                elif line.startswith('+ '):
                    content = self._escape_html(line[2:])
                    left_html += f'<span style="background: #f5f5f5; color: #999;">{" ":4s} |  </span>\n'
                    right_html += f'<span style="background: #c8e6c9; color: #2e7d32;">{right_line_num + 1:4d} | {content}</span>\n'
                    right_line_num += 1
                    add_count += 1
            
            left_html += '</pre>'
            right_html += '</pre>'
            
            self.left_text.setHtml(left_html)
            self.right_text.setHtml(right_html)
            
            self.left_text.verticalScrollBar().valueChanged.connect(
                lambda v: self.right_text.verticalScrollBar().setValue(v)
            )
            self.right_text.verticalScrollBar().valueChanged.connect(
                lambda v: self.left_text.verticalScrollBar().setValue(v)
            )
            
            total1 = len(self.lines1)
            total2 = len(self.lines2)
            self.stats_label.setText(
                f"文件 1 总行数：{total1}  |  文件 2 总行数：{total2}  |   "
                f"相同：{same_count}  |  文件 1 独有：{remove_count}  |  文件 2 独有：{add_count}"
            )
            
        except Exception as e:
            self.left_text.setHtml(f'<span style="color: red;">错误：{str(e)}</span>')
            self.right_text.clear()
            self.stats_label.clear()

    def _escape_html(self, text):
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ==================== 主窗口 ====================
class DesktopTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_file = "todos.json"
        self.memo_file = "memo.txt"
        self.apps_file = "apps.json"
        self.todos = []
        self.sequence_counter = 0
        self.memo_timer = None
        self.drag_start_idx = None
        self.drag_start_pos = None
        self.dragged_widget = None
        self.apps = []
        self.extract_worker = None
        
        self.init_ui()
        self.load_todos()
        self.load_memo()
        self.load_apps()
        self.update_time()
        # IP 地址由 IPAddressWidget 组件自动加载

    def init_ui(self):
        self.setWindowTitle("个人效率小工具")
        self.setGeometry(100, 100, 900, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # === 顶部信息区 ===
        # 使用新的 IP 地址显示组件
        self.ip_widget = IPAddressWidget()
        main_layout.addWidget(self.ip_widget)
        
        separator_top = QFrame()
        separator_top.setFrameShape(QFrame.HLine)
        separator_top.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator_top)
        
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("font-family: Consolas; font-size: 14px; ")
        main_layout.addWidget(self.time_label)
        
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator1)
        
        # === 选项卡 ===
        self.tabs = QTabWidget()
        
        # 第一页：待办事项 + 备忘录
        self.todo_tab = QWidget()
        self.todo_tab_layout = QVBoxLayout(self.todo_tab)
        self.todo_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.todo_tab_layout.setSpacing(10)
        self.setup_todo_tab()
        self.tabs.addTab(self.todo_tab, "📋 待办事项")
        
        # 第二页：快捷启动
        self.apps_tab = QWidget()
        self.apps_tab_layout = QVBoxLayout(self.apps_tab)
        self.apps_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.apps_tab_layout.setSpacing(10)
        self.setup_apps_tab()
        self.tabs.addTab(self.apps_tab, "🚀 快捷启动")
        
        # 第三页：文件抽取
        self.extract_tab = QWidget()
        self.extract_tab_layout = QVBoxLayout(self.extract_tab)
        self.extract_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.extract_tab_layout.setSpacing(10)
        self.setup_extract_tab()
        self.tabs.addTab(self.extract_tab, "📁 文件抽取")
        
        # 第四页：文本对比（按行）
        self.compare_tab = TextCompareWidget()
        self.tabs.addTab(self.compare_tab, "📝 文本对比")
        
        # 第五页：Git 日志查询（新增）
        self.git_log_tab = GitLogWidget()
        self.tabs.addTab(self.git_log_tab, "🔍 Git 日志")
        
        main_layout.addWidget(self.tabs)
        
        # 底部操作区（仅待办事项页显示）
        self.control_widget = QWidget()
        control_layout = QHBoxLayout(self.control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("输入待办事项...")
        self.entry.returnPressed.connect(self.add_todo)
        control_layout.addWidget(self.entry, stretch=1)
        
        add_btn = QPushButton("添加待办")
        add_btn.clicked.connect(self.add_todo)
        control_layout.addWidget(add_btn)
        
        self.topmost_chk = QCheckBox("窗口置顶")
        self.topmost_chk.stateChanged.connect(self.toggle_topmost)
        control_layout.addWidget(self.topmost_chk)
        
        main_layout.addWidget(self.control_widget)

    def setup_todo_tab(self):
        todo_label = QLabel("📋 待办事项 (拖动 ☰ 排序)")
        todo_label.setStyleSheet("font-weight: bold; font-size: 14px; ")
        self.todo_tab_layout.addWidget(todo_label)
        
        self.todo_scroll = QScrollArea()
        self.todo_scroll.setWidgetResizable(True)
        self.todo_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.todo_content = QWidget()
        self.todo_layout = QVBoxLayout(self.todo_content)
        self.todo_layout.setAlignment(Qt.AlignTop)
        self.todo_layout.setSpacing(5)
        self.todo_scroll.setWidget(self.todo_content)
        self.todo_scroll.setMinimumHeight(200)
        self.todo_scroll.setMaximumHeight(250)
        self.todo_tab_layout.addWidget(self.todo_scroll)
        
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        self.todo_tab_layout.addWidget(separator2)
        
        memo_label = QLabel("📝 备忘录")
        memo_label.setStyleSheet("font-weight: bold; font-size: 14px; ")
        self.todo_tab_layout.addWidget(memo_label)
        
        self.memo_text = QTextEdit()
        self.memo_text.setFont(QFont("Consolas", 11))
        self.memo_text.setMinimumHeight(150)
        self.memo_text.setMaximumHeight(200)
        self.memo_text.textChanged.connect(self.on_memo_change)
        self.todo_tab_layout.addWidget(self.memo_text)
        
        self.memo_status = QLabel("")
        self.memo_status.setAlignment(Qt.AlignRight)
        self.memo_status.setStyleSheet("color: #888888; ")
        self.todo_tab_layout.addWidget(self.memo_status)

    def setup_apps_tab(self):
        header_layout = QHBoxLayout()
        apps_label = QLabel("🚀 快捷启动程序")
        apps_label.setStyleSheet("font-weight: bold; font-size: 14px; ")
        header_layout.addWidget(apps_label)
        header_layout.addStretch()
        
        add_app_btn = QPushButton("+ 添加程序")
        add_app_btn.clicked.connect(self.add_app)
        add_app_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        header_layout.addWidget(add_app_btn)
        self.apps_tab_layout.addLayout(header_layout)
        
        self.apps_scroll = QScrollArea()
        self.apps_scroll.setWidgetResizable(True)
        self.apps_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.apps_content = QWidget()
        self.apps_grid = QGridLayout(self.apps_content)
        self.apps_grid.setAlignment(Qt.AlignTop)
        self.apps_grid.setSpacing(15)
        self.apps_scroll.setWidget(self.apps_content)
        self.apps_tab_layout.addWidget(self.apps_scroll)
        
        hint_label = QLabel("💡 提示：点击按钮启动程序，右键按钮可删除")
        hint_label.setStyleSheet("color: #888888; font-size: 11px; ")
        hint_label.setAlignment(Qt.AlignCenter)
        self.apps_tab_layout.addWidget(hint_label)

    def setup_extract_tab(self):
        group_list = QGroupBox("1. 文件列表 (.txt)")
        layout_list = QHBoxLayout()
        self.list_file_edit = QLineEdit()
        self.list_file_edit.setPlaceholderText("选择包含文件路径的 txt 文件")
        btn_browse_list = QPushButton("浏览")
        btn_browse_list.clicked.connect(self.browse_list_file)
        layout_list.addWidget(self.list_file_edit)
        layout_list.addWidget(btn_browse_list)
        group_list.setLayout(layout_list)
        self.extract_tab_layout.addWidget(group_list)

        group_paths = QGroupBox("2. 路径设置")
        layout_paths = QVBoxLayout()

        layout_src = QHBoxLayout()
        layout_src.addWidget(QLabel("源根目录:"))
        self.source_dir_edit = QLineEdit()
        self.source_dir_edit.setPlaceholderText("选择源文件所在根目录")
        btn_browse_src = QPushButton("浏览")
        btn_browse_src.clicked.connect(self.browse_source_dir)
        layout_src.addWidget(self.source_dir_edit)
        layout_src.addWidget(btn_browse_src)
        layout_paths.addLayout(layout_src)

        layout_dest = QHBoxLayout()
        layout_dest.addWidget(QLabel("目标根目录:"))
        self.dest_dir_edit = QLineEdit()
        self.dest_dir_edit.setPlaceholderText("选择抽取目标目录")
        btn_browse_dest = QPushButton("浏览")
        btn_browse_dest.clicked.connect(self.browse_dest_dir)
        layout_dest.addWidget(self.dest_dir_edit)
        layout_dest.addWidget(btn_browse_dest)
        layout_paths.addLayout(layout_dest)

        group_paths.setLayout(layout_paths)
        self.extract_tab_layout.addWidget(group_paths)

        group_control = QGroupBox("3. 控制")
        layout_control = QHBoxLayout()
        self.btn_start = QPushButton("开始抽取")
        self.btn_start.clicked.connect(self.start_extraction)
        self.btn_stop = QPushButton("停止")
        self.btn_stop.clicked.connect(self.stop_extraction)
        self.btn_stop.setEnabled(False)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.extract_status_label = QLabel("就绪")
        self.extract_status_label.setStyleSheet("color: gray; ")
        layout_control.addWidget(self.btn_start)
        layout_control.addWidget(self.btn_stop)
        layout_control.addWidget(self.progress_bar)
        layout_control.addWidget(self.extract_status_label)
        group_control.setLayout(layout_control)
        self.extract_tab_layout.addWidget(group_control)

        group_log = QGroupBox("运行日志")
        layout_log = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout_log.addWidget(self.log_text)
        group_log.setLayout(layout_log)
        self.extract_tab_layout.addWidget(group_log)

    def update_time(self):
        now = datetime.datetime.now()
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        weekday_map = ["一", "二", "三", "四", "五", "六", "日"]
        self.time_label.setText(f"{time_str} 星期{weekday_map[now.weekday()]}")
        QTimer.singleShot(1000, self.update_time)

    # update_ip 方法已废弃，使用 IPAddressWidget 组件替代

    # ==================== 待办事项功能 ====================
    def load_todos(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.todos = data.get('todos', [])
                self.sequence_counter = data.get('counter', 0)
                self.render_todos()

    def save_todos(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump({'todos': self.todos, 'counter': self.sequence_counter}, f, ensure_ascii=False, indent=2)

    def add_todo(self):
        text = self.entry.text().strip()
        if not text:
            return
        self.todos.append({
            "id": datetime.datetime.now().timestamp(), 
            "text": text, 
            "done": False, 
            "seq": self.sequence_counter
        })
        self.sequence_counter += 1
        self.entry.clear()
        self.save_todos()
        self.render_todos()

    def render_todos(self):
        while self.todo_layout.count():
            item = self.todo_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        sorted_todos = sorted(self.todos, key=lambda x: (x['done'], x['seq']))
        
        for idx, todo in enumerate(sorted_todos):
            widget = TodoItem(todo['text'], todo['done'], todo['id'], todo['seq'])
            widget.checkbox.stateChanged.connect(lambda state, tid=todo['id']: self.toggle_status(tid))
            widget.del_btn.clicked.connect(lambda checked, tid=todo['id']: self.delete_todo(tid))
            widget.edit_btn.clicked.connect(lambda checked, tid=todo['id']: self.edit_todo(tid))
            
            if not todo['done']:
                widget.drag_label.mousePressEvent = lambda e, idx=idx: self.start_drag(e, idx)
                widget.drag_label.mouseMoveEvent = self.do_drag
                widget.drag_label.mouseReleaseEvent = self.end_drag
                widget.setCursor(Qt.OpenHandCursor)
            else:
                widget.setCursor(Qt.ArrowCursor)
            
            self.todo_layout.addWidget(widget)

    def toggle_status(self, todo_id):
        for todo in self.todos:
            if todo['id'] == todo_id:
                todo['done'] = not todo['done']
                break
        self.save_todos()
        self.render_todos()

    def edit_todo(self, todo_id):
        """编辑待办事项"""
        for todo in self.todos:
            if todo['id'] == todo_id:
                # 创建编辑对话框
                dialog = QDialog(self)
                dialog.setWindowTitle("编辑待办事项")
                dialog.setMinimumWidth(400)
                
                layout = QVBoxLayout(dialog)
                
                # 输入框
                label = QLabel("修改待办内容：")
                label.setStyleSheet("font-weight: bold; padding: 5px;")
                layout.addWidget(label)
                
                text_edit = QTextEdit()
                text_edit.setPlainText(todo['text'])
                text_edit.setMaximumHeight(100)
                layout.addWidget(text_edit)
                
                # 按钮
                btn_layout = QHBoxLayout()
                btn_layout.addStretch()
                
                cancel_btn = QPushButton("取消")
                cancel_btn.clicked.connect(dialog.reject)
                cancel_btn.setStyleSheet("padding: 8px 20px;")
                btn_layout.addWidget(cancel_btn)
                
                save_btn = QPushButton("保存")
                save_btn.setStyleSheet("padding: 8px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; font-weight: bold;")
                save_btn.clicked.connect(lambda: self.save_edit(todo_id, text_edit.toPlainText(), dialog))
                btn_layout.addWidget(save_btn)
                
                layout.addLayout(btn_layout)
                
                dialog.exec_()
                break
    
    def save_edit(self, todo_id, new_text, dialog):
        """保存编辑的待办事项"""
        new_text = new_text.strip()
        if not new_text:
            QMessageBox.warning(self, "警告", "待办内容不能为空！")
            return
        
        for todo in self.todos:
            if todo['id'] == todo_id:
                todo['text'] = new_text
                break
        
        self.save_todos()
        self.render_todos()
        dialog.accept()

    def delete_todo(self, todo_id):
        reply = QMessageBox.question(self, "确认", "确定要删除吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.todos = [t for t in self.todos if t['id'] != todo_id]
            self.save_todos()
            self.render_todos()

    def start_drag(self, event, index):
        self.drag_start_idx = index
        self.drag_start_pos = event.globalPos().y()
        self.dragged_widget = self.todo_layout.itemAt(index).widget()
        if self.dragged_widget:
            self.dragged_widget.setStyleSheet("background: #e0e0e0; border-radius: 5px; ")

    def do_drag(self, event):
        if self.drag_start_idx is None or self.dragged_widget is None:
            return
        current_y = event.globalPos().y()
        delta = current_y - self.drag_start_pos
        if abs(delta) > 40:
            direction = 1 if delta > 0 else -1
            target_idx = self.drag_start_idx + direction
            if self.swap_items(self.drag_start_idx, target_idx):
                self.drag_start_idx = target_idx
                self.drag_start_pos = current_y

    def swap_items(self, from_idx, to_idx):
        if to_idx < 0 or to_idx >= self.todo_layout.count():
            return False
        from_widget = self.todo_layout.itemAt(from_idx).widget()
        to_widget = self.todo_layout.itemAt(to_idx).widget()
        if from_widget is None or to_widget is None:
            return False
        if to_widget.is_done:
            return False
        self.todo_layout.takeAt(from_idx)
        self.todo_layout.takeAt(to_idx if to_idx < from_idx else to_idx - 1)
        self.todo_layout.insertWidget(to_idx, from_widget)
        self.todo_layout.insertWidget(from_idx, to_widget)
        return True

    def end_drag(self, event):
        if self.dragged_widget:
            self.dragged_widget.setStyleSheet("")
        self.drag_start_idx = None
        self.drag_start_pos = None
        self.dragged_widget = None
        self.update_seq_after_drag()

    def update_seq_after_drag(self):
        undone_widgets = []
        for i in range(self.todo_layout.count()):
            widget = self.todo_layout.itemAt(i).widget()
            if widget and not widget.is_done:
                undone_widgets.append(widget)
        for i, widget in enumerate(undone_widgets):
            for todo in self.todos:
                if todo['id'] == widget.todo_id:
                    todo['seq'] = i
                    break
        self.save_todos()

    # ==================== 备忘录功能 ====================
    def load_memo(self):
        if os.path.exists(self.memo_file):
            with open(self.memo_file, 'r', encoding='utf-8') as f:
                self.memo_text.setPlainText(f.read())

    def save_memo(self):
        with open(self.memo_file, 'w', encoding='utf-8') as f:
            f.write(self.memo_text.toPlainText())
        self.memo_status.setText("✓ 已保存")
        self.memo_status.setStyleSheet("color: #28a745; ")
        QTimer.singleShot(2000, lambda: self.memo_status.setText(""))

    def on_memo_change(self):
        self.memo_status.setText("● 未保存")
        self.memo_status.setStyleSheet("color: #ffc107; ")
        if self.memo_timer:
            self.memo_timer.stop()
        self.memo_timer = QTimer()
        self.memo_timer.timeout.connect(self.save_memo)
        self.memo_timer.setSingleShot(True) 
        self.memo_timer.start(3000)

    # ==================== 快捷启动功能 ====================
    def load_apps(self):
        if os.path.exists(self.apps_file):
            with open(self.apps_file, 'r', encoding='utf-8') as f:
                self.apps = json.load(f)
                self.render_apps()

    def save_apps(self):
        with open(self.apps_file, 'w', encoding='utf-8') as f:
            json.dump(self.apps, f, ensure_ascii=False, indent=2)

    def add_app(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择程序", "", "程序文件 (*.exe);;所有文件 (*.*)")
        if file_path:
            name, _ = QInputDialog.getText(self, "程序名称", "请输入显示名称: ", text=os.path.basename(file_path))
            if name:
                self.apps.append({"name": name, "path": file_path, "icon": ""})
                self.save_apps()
                self.render_apps()

    def render_apps(self):
        while self.apps_grid.count():
            item = self.apps_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        col = 0
        row = 0
        for app in self.apps:
            btn = AppLauncherButton(app['name'], app['path'], app.get('icon', ''))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, a=app: self.show_app_context_menu(pos, a))
            self.apps_grid.addWidget(btn, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def show_app_context_menu(self, pos, app):
        menu = QMenu(self)
        delete_action = menu.addAction("🗑️ 删除此程序")
        action = menu.exec_(QCursor.pos())
        if action == delete_action:
            reply = QMessageBox.question(self, "确认", f"确定要删除 {app['name']} 吗？", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.apps = [a for a in self.apps if a['path'] != app['path']]
                self.save_apps()
                self.render_apps()

    # ==================== 文件抽取功能 ====================
    def browse_list_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件列表", "", "文本文件 (*.txt)")
        if file_path:
            self.list_file_edit.setText(file_path)

    def browse_source_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择源根目录")
        if dir_path:
            self.source_dir_edit.setText(dir_path)

    def browse_dest_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择目标目录")
        if dir_path:
            self.dest_dir_edit.setText(dir_path)

    def log(self, message, msg_type="INFO"):
        color = {"INFO": "black", "SUCCESS": "green", "ERROR": "red"}.get(msg_type, "black")
        self.log_text.append(f'<span style="color:{color}">{message}</span>')
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def start_extraction(self):
        list_file = self.list_file_edit.text().strip()
        source_dir = self.source_dir_edit.text().strip()
        dest_dir = self.dest_dir_edit.text().strip()

        if not list_file or not os.path.exists(list_file):
            QMessageBox.warning(self, "错误", "请选择有效的文件列表！")
            return
        if not source_dir or not os.path.isdir(source_dir):
            QMessageBox.warning(self, "错误", "请选择有效的源目录！")
            return
        if not dest_dir:
            QMessageBox.warning(self, "错误", "请选择目标目录！")
            return

        self.log_text.clear()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self.extract_status_label.setText("处理中...")
        self.extract_status_label.setStyleSheet("color: blue; ")

        self.extract_worker = ExtractWorker(list_file, source_dir, dest_dir)
        self.extract_worker.log_signal.connect(self.log)
        self.extract_worker.progress_signal.connect(self.update_progress)
        self.extract_worker.status_signal.connect(self.extract_status_label.setText)
        self.extract_worker.finished_signal.connect(self.extraction_finished)
        self.extract_worker.start()

    def stop_extraction(self):
        if self.extract_worker and self.extract_worker.isRunning():
            self.extract_worker.stop()
            self.extract_status_label.setText("正在停止...")
            self.btn_stop.setEnabled(False)

    def update_progress(self, current, total):
        percent = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.extract_status_label.setText(f"处理中：{current}/{total}")

    def extraction_finished(self, success):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        if success:
            self.extract_status_label.setText("完成")
            self.extract_status_label.setStyleSheet("color: green; ")
            QMessageBox.information(self, "完成", "文件抽取完成！")
        else:
            self.extract_status_label.setText("已停止/失败")
            self.extract_status_label.setStyleSheet("color: red; ")

    # ==================== 其他功能 ====================
    def toggle_topmost(self, state):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, state == Qt.Checked)
        self.show()

    def closeEvent(self, event):
        if self.memo_status.text() == "● 未保存":
            self.save_memo()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DesktopTool()
    window.show()
    sys.exit(app.exec_())