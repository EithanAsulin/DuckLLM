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
import webbrowser
import random
import ctypes
import platform
import time
import socketserver
import http.server
import signal
from PySide6.QtCore import Qt, QTimer, QRectF, Signal, QObject, QSize
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QHBoxLayout, QFrame, QTextEdit, QFileDialog, QScrollArea, QSizePolicy
)
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPainterPath, QRegion, QKeyEvent, QPixmap, QFont, QIcon
)

# Global download state for progress tracking
_download_progress = {}

if "WAYLAND_DISPLAY" in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "wayland"


def get_ollama_cmd(script_dir):
    """Cross-platform Ollama binary discovery."""
    if platform.system() == "Windows":
        paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"),
            "C:\\Program Files\\Ollama\\ollama.exe",
            "ollama.exe"
        ]
        for p in paths:
            if os.path.exists(p) or p == "ollama.exe":
                return p if " " not in p else f'"{p}"'
    else: # MacOS / Linux
        paths = ["/usr/local/bin/ollama", "/usr/bin/ollama", "ollama"]
        for p in paths:
            if os.path.exists(p) or p == "ollama":
                return p
    return "ollama"


def get_user_data_dir():
    """Returns the platform-specific user data directory."""
    app_name = "DuckLLM"
    home = os.path.expanduser("~")
    if platform.system() == "Windows":
        # %LOCALAPPDATA%/DuckLLM
        return os.path.join(os.environ.get("LOCALAPPDATA", home), app_name)
    elif platform.system() == "Darwin":
        # ~/Library/Application Support/DuckLLM
        return os.path.join(home, "Library", "Application Support", app_name)
    else: # Linux/Unix
        # ~/.local/share/DuckLLM
        return os.path.join(home, ".local", "share", app_name)


