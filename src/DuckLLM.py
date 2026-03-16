import sys
import os
import json
import requests
import threading
import base64
import urllib.request
import urllib.parse
import re
import datetime
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, Signal, QObject, QRect, QSize, QMimeData
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                               QLabel, QHBoxLayout, QFrame, QLineEdit, QTextEdit, QFileDialog, QScrollArea, QSizePolicy)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QRegion, QKeyEvent, QCursor, QPixmap, QImage, QTextCursor, QIcon, QClipboard, QFont
import webbrowser
import random
import ctypes
import platform
if hasattr(ctypes, "windll"):
    from ctypes import wintypes

if "WAYLAND_DISPLAY" in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "wayland"

class CodeBlock(QFrame):
    def __init__(self, code: str, language: str = "", parent=None):
        super().__init__(parent)
        self.code = code
        self.language = language
        self.setStyleSheet("background: #0d0d0d; border: 1px solid #2a2a2a; border-radius: 10px;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("background: #1a1a1a; border-radius: 10px 10px 0 0; border-bottom: 1px solid #2a2a2a;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 8, 6)

        lang_label = QLabel(language.upper() if language else "CODE")
        lang_label.setStyleSheet("color: #555; font-size: 10px; font-weight: 700; letter-spacing: 2px;")

        copy_btn = QPushButton("Copy")
        copy_btn.setFixedHeight(24)
        copy_btn.setStyleSheet("""
            QPushButton { background: #2a2a2a; color: #aaa; border: none; border-radius: 4px;
                          font-size: 11px; padding: 0 10px; }
            QPushButton:hover { background: #3a3a3a; color: white; }
        """)
        copy_btn.clicked.connect(self.copy_code)

        dl_btn = QPushButton("↓ Download")
        dl_btn.setFixedHeight(24)
        dl_btn.setToolTip("Save to Downloads folder")
        dl_btn.setStyleSheet("""
            QPushButton { background: #2a2a2a; color: #aaa; border: none; border-radius: 4px;
                          font-size: 11px; padding: 0 10px; }
            QPushButton:hover { background: #0040FF; color: white; }
        """)
        dl_btn.clicked.connect(self.download_code)

        header_layout.addWidget(lang_label)
        header_layout.addStretch()
        header_layout.addWidget(copy_btn)
        header_layout.addWidget(dl_btn)

        code_edit = QTextEdit()
        code_edit.setReadOnly(True)
        code_edit.setFont(QFont("Courier New", 12))
        code_edit.setStyleSheet("background: transparent; border: none; color: #e0e0e0; padding: 12px;")
        code_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        code_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        line_count = code.count('\n') + 1
        line_height = 22
        estimated_height = min(line_count * line_height + 30, 350)
        code_edit.setFixedHeight(max(estimated_height, 60))
        code_edit.setPlainText(code)

        layout.addWidget(header)
        layout.addWidget(code_edit)

    def copy_code(self):
        QApplication.clipboard().setText(self.code)
        btn = self.sender()
        if btn:
            btn.setText("Copied!")
            QTimer.singleShot(1500, lambda: btn.setText("Copy"))

    def download_code(self):
        ext_map = {
            "python": ".py", "py": ".py", "javascript": ".js", "js": ".js",
            "typescript": ".ts", "ts": ".ts", "html": ".html", "css": ".css",
            "bash": ".sh", "sh": ".sh", "json": ".json", "sql": ".sql",
            "java": ".java", "cpp": ".cpp", "c": ".c", "rust": ".rs",
            "go": ".go", "ruby": ".rb", "php": ".php", "swift": ".swift",
        }
        ext = ext_map.get(self.language.lower(), ".txt")
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads):
            downloads = os.path.expanduser("~")
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        filename = f"duckllm_code_{timestamp}{ext}"
        path = os.path.join(downloads, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.code)
        btn = self.sender()
        if btn:
            btn.setText("✓ Saved!")
            btn.setToolTip(f"Saved to: {path}")
            short_path = f"…/{os.path.basename(path)}"
            QTimer.singleShot(1000, lambda: btn.setText(short_path))
            QTimer.singleShot(4000, lambda: btn.setText("↓ Download"))
            QTimer.singleShot(4000, lambda: btn.setToolTip("Save to Downloads folder"))

class ChatMessageWidget(QFrame):
    def __init__(self, text: str, role: str = "assistant", parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)
        segments = self._parse_segments(text)
        for seg_type, content, lang in segments:
            if seg_type == "code":
                layout.addWidget(CodeBlock(content, lang))
            else:
                if content.strip():
                    lbl = QLabel()
                    lbl.setTextFormat(Qt.MarkdownText)
                    # Force hard breaks for single newlines in Markdown
                    formatted = content.strip().replace("\n", "  \n")
                    lbl.setText(formatted)
                    lbl.setWordWrap(True)
                    lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
                    color = "#CCC" if role == "assistant" else "#aaddff"
                    lbl.setStyleSheet(f"color: {color}; font-size: 16px; line-height: 1.6; background: transparent;")
                    layout.addWidget(lbl)

    def _parse_segments(self, text):
        segments = []
        pattern = re.compile(r'```(\w*)\n?(.*?)```', re.DOTALL)
        last = 0
        for m in pattern.finditer(text):
            if m.start() > last:
                segments.append(("text", text[last:m.start()], ""))
            segments.append(("code", m.group(2), m.group(1)))
            last = m.end()
        if last < len(text):
            segments.append(("text", text[last:], ""))
        return segments

class WorkerSignals(QObject):
    text_received = Signal(str)
    finished = Signal()