def start_local_server(script_dir, data_dir, port=17432):
    """Starts the background server for Fullscreen mode."""
    ollama_cmd = get_ollama_cmd(script_dir)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            clean_path = self.path.split("?")[0]
            # Silencing noisy progress/tags checks
            if clean_path not in ("/api/download-progress", "/api/tags", "/duckllm_settings.json"):
                print(f"Server GET: {clean_path}")
            json_files = {
                "/duckllm_chat.json": "duckllm_chat.json",
                "/load": "duckllm_chat.json",
                "/duckllm_settings.json": "duckllm_settings.json",
                "/load-settings": "duckllm_settings.json"
            }
            
            if clean_path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(b"DUCKLLM SERVER V2")
                return

            if clean_path == "/list-chats":
                chats_root = os.path.join(data_dir, "chats")
                os.makedirs(chats_root, exist_ok=True)
                raw_list = []
                for root, _, files in os.walk(chats_root):
                    for f in files:
                        if f.endswith(".json"):
                            p = os.path.join(root, f)
                            try:
                                mtime = os.path.getmtime(p)
                                with open(p, "r", encoding="utf-8") as fin:
                                    data = json.load(fin)
                                    msgs = data if isinstance(data, list) else data.get("messages", [])
                                    fc = msgs[0].get("content", "New Chat") if msgs else "New Chat"
                                    title = (fc[:30] + '...') if len(fc) > 30 else fc
                                    raw_list.append({"id": f.replace(".json", ""), "title": title, "time": mtime})
                            except Exception:
                                pass
                
                # Sort by time descending
                raw_list.sort(key=lambda x: x['time'], reverse=True)
                chat_list = [{"id": x['id'], "title": x['title']} for x in raw_list]
                
                print(f"List-chats: found {len(chat_list)} chats")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(chat_list).encode())
            elif clean_path == "/exit":
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(b'{"status": "quitting"}')
                QApplication.quit()
            elif clean_path == "/load-chat":
                cid = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get("id", [""])[0]
                print(f"Loading chat: {cid}")
                found = False
                chats_root = os.path.join(data_dir, "chats")
                for root, _, files in os.walk(chats_root):
                    if f"{cid}.json" in files:
                        with open(os.path.join(root, f"{cid}.json"), "rb") as fchat:
                            self.send_response(200)
                            self.send_header("Access-Control-Allow-Origin", "*")
                            self.send_header("Content-Type", "application/json")
                            self.end_headers()
                            self.wfile.write(fchat.read())
                            found = True
                            break
                if not found:
                    self.send_response(404)
                    self.end_headers()
            elif clean_path == "/delete-chat":
                print(f"DuckLLM: Delete request for {self.path}")
                cid = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get("id", [""])[0]
                chats_root = os.path.join(data_dir, "chats")
                deleted = False
                for root, _, files in os.walk(chats_root):
                    if f"{cid}.json" in files:
                        os.remove(os.path.join(root, f"{cid}.json"))
                        print(f"DuckLLM: Deleted chat file {cid}.json")
                        deleted = True
                        break
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"deleted": deleted}).encode())
                return
            elif clean_path == "/api/tags":
                try:
                    resp = requests.get("http://localhost:11434/api/tags", timeout=5)
                    self.send_response(resp.status_code)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(resp.content)
                except Exception:
                    self.send_response(502)
                    self.end_headers()
            elif clean_path == "/api/list-duck-models":
                try:
                    print("DuckLLM: Fetching models from Hugging Face...")
                    url = "https://huggingface.co/api/models?search=DuckLLM&author=DuckLLM&expand[]=lastModified"
                    resp = requests.get(url, timeout=10)
                    print(f"DuckLLM: HF Status: {resp.status_code}")
                    if resp.ok:
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        self.wfile.write(resp.content)
                        print(f"DuckLLM: Sent {len(resp.json())} models to client")
                    else:
                        print(f"DuckLLM: HF Error - {resp.text}")
                        self.send_error(resp.status_code, "HF API Error")
                except Exception as e:
                    print(f"DuckLLM: Exception fetching models: {e}")
                    self.send_error(500, str(e))
                return
            elif clean_path == "/api/download-progress":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(_download_progress).encode())
            elif clean_path in json_files:
                filepath = os.path.join(data_dir, json_files[clean_path])
                data = b"[]"
                if os.path.exists(filepath):
                    with open(filepath, "rb") as f:
                        data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
            else:
                # Map specific paths to script_dir for static files if needed
                if clean_path in ("/fullscreen.html", "/logo.png", "/Attachment.png", "/Web.png", "/Unfiltered.png"):
                    full_path = os.path.join(script_dir, clean_path[1:])
                    if os.path.exists(full_path):
                        self.send_response(200)
                        self.send_header("Access-Control-Allow-Origin", "*")
                        if full_path.endswith(".html"):
                            self.send_header("Content-Type", "text/html")
                        elif full_path.endswith(".png"):
                            self.send_header("Content-Type", "image/png")
                        self.end_headers()
                        with open(full_path, "rb") as f:
                            self.wfile.write(f.read())
                        return
                super(Handler, self).do_GET()

        def do_POST(self):
            print(f"Server POST: {self.path}")
            clean_path = self.path.split("?")[0]
            body_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(body_len) if body_len > 0 else b""
            
            if clean_path == "/save-chat":
                cid = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get("id", [""])[0]
                now = time.localtime()
                save_dir = os.path.join(data_dir, "chats", time.strftime("%Y/%m/%d", now))
                os.makedirs(save_dir, exist_ok=True)
                with open(os.path.join(save_dir, f"{cid}.json"), 'wb') as f:
                    f.write(body)
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
            elif clean_path == "/delete-chat":
                cid = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get("id", [""])[0]
                chats_root = os.path.join(data_dir, "chats")
                for root, _, files in os.walk(chats_root):
                    if f"{cid}.json" in files:
                        os.remove(os.path.join(root, f"{cid}.json"))
                        break
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
            elif clean_path == "/api/delete-model":
                name = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get("name", [""])[0]
                if name:
                    import subprocess
                    subprocess.run(f"{ollama_cmd} rm {name}", shell=True)
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
            elif clean_path == "/api/download-duck":
                data = json.loads(body)
                def download(m_key, repo, filename):
                    try:
                        _download_progress[m_key] = {"status": "downloading", "progress": 0}
                        mdir = os.path.join(data_dir, "models")
                        os.makedirs(mdir, exist_ok=True)
                        l_path = os.path.join(mdir, f"DuckLLM-{m_key}.gguf")
                        url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
                        with requests.get(url, stream=True) as r:
                            t_size = int(r.headers.get('content-length', 0))
                            d_size = 0
                            with open(l_path, 'wb') as f:
                                for ch in r.iter_content(8192):
                                    f.write(ch)
                                    d_size += len(ch)
                                    if t_size > 0:
                                        _download_progress[m_key]["progress"] = int((d_size/t_size)*100)
                        _download_progress[m_key] = {"status": "finalizing", "progress": 100}
                        mfile = os.path.join(mdir, f"Modelfile-{m_key}")
                        with open(mfile, "w") as f:
                            f.write(f"FROM {l_path}\n")
                        import subprocess
                        subprocess.run(f"{ollama_cmd} create DuckLLM-{m_key}:latest -f \"{mfile}\"", shell=True)
                        _download_progress[m_key] = {"status": "done", "progress": 100}
                        print(f"DuckLLM: Model {m_key} is ready!")
                    except Exception as e:
                        _download_progress[m_key] = {"status": "error", "message": str(e)}
                threading.Thread(
                    target=download,
                    args=(data.get("model_key"), data.get("repo"), data.get("filename")),
                    daemon=True
                ).start()
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status":"started"}')
            elif clean_path == "/api/stop-gen":
                # Static access to the last created DuckLLM instance for web control
                global duck_llm_instance
                if 'duck_llm_instance' in globals():
                    duck_llm_instance.stop_generation()
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status":"stopped"}')
            elif clean_path in ("/api/chat", "/api/generate"):
                try:
                    resp = requests.post(f"http://localhost:11434{self.path}", data=body, stream=True)
                    self.send_response(resp.status_code)
                    for k, v in resp.headers.items():
                        if k.lower() not in ("content-length", "transfer-encoding"):
                            self.send_header(k, v)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    for chunk in resp.iter_content(1024): 
                        if chunk:
                            self.wfile.write(chunk)
                            self.wfile.flush()
                except Exception:
                    pass
            else:
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

    def serve():
        socketserver.TCPServer.allow_reuse_address = True
        try:
            with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
                print(f"DuckLLM Server: Listening on http://localhost:{port}")
                httpd.serve_forever()
        except Exception as e:
            print(f"DuckLLM Server: FAILED TO START on port {port}: {e}")
            print("Suggestion: Make sure no other instance of DuckLLM is running.")

    threading.Thread(target=serve, daemon=True).start()


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
            QPushButton:hover { background: #015AE6; color: white; }
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
                    txt = QTextEdit()
                    txt.setReadOnly(True)
                    txt.setMarkdown(content.strip().replace("\n", "  \n"))
                    txt.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                    txt.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                    txt.setFrameShape(QFrame.NoFrame)
                    txt.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
                    
                    is_rtl = any('\u0590' <= c <= '\u05FF' for c in content)
                    opt = txt.document().defaultTextOption()
                    if is_rtl:
                        txt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        opt.setTextDirection(Qt.RightToLeft)
                    else:
                        txt.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                        opt.setTextDirection(Qt.LeftToRight)
                    txt.document().setDefaultTextOption(opt)

                    color = "#CCC" if role == "assistant" else "#aaddff"
                    txt.setStyleSheet(f"color: {color}; font-size: 16px; background: transparent; border: none;")
                    
                    # Auto-adjust height logic
                    doc = txt.document()
                    doc.setTextWidth(900 - 40) # Sidebar offset / padding
                    txt.setFixedHeight(int(doc.size().height()) + 10)
                    
                    layout.addWidget(txt)

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
        self.data_dir = get_user_data_dir()
        
        # Hardened Migration: Merge history from old src/data into new data_dir
        old_data_dir = os.path.join(self.script_dir, "data")
        if os.path.exists(old_data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
            import shutil
            for item in os.listdir(old_data_dir):
                s, d = os.path.join(old_data_dir, item), os.path.join(self.data_dir, item)
                try:
                    if os.path.isdir(s):
                        if not os.path.exists(d) or not os.listdir(d):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                            print(f"DuckLLM: Migrated folder {item}")
                    elif not os.path.exists(d):
                        shutil.copy2(s, d)
                        print(f"DuckLLM: Migrated file {item}")
                except Exception as e:
                    print(f"Migration error ({item}): {e}")
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        os.makedirs(self.data_dir, exist_ok=True)

        logo_path = os.path.join(self.script_dir, "logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        
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
        self.abort_flag = False
        self.has_content = False
        self.expand_direction = "down"
        self.pending_images = []
        self.web_mode = False
        self.unfiltered_mode = False
        self.settings_file = os.path.join(self.script_dir, "duckllm_settings.json")
        self.load_settings()
        
        self._pending_user_query = ""
        self._was_web_mode = False
        self.chat_history = []
        self.chat_file = os.path.join(self.data_dir, "duckllm_chat.json")
        
        self.thinking_phrases = ["Please Wait", "Processing", "Analyzing", "Generating", "Almost Done", "Hold On"]
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
        
        # Start background server
        start_local_server(self.script_dir, self.data_dir)
        
    def eventFilter(self, obj, event):
        if obj is self.input_field and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
                self.start_query()
                return True
        return super().eventFilter(obj, event)

    def _on_input_changed(self):
        try:
            text = self.input_field.toPlainText()
            if not text: 
                if hasattr(self, "_last_dir"):
                    delattr(self, "_last_dir")
                return

            first_strong = ""
            for char in text:
                if char.isalnum():
                    first_strong = char
                    break
            
            # PLATFORM-AWARE BIDI:
            # On user's mirrored Windows, LTR commands yield RTL visual.
            # On Linux/MacOS, standard BiDi logic applies.
            is_rtl = '\u0590' <= first_strong <= '\u05FF'
            
            if sys.platform == "win32":
                # User's Windows is mirrored: LTR visually is RTL
                new_dir = Qt.LeftToRight if is_rtl else Qt.RightToLeft
            else:
                # Standard Platforms: Hebrew is RTL
                new_dir = Qt.RightToLeft if is_rtl else Qt.LeftToRight
            
            if not hasattr(self, '_last_dir') or self._last_dir != new_dir:
                self._last_dir = new_dir
                self._apply_direction()
                
            doc_height = self.input_field.document().size().height()
            new_height = min(max(int(doc_height) + 12, 44), 120)
            self.input_field.setFixedHeight(new_height)
            if not self.has_content:
                self.expand_ui()
        except Exception as e:
            print(f"DEBUG Logic Error: {e}")

    def _apply_direction(self):
        """Inverted logic to match user's mirrored environment."""
        try:
            # Applying LTR when Hebrew is detected because user's machine mirrors it to Right
            direction = self._last_dir # This is already LTR if is_rtl
            alignment = (Qt.AlignLeft | Qt.AlignVCenter) if (direction == Qt.LeftToRight) else (Qt.AlignRight | Qt.AlignVCenter)

            self.input_field.blockSignals(True)
            self.input_field.setLayoutDirection(direction)
            self.input_field.setAlignment(alignment)
            
            doc = self.input_field.document()
            opt = doc.defaultTextOption()
            opt.setTextDirection(direction)
            opt.setAlignment(alignment)
            doc.setDefaultTextOption(opt)
            
            self.input_field.blockSignals(False)
            self.input_field.viewport().update()
            print(f"DEBUG: Logic inversion applied ({'LTR-as-RTL' if direction == Qt.LeftToRight else 'RTL-as-LTR'})")
        except Exception as e:
            print(f"DEBUG Alignment Error: {e}")
            if hasattr(self, 'input_field'):
                self.input_field.blockSignals(False)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            QApplication.quit()

    def _setup_win32_hotkey(self):
        if not hasattr(ctypes, "windll"):
            return
        WM_HOTKEY, MOD_NONE, VK_DELETE, HOTKEY_ID = 0x0312, 0x0000, 0x2E, 1
        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_NONE, VK_DELETE):
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
        self.show()
        self.activateWindow()
        self.raise_()
        self.expand_ui()
        self.input_field.setFocus()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    json.load(f)
                    # We no longer load web/unfiltered modes to start fresh each session
            except Exception:
                pass
        self.save_settings()

    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                # We only save an empty or basic config, not the session modes
                json.dump({}, f, indent=2)
        except Exception:
            pass

    def save_chat(self):
        try:
            saveable = [{"role": msg["role"], "content": msg["content"]} for msg in self.chat_history]
            with open(self.chat_file, 'w', encoding='utf-8') as f:
                json.dump(saveable, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def init_ui(self):
        self.container = QFrame(self)
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(40, 15, 40, 25)
        
        self.header_container = QWidget()
        self.header = QHBoxLayout(self.header_container)
        self.header.setContentsMargins(0, 0, 0, 0)
        
        self.logo_label = QLabel()
        logo_path = os.path.join(self.script_dir, "logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setFixedSize(24, 24)
            self.logo_label.setStyleSheet("background: #015AE6; border-radius: 12px;")
            
        self.label = QLabel("DUCKLLM")
        self.label.setStyleSheet("color: #666; font-weight: 800; font-size: 11px; letter-spacing: 4px;")
        
        self.status_dot = QFrame()
        self.status_dot.setFixedSize(6, 6)
        self.status_dot.setStyleSheet("background: #00FF88; border-radius: 3px;")
        
        self.header.addWidget(self.logo_label)
        self.header.addSpacing(10)
        self.header.addWidget(self.label)
        self.header.addSpacing(8)
        self.header.addWidget(self.status_dot)
        self.header.addStretch()
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #444; font-size: 14px; border: none; font-weight: bold; }
            QPushButton:hover { color: #FF4444; }
        """)
        self.close_btn.clicked.connect(QApplication.quit)
        self.header.addWidget(self.close_btn)

        self.stop_btn = QPushButton("STOP 🛑")
        self.stop_btn.setFixedSize(80, 30)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.hide()
        self.stop_btn.setStyleSheet("""
            QPushButton { background: #FF4444; color: white; border-radius: 15px; font-weight: bold; font-size: 11px; }
            QPushButton:hover { background: #CC0000; }
        """)
        self.stop_btn.clicked.connect(self.stop_generation)
        self.header.insertWidget(4, self.stop_btn) # Insert before close_btn

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
        self.input_field.setStyleSheet("background: transparent; border: none; color: white; font-size: 20px; padding: 6px 0;")
        self.input_field.textChanged.connect(self._on_input_changed)
        self.input_field.installEventFilter(self)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("background: transparent; border: none;")
        self.chat_scroll.hide()

        self.chat_container = QWidget()
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
        btn_style_base = "background: #080808; border-radius: 27px; color: #666; font-size: 28px;"
        
        self.file_btn = QPushButton(self)
        self.file_btn.setFixedSize(btn_size)
        self.file_btn.hide()
        self.file_btn.clicked.connect(self.handle_file_dialog)
        self.file_btn.setIcon(QIcon(os.path.join(self.script_dir, "Attachment.png")))
        self.file_btn.setIconSize(QSize(40, 40))
        self.file_btn.setStyleSheet(btn_style_base)
        
        self.web_btn = QPushButton(self)
        self.web_btn.setFixedSize(btn_size)
        self.web_btn.hide()
        self.web_btn.clicked.connect(self.toggle_web_mode)
        self.web_btn.setIcon(QIcon(os.path.join(self.script_dir, "Web.png")))
        self.web_btn.setIconSize(QSize(40, 40))
        self.web_btn.setStyleSheet(btn_style_base)
        
        self.unfiltered_btn = QPushButton(self)
        self.unfiltered_btn.setFixedSize(btn_size)
        self.unfiltered_btn.hide()
        self.unfiltered_btn.clicked.connect(self.toggle_unfiltered_mode)
        self.unfiltered_btn.setIcon(QIcon(os.path.join(self.script_dir, "Unfiltered.png")))
        self.unfiltered_btn.setIconSize(QSize(40, 40))
        self.unfiltered_btn.setStyleSheet(btn_style_base)
 
        self.fullscreen_btn = QPushButton(self)
        self.fullscreen_btn.setFixedSize(btn_size)
        self.fullscreen_btn.hide()
        self.fullscreen_btn.clicked.connect(self.open_fullscreen)
        self.fullscreen_btn.setText("⛶")
        self.fullscreen_btn.setStyleSheet(btn_style_base)
 
        self.update_mode_styles()
 
    def update_mode_styles(self):
        web_border = "2px solid #015AE6" if self.web_mode else "none"
        self.web_btn.setStyleSheet(f"background: #080808; border: {web_border}; border-radius: 27px; color: #666; font-size: 28px;")
        unfiltered_border = "2px solid #FF4444" if self.unfiltered_mode else "none"
        self.unfiltered_btn.setStyleSheet(f"background: #080808; border: {unfiltered_border}; border-radius: 27px; color: #666; font-size: 28px;")
        
        mode_text = []
        if self.web_mode:
            mode_text.append("WEB")
        if self.unfiltered_mode:
            mode_text.append("UNFILTERED")
        
        status = getattr(self, '_current_status', "READY")
        suffix = f" [{ ' '.join(mode_text) }]" if mode_text else ""
        self.label.setText(f"DUCKLLM - {status}{suffix}")

    def animate_thinking_label(self):
        if not self.is_thinking:
            return
        if random.random() < 0.05:
            self.current_phrase = random.choice(self.thinking_phrases)
        self._dot_count += 1
        self._current_status = f"{self.current_phrase}{'.' * (self._dot_count % 4)}"
        self.update_mode_styles()

    def open_fullscreen(self):
        webbrowser.open("http://localhost:17432/fullscreen.html")
        self.hide()

    def toggle_web_mode(self):
        self.web_mode = not self.web_mode
        self.save_settings()
        self.update_mode_styles()

    def stop_generation(self):
        self.abort_flag = True
        self.is_thinking = False
        self.on_finished()
        # Notify the server too if needed (it will check the flag)
        print("DuckLLM: Generation stopped by user.")

    def toggle_unfiltered_mode(self):
        self.unfiltered_mode = not self.unfiltered_mode
        self.save_settings()
        self.update_mode_styles()

    def pivot_logic(self):
        for i in [self.header_container, self.input_field, self.preview_frame, self.chat_scroll]:
            self.main_layout.removeWidget(i)
            self.main_layout.addWidget(i)

    def enterEvent(self, e):
        if not self.is_thinking:
            self.expand_ui()
            self.activateWindow()
            self.input_field.setFocus()

    def leaveEvent(self, e):
        if not self.input_field.hasFocus() and not self.is_thinking:
            self.target_w, self.target_h = self.compact_w, self.compact_h
            for w in [self.input_field, self.chat_scroll, self.file_btn, self.web_btn, self.unfiltered_btn, self.fullscreen_btn]:
                w.hide()
    
    def update_physics(self):
        lerp = 0.14
        self._curr_w += (self.target_w - self._curr_w) * lerp
        self._curr_h += (self.target_h - self._curr_h) * lerp
        self.container.setFixedSize(int(self._curr_w), int(self._curr_h))
        mx, my, gap = (self.width() - int(self._curr_w)) // 2, 20, 15
        self.container.move(mx, my)
        bx = mx + int(self._curr_w) + gap
        self.file_btn.move(bx, my + 5)
        self.web_btn.move(bx, my + 65)
        self.unfiltered_btn.move(bx, my + 125)
        self.fullscreen_btn.move(bx, my + 185)
        mpath = QPainterPath()
        mpath.addRect(QRectF(mx-100, my-100, int(self._curr_w)+300, 800))
        self.setMask(QRegion(mpath.toFillPolygon().toPolygon()))
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setCompositionMode(QPainter.CompositionMode_Clear)
        p.fillRect(self.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.container.geometry()), 30, 30)
        p.fillPath(path, QBrush(QColor(8, 8, 8)))

    def expand_ui(self):
        self.pivot_logic()
        h_sum = 50 + self.input_field.height()
        if self.preview_frame.isVisible() and self.img_display.pixmap():
            h_sum += self.img_display.pixmap().height() + 20
        if self.has_content:
            self.chat_scroll.show()
            h_sum += min(max(self.chat_container.sizeHint().height()+20, 80), 500)
        self.target_h = min(max(h_sum, self.hover_h), self.max_h)
        self.target_w = self.hover_w if not self.has_content else self.max_w
        for w in [self.input_field, self.file_btn, self.web_btn, self.unfiltered_btn, self.fullscreen_btn]:
            w.show()
        self.activateWindow()
        self.input_field.setFocus()

    def handle_file_dialog(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if p:
            pix = QPixmap(p)
            if not pix.isNull():
                self.img_display.setPixmap(pix.scaled(self.hover_w-100, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.preview_frame.show()
                with open(p, "rb") as f:
                    self.pending_images.append(base64.b64encode(f.read()).decode('utf-8'))
                self.expand_ui()

    def clear_attachment(self):
        self.pending_images = []
        self.preview_frame.hide()
        self.img_display.clear()
        self.expand_ui()

    def start_query(self):
        q = self.input_field.toPlainText().strip()
        if not q and not self.pending_images:
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
        self._pending_user_query, self._was_web_mode = q, self.web_mode
        self.is_thinking = True
        self.abort_flag = False
        self.stop_btn.show()
        self.status_dot.setStyleSheet("background: #015AE6; border-radius: 4px;")
        self.input_field.setEnabled(False)
        self.thinking_timer.start(300)
        if self.web_mode:
            self.current_phrase = "Searching Web"
            threading.Thread(target=self.fetch_web_response, args=(q,), daemon=True).start()
        else:
            self.current_phrase = "Thinking"
            threading.Thread(target=self.fetch_ollama, args=(q, list(self.pending_images)), daemon=True).start()

    def fetch_web_response(self, q):
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
            r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(r) as resp:
                html = resp.read().decode('utf-8')
                results = re.findall(r'<a class="result__snippet" href="(.*?)"[^>]*>(.*?)</a>', html, re.DOTALL)
                context = " ".join([re.sub(r'<[^>]+>', '', s).strip() for _, s in results[:5]])
                sources = []
                for link, _ in results[:5]:
                    if 'http' in link:
                        m = re.search(r'https?://(?:www\.)?([^/]+)', link)
                        if m:
                            sources.append(m.group(1))
                sources = list(set(sources))
            m = "DuckLLM_Unfiltered:latest" if self.unfiltered_mode else "DuckLLM:latest"
            sys_prompt = f"You are an AI assistant. You MUST strictly answer in the user's language. If the user speaks Hebrew, you MUST answer in Hebrew. Context: {context}"
            res = requests.post("http://localhost:11434/api/generate", json={"model":m, "prompt":f"{sys_prompt}\n\nQ:{q}", "stream":True}, stream=True)
            for line in res.iter_lines():
                if self.abort_flag:
                    break
                if line:
                    token = json.loads(line.decode()).get('response', '')
                    if token:
                        self.signals.text_received.emit(token)
            if sources:
                self.signals.text_received.emit("\n\nSources: " + ", ".join(sources))
        except Exception as e:
            self.signals.text_received.emit(f"\n\nSearch failed: {e}")
        finally:
            self.signals.finished.emit()

    def fetch_ollama(self, query, images):
        try:
            msg = {"role": "user", "content": query}
            if images:
                msg["images"] = images
            self.chat_history.append(msg)
            m = "DuckLLM_Unfiltered:latest" if self.unfiltered_mode else "DuckLLM:latest"
            sys_prompt = "You are a helpful AI assistant. You MUST strictly answer in the user's language. If the user speaks Hebrew, you MUST answer in Hebrew."
            sh = [{"role": "system", "content": sys_prompt}] + self.chat_history
            res = requests.post("http://localhost:11434/api/chat", json={"model": m, "messages": sh, "stream": True}, stream=True)
            full = ""
            for line in res.iter_lines():
                if self.abort_flag:
                    break
                if line:
                    token = json.loads(line.decode()).get('message', {}).get('content', '')
                    full += token
                    self.signals.text_received.emit(token)
            self.chat_history.append({"role": "assistant", "content": full})
            self.save_chat()
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]
            self.signals.finished.emit()
        except Exception:
            self.signals.finished.emit()

    def update_response_ui(self, t):
        if not self.has_content:
            self.has_content = True
            self.is_thinking = True
            self._current_status = "RESPONDING"
            self.update_mode_styles()
            self.status_dot.setStyleSheet("background: #015AE6; border-radius: 4px;")
            self._stream_label.show()
            self.expand_ui()
        self._current_stream += t
        self._stream_label.setText(self._current_stream.replace("\n", "  \n"))
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())

    def on_finished(self):
        self.is_thinking = False
        self.stop_btn.hide()
        self._current_status = "READY"
        self.update_mode_styles()
        self.status_dot.setStyleSheet("background: #00FF88; border-radius: 4px;")
        self.thinking_timer.stop()
        self.input_field.setEnabled(True)
        self.input_field.clear()
        self.clear_attachment()
        if self._current_stream.strip():
            self._stream_label.hide()
            self._stream_label.setText("")
            self.chat_vbox.insertWidget(
                self.chat_vbox.count() - 1,
                ChatMessageWidget(self._current_stream, role="assistant")
            )
            self._current_stream = ""
            QTimer.singleShot(
                50,
                lambda: self.chat_scroll.verticalScrollBar().setValue(
                    self.chat_scroll.verticalScrollBar().maximum()
                )
            )


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        app = QApplication(sys.argv)
        global duck_llm_instance
        duck_llm_instance = DuckLLM()
        duck_llm_instance.show()
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        print(f"DUCKLLM CRITICAL CRASH: {e}")
        traceback.print_exc()
        sys.exit(1)