class DuckLLM(QWidget):
    show_requested = Signal()

    def __init__(self):
        super().__init__()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent;")
        self.setMouseTracking(True)
        
        self.compact_w, self.compact_h = 320, 60
        self.hover_w, self.hover_h = 900, 100
        self.max_w, self.max_h = 1000, 750
        
        self._curr_w, self._curr_h = float(self.compact_w), float(self.compact_h)
        self.target_w, self.target_h = self._curr_w, self._curr_h
        
        self.is_thinking = False
        self.has_content = False
        self.expand_direction = "down"
        self.pending_images = []
        self.web_mode = False
        self.unfiltered_mode = False
        self.settings_file = os.path.join(self.script_dir, "duckllm_settings.json")
        self.load_settings()
        
        self.chat_history = []
        try:
            _base = os.path.dirname(os.path.realpath(__file__))
        except NameError:
            _base = os.getcwd()
        self.chat_file = os.path.join(_base, "duckllm_chat.json")
        self._pending_user_query = ""
        self._was_web_mode = False
        
        self.thinking_phrases = [
            "Please Wait", "Processing", "Analyzing",
            "Generating", "Almost Done", "Hold On",
        ]
        self.current_phrase = "THINKING"
        self._dot_count = 0
        self.thinking_timer = QTimer()
        self.thinking_timer.timeout.connect(self.animate_thinking_label)
        
        self.signals = WorkerSignals()
        self.signals.text_received.connect(self.update_response_ui)
        self.signals.finished.connect(self.on_finished)

        self.show_requested.connect(self._on_show_requested)

        if platform.system() == "Windows":
            threading.Thread(target=self._setup_win32_hotkey, daemon=True).start()

        self.init_ui()
        
        self.engine = QTimer()
        self.engine.timeout.connect(self.update_physics)
        self.engine.start(16)
        
        screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geo)
        self.pivot_logic()

    def eventFilter(self, obj, event):
        if obj is self.input_field and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
                self.start_query()
                return True
        return super().eventFilter(obj, event)

    def _on_input_changed(self):
        doc_height = self.input_field.document().size().height()
        new_height = min(max(int(doc_height) + 12, 44), 120)
        self.input_field.setFixedHeight(new_height)
        if not self.has_content:
            self.expand_ui()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            QApplication.quit()

    def _setup_win32_hotkey(self):
        if not hasattr(ctypes, "windll"):
            return
        WM_HOTKEY = 0x0312
        MOD_NONE = 0x0000
        VK_DELETE = 0x2E
        HOTKEY_ID = 1

        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_NONE, VK_DELETE):
            print("Could not register Delete hotkey (key may be in use by another app).")
            return

        from ctypes import wintypes as wt
        msg = wt.MSG()
        try:
            while True:
                if user32.GetMessageA(ctypes.byref(msg), None, 0, 0):
                    if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                        self.show_requested.emit()
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageA(ctypes.byref(msg))
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)

    def _on_show_requested(self):
        """Expand and focus the duck — triggered by Del key or voice wake word."""
        self.activateWindow()
        self.raise_()
        self.expand_ui()
        self.input_field.setFocus()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.web_mode = data.get('web_mode', False)
                    self.unfiltered_mode = data.get('unfiltered_mode', False)
            except Exception as e:
                print(f"Error loading settings: {e}")
        self.save_settings()

    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump({
                    "web_mode": self.web_mode,
                    "unfiltered_mode": self.unfiltered_mode
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def save_chat(self):
        try:

            saveable = []
            for msg in self.chat_history:
                entry = {"role": msg["role"], "content": msg["content"]}
                saveable.append(entry)
            with open(self.chat_file, 'w', encoding='utf-8') as f:
                json.dump(saveable, f, indent=2, ensure_ascii=False)
            print(f"[Chat] Saved {len(saveable)} messages to {self.chat_file}")
        except Exception as e:
            print(f"[Chat] Error saving chat: {e}")

    def init_ui(self):
        self.container = QFrame(self)
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(40, 15, 40, 25)
        
        self.header_container = QWidget()
        self.header = QHBoxLayout(self.header_container)
        self.header.setContentsMargins(0, 0, 0, 0)
        self.status_dot = QFrame()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet("background: #00FF88; border-radius: 4px;")
        self.label = QLabel("DUCKLLM")
        self.label.setStyleSheet("color: #444; font-weight: 800; font-size: 11px; letter-spacing: 4px;")
        self.header.addWidget(self.status_dot)
        self.header.addWidget(self.label)
        self.header.addStretch()
        
        self.preview_frame = QFrame()
        self.preview_frame.hide()
        self.preview_layout = QVBoxLayout(self.preview_frame)
        self.img_display = QLabel()
        self.img_display.setAlignment(Qt.AlignCenter)
        self.img_display.setStyleSheet("border-radius: 15px; background: #111;")
        self.remove_img_btn = QPushButton("✕", self.preview_frame)
        self.remove_img_btn.setFixedSize(24, 24)
        self.remove_img_btn.setStyleSheet("background: #FF4444; color: white; border-radius: 12px; font-weight: bold; border: none;")
        self.remove_img_btn.clicked.connect(self.clear_attachment)
        self.preview_layout.addWidget(self.img_display)
        
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Ask DuckLLM...")
        self.input_field.hide()
        self.input_field.setFixedHeight(44)
        self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.input_field.setStyleSheet("background: transparent; border: none; color: white; font-size: 20px; padding: 6px 0;")
        self.input_field.textChanged.connect(self._on_input_changed)
        self.input_field.installEventFilter(self)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet("background: transparent; border: none;")
        self.chat_scroll.hide()

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_vbox = QVBoxLayout(self.chat_container)
        self.chat_vbox.setContentsMargins(0, 0, 0, 0)
        self.chat_vbox.setSpacing(8)
        self.chat_vbox.addStretch()
        self.chat_scroll.setWidget(self.chat_container)

        self._stream_label = QLabel()
        self._stream_label.setTextFormat(Qt.MarkdownText)
        self._stream_label.setWordWrap(True)
        self._stream_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._stream_label.setStyleSheet("color: #CCC; font-size: 16px; background: transparent;")
        self._stream_label.hide()
        self.chat_vbox.insertWidget(self.chat_vbox.count() - 1, self._stream_label)

        self._current_stream = ""

        btn_size = QSize(55, 55)
        btn_style_base = "background: transparent; border: none;"
        
        self.file_btn = QPushButton(self)
        self.file_btn.setFixedSize(btn_size)
        self.file_btn.hide()
        self.file_btn.clicked.connect(self.handle_file_dialog)
        self.file_btn.setStyleSheet(btn_style_base)
        if os.path.exists(os.path.join(self.script_dir, "Attachment.png")):
            self.file_btn.setIcon(QIcon(os.path.join(self.script_dir, "Attachment.png")))
            self.file_btn.setIconSize(btn_size)
        else:
            self.file_btn.setText("📎")
            self.file_btn.setStyleSheet("background: #080808; border-radius: 27px; color: #666; font-size: 18px;")

        self.web_btn = QPushButton(self)
        self.web_btn.setFixedSize(btn_size)
        self.web_btn.hide()
        self.web_btn.clicked.connect(self.toggle_web_mode)
        self.web_btn.setStyleSheet(btn_style_base)
        if os.path.exists(os.path.join(self.script_dir, "Web.png")):
            self.web_btn.setIcon(QIcon(os.path.join(self.script_dir, "Web.png")))
            self.web_btn.setIconSize(btn_size)
        else:
            self.web_btn.setText("🌐")
            self.web_btn.setStyleSheet("background: #080808; border-radius: 27px; color: #666; font-size: 18px;")
        
        self.unfiltered_btn = QPushButton(self)
        self.unfiltered_btn.setFixedSize(btn_size)
        self.unfiltered_btn.hide()
        self.unfiltered_btn.clicked.connect(self.toggle_unfiltered_mode)
        self.unfiltered_btn.setStyleSheet(btn_style_base)
        if os.path.exists(os.path.join(self.script_dir, "Unfiltered.png")):
            self.unfiltered_btn.setIcon(QIcon(os.path.join(self.script_dir, "Unfiltered.png")))
            self.unfiltered_btn.setIconSize(btn_size)
        else:
            self.unfiltered_btn.setText("🔓")
            self.unfiltered_btn.setStyleSheet("background: #080808; border-radius: 27px; color: #666; font-size: 18px;")

        self.fullscreen_btn = QPushButton(self)
        self.fullscreen_btn.setFixedSize(btn_size)
        self.fullscreen_btn.hide()
        self.fullscreen_btn.clicked.connect(self.open_fullscreen)
        self.fullscreen_btn.setText("⛶")
        self.fullscreen_btn.setStyleSheet("background: #080808; border-radius: 27px; color: #666; font-size: 18px;")
        self.fullscreen_btn.setToolTip("Open Fullscreen")

        self.update_mode_styles()

    def update_mode_styles(self):
        web_border = "2px solid #0040FF" if self.web_mode else "none"
        self.web_btn.setStyleSheet(f"background: transparent; border: {web_border}; border-radius: 27px;")
        
        unfiltered_border = "2px solid #FF4444" if self.unfiltered_mode else "none"
        self.unfiltered_btn.setStyleSheet(f"background: transparent; border: {unfiltered_border}; border-radius: 27px;")

        mode_text = []
        if self.web_mode:
            mode_text.append("WEB")
        if self.unfiltered_mode:
            mode_text.append("UNFILTERED")
        
        if mode_text:
            self.label.setText(f"DUCKLLM [{' '.join(mode_text)}]")
        else:
            self.label.setText("DUCKLLM")

    def animate_thinking_label(self):
        if not self.is_thinking:
            return
        
        if random.random() < 0.05:
            self.current_phrase = random.choice(self.thinking_phrases)
        
        self._dot_count += 1
        dots = "." * (self._dot_count % 4)
        self.label.setText(f"{self.current_phrase}{dots}")

    def open_fullscreen(self):
        import http.server
        import socketserver
        import socket
        port = 17432
        script_dir = self.script_dir

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=script_dir, **kwargs)
            def log_message(self, format, *args):
                pass
            def do_GET(self):
                clean_path = self.path.split("?")[0]
                json_map = {
                    "/duckllm_chat.json": "duckllm_chat.json",
                    "/load": "duckllm_chat.json",
                    "/duckllm_settings.json": "duckllm_settings.json",
                    "/load-settings": "duckllm_settings.json",
                }
                if clean_path in json_map:
                    filepath = os.path.join(script_dir, json_map[clean_path])
                    try:
                        with open(filepath, "rb") as f:
                            data = f.read()
                    except FileNotFoundError:
                        data = b"[]"
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    super().do_GET()
            def do_POST(self):
                if self.path in ('/save', '/save-settings'):
                    length = int(self.headers.get('Content-Length', 0))
                    body = self.rfile.read(length)
                    filename = 'duckllm_chat.json' if self.path == '/save' else 'duckllm_settings.json'
                    try:
                        path = os.path.join(script_dir, filename)
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(body.decode('utf-8'))
                        self.send_response(200)
                    except Exception:
                        self.send_response(500)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()

        try:
            with socket.create_connection(("localhost", port), timeout=0.3):
                webbrowser.open(f"http://localhost:{port}/fullscreen.html")
                QApplication.quit()
                return
        except OSError:
            pass

        import signal as _signal
        try:
            import subprocess
            result = subprocess.run(["fuser", f"{port}/tcp"], capture_output=True, text=True)
            for pid in result.stdout.split():
                try:
                    os.kill(int(pid), _signal.SIGTERM)
                except Exception:
                    pass
        except Exception:
            pass

        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True
        def serve():
            with ReusableTCPServer(("", port), Handler) as httpd:
                httpd.serve_forever()

        t = threading.Thread(target=serve)
        t.daemon = False
        t.start()

        for _ in range(20):
            try:
                with socket.create_connection(("localhost", port), timeout=0.1):
                    break
            except OSError:
                import time; time.sleep(0.1)

        webbrowser.open(f"http://localhost:{port}/fullscreen.html")
        QApplication.quit()

    def toggle_web_mode(self):
        self.web_mode = not self.web_mode
        self.save_settings()
        self.update_mode_styles()

    def toggle_unfiltered_mode(self):
        self.unfiltered_mode = not self.unfiltered_mode
        self.save_settings()
        self.update_mode_styles()

    def pivot_logic(self):
        self.expand_direction = "down"
        items = [self.header_container, self.input_field, self.preview_frame, self.chat_scroll]
        for i in items:
            self.main_layout.removeWidget(i)
        for i in items:
            self.main_layout.addWidget(i)

    def enterEvent(self, event):
        if not self.is_thinking:
            self.expand_ui()

            self.activateWindow()
            self.input_field.setFocus()

    def leaveEvent(self, event):
        if not self.input_field.hasFocus() and not self.is_thinking:
            self.target_w, self.target_h = self.compact_w, self.compact_h
            self.input_field.hide()
            self.chat_scroll.hide()
            self.file_btn.hide()
            self.web_btn.hide()
            self.unfiltered_btn.hide()
            self.fullscreen_btn.hide()

    def mousePressEvent(self, event):

        self.activateWindow()
        self.input_field.setFocus()
        super().mousePressEvent(event)

    def update_physics(self):
        lerp = 0.14
        self._curr_w += (self.target_w - self._curr_w) * lerp
        self._curr_h += (self.target_h - self._curr_h) * lerp
        self.container.setFixedSize(int(self._curr_w), int(self._curr_h))
        
        mx = (self.width() - int(self._curr_w)) // 2
        my = 20
        gap = 15
        
        self.container.move(mx, my)
        
        btn_y = my + 5
        self.file_btn.move(mx + int(self._curr_w) + gap, btn_y)
        self.web_btn.move(mx + int(self._curr_w) + gap, btn_y + 60)
        self.unfiltered_btn.move(mx + int(self._curr_w) + gap, btn_y + 120)
        self.fullscreen_btn.move(mx + int(self._curr_w) + gap, btn_y + 180)

        if self.preview_frame.isVisible():
            self.remove_img_btn.move(self.preview_frame.width() - 35, 15)

        mpath = QPainterPath()
        
        buffer = 150
        sensor_rect = QRectF(
            mx - buffer,
            my - buffer,
            int(self._curr_w) + gap + 80 + (buffer * 2),
            int(self._curr_h) + (buffer * 2)
        )
        mpath.addRect(sensor_rect)
        
        self.setMask(QRegion(mpath.toFillPolygon().toPolygon()))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        rect = QRectF(self.container.geometry())
        path = QPainterPath()
        path.addRoundedRect(rect, 30, 30)
        painter.fillPath(path, QBrush(QColor(8, 8, 8)))

    def expand_ui(self):
        self.pivot_logic()
        input_h = self.input_field.height()
        h_sum = 50 + input_h

        if self.preview_frame.isVisible():
            if self.img_display.pixmap():
                h_sum += self.img_display.pixmap().height() + 20

        if self.has_content:
            chat_h = min(self.chat_container.sizeHint().height() + 20, 500)
            chat_h = max(chat_h, 80)
            h_sum += chat_h
            self.chat_scroll.show()
            self.chat_scroll.setMinimumHeight(0)

        self.target_h = min(max(h_sum, self.hover_h), self.max_h)
        self.target_w = self.hover_w if not self.has_content else self.max_w
        self.input_field.show()
        self.file_btn.show()
        self.web_btn.show()
        self.unfiltered_btn.show()
        self.fullscreen_btn.show()
        
        self.activateWindow()
        self.input_field.setFocus()

    def handle_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "Files (*.txt *.py *.docx *.pdf *.cpp *.cp *.js *.jsx *.img *.iso *.css *.deb *.tar *.gz *.md5 *.modelfile *.docker *.html *.png *.jpg *.jpeg *.webp *.bmp *.mp4 *.shortcut *.md *.json *.jsonl *.xml *.yaml *.yml *.csv *.java *.c *.h *.hpp *.cs *.php *.rb *.go *.rs *.ts *.tsx *.sql *.sh *.bash *.ps1 *.lua *.r *.m *.swift *.kt *.scala *.vue *.svelte *.ipynb *.rtf *.tex *.log *.ini *.cfg *.conf *.toml *.env *.gif *.tiff *.tif *.svg *.ico *.pptx *.xlsx *.xls *.odt *.ods *.odp *.epub *.mp3 *.wav *.ogg *.flac *.m4a *.aac *.avi *.mov *.mkv *.webm *.htm *.xhtml *.rst *.zip *.rar *.7z *.scss *.sass *.less)"
        )

        if path:
            pix = QPixmap(path)
            if pix.isNull():
                return
            
            scaled_pix = pix.scaled(
                self.hover_w - 100,
                300,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.img_display.setPixmap(scaled_pix)
            self.preview_frame.show()
            
            try:
                with open(path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                    self.pending_images.append(img_data)
            except Exception as e:
                print(f"Image encoding error: {e}")
                return
            
            self.expand_ui()

    def clear_attachment(self):
        self.pending_images = []
        self.preview_frame.hide()
        self.img_display.clear()
        self.expand_ui()

    def get_domain(self, url):
        try:
            domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
            return domain.group(1) if domain else "Unknown Source"
        except:
            return "Source"

    def fetch_web_data(self, user_input):
        try:
            search_query = urllib.parse.quote(user_input)
            url = f"https://html.duckduckgo.com/html/?q={search_query}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8')
                
                results = re.findall(r'<a class="result__snippet" href="(.*?)"[^>]*>(.*?)</a>', content, re.DOTALL)
                
                texts = []
                sources = set()
                
                for link, snippet in results[:6]:
                    clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                    if clean_snippet:
                        texts.append(clean_snippet)
                    
                    if 'uddg=' in link:
                        actual_link = urllib.parse.unquote(link.split('uddg=')[-1].split('&')[0])
                    else:
                        actual_link = link
                    sources.add(self.get_domain(actual_link))
                
                return "  ".join(texts), list(sources)
        except Exception as e:
            print(f"Web search error: {e}")
            return "", []

    def fetch_web_response(self, query):
        try:
            context, sources = self.fetch_web_data(query)
            if not context.strip():
                context = "No relevant information found from web search."
            
            system_instruction = (
                "You are a helpful AI. Provide a normal, concise summary of the topic.  "
                "Do NOT mention you are summarizing or that you searched the web.  "
                "Just give the answer directly in under 100 words."
            )
            full_prompt = f"{system_instruction}\n\nContext: {context}\n\nQuestion: {query}"
            
            model_name = "DuckLLM_Unfiltered:latest" if self.unfiltered_mode else "DuckLLM:latest"
            
            payload = {
                "model": model_name,
                "prompt": full_prompt,
                "stream": True
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                stream=True,
                timeout=60
            )
            
            for line in response.iter_lines():
                if line:
                    try: 
                        chunk = json.loads(line.decode())
                        if token := chunk.get('response'):
                            self.signals.text_received.emit(token)
                        if chunk.get('done'):
                            break
                    except:
                        continue
            
            if sources:
                sources_str = "\n\nSources: " + ", ".join(sources)
                self.signals.text_received.emit(sources_str)
                
        except Exception as e:
            self.signals.text_received.emit(f"\n\nSearch failed: {str(e)[:100]}")
        finally:
            self.signals.finished.emit()

    def start_query(self):
        query = self.input_field.toPlainText().strip()
        if not query and not self.pending_images:
            return

        self._current_stream = ""
        self._stream_label.setText("")
        self._stream_label.hide()
        self.has_content = False

        while self.chat_vbox.count() > 1:  
            item = self.chat_vbox.takeAt(0)
            if item.widget() and item.widget() is not self._stream_label:
                item.widget().deleteLater()
        self.chat_vbox.insertWidget(0, self._stream_label)

        self._pending_user_query = query
        self._was_web_mode = self.web_mode

        if self.web_mode:
            self.is_thinking = True
            self.input_field.setEnabled(False)
            self.current_phrase = "Searching Web"
            self.status_dot.setStyleSheet("background: #FFCC00; border-radius: 4px;")
            self.thinking_timer.start(300)
            
            threading.Thread(
                target=self.fetch_web_response,
                args=(query,),
                daemon=True
            ).start()
            return
        
        self.is_thinking = True
        self.input_field.setEnabled(False)
        
        self.current_phrase = "Thinking"
        self.status_dot.setStyleSheet("background: #FFCC00; border-radius: 4px;")
        self.thinking_timer.start(300)
        
        imgs_to_send = list(self.pending_images)
        threading.Thread(target=self.fetch_ollama, args=(query, imgs_to_send), daemon=True).start()

    def fetch_ollama(self, query, images):
        try:
            user_msg = {"role": "user", "content": query}
            if images:
                user_msg["images"] = images
            
            self.chat_history.append(user_msg)

            model_name = "DuckLLM_Unfiltered:latest" if self.unfiltered_mode else "DuckLLM:latest"

            payload = {
                "model": model_name,
                "messages": self.chat_history,
                "stream": True
            }

            res = requests.post("http://localhost:11434/api/chat", json=payload, stream=True)
            
            full_assistant_response = ""
            for line in res.iter_lines():
                if line:
                    chunk = json.loads(line.decode())
                    if 'message' in chunk:
                        token = chunk['message']['content']
                        full_assistant_response += token
                        self.signals.text_received.emit(token)
            
            self.chat_history.append({"role": "assistant", "content": full_assistant_response})
            self.save_chat()
            
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]

            self.signals.finished.emit()
            
        except Exception as e:
            print(f"Chat Error: {e}")
            self.signals.finished.emit()

    def update_response_ui(self, token):
        if not self.has_content:
            self.has_content = True
            self.thinking_timer.stop()
            self.label.setText("Responding...")
            self.status_dot.setStyleSheet("background: #00CCFF; border-radius: 4px;")
            self._stream_label.show()
            self.expand_ui()

        self._current_stream += token
        # Force hard breaks for single newlines in Markdown
        formatted = self._current_stream.replace("\n", "  \n")
        try:
            self._stream_label.setText(formatted)
            self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            )
        except RuntimeError:
            pass # Signal source or label might be deleted during streaming

    def on_finished(self):
        self.is_thinking = False
        self.thinking_timer.stop()
        self.input_field.setEnabled(True)
        self.input_field.clear()
        self.input_field.setFixedHeight(44)
        self.clear_attachment()
        self.label.setText("READY")
        self.status_dot.setStyleSheet("background: #00FF88; border-radius: 4px;")

        if self._current_stream.strip():
            self._stream_label.hide()
            self._stream_label.setText("")
            msg_widget = ChatMessageWidget(self._current_stream, role="assistant")
            self.chat_vbox.insertWidget(self.chat_vbox.count() - 1, msg_widget)

            if self._was_web_mode and self._pending_user_query:
                self.chat_history.append({"role": "user", "content": self._pending_user_query})
                self.chat_history.append({"role": "assistant", "content": self._current_stream})
                if len(self.chat_history) > 10:
                    self.chat_history = self.chat_history[-10:]
                self.save_chat()

            self._current_stream = ""
            QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            ))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    frontend = DuckLLM()
    frontend.show()
    sys.exit(app.exec())