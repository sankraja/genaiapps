import sys
import subprocess
import threading
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QLineEdit, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, QObject, QThread

# Load environment variables from workspace root .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

class MCPServerController(QObject):
    status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__() 
        self.process = None

    def start_server(self):
        if self.process is None or self.process.poll() is not None:
            npx_path = os.environ.get("NPX_PATH")
            screenshot_dir = os.environ.get("DESKTOP_CLIENT_SCREENSHOT_DIR")
            mcp_command = [
                npx_path,
                "@playwright/mcp@latest",
                "--output-dir",
                screenshot_dir
            ]
            self.process = subprocess.Popen(mcp_command)
            self.status_changed.emit("MCP Server started.")
        else:
            self.status_changed.emit("MCP Server already running.")

    def stop_server(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process = None
            self.status_changed.emit("MCP Server stopped.")
        else:
            self.status_changed.emit("MCP Server not running.")

class AgentRunner(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, prompt, agent_path):
        super().__init__()
        self.prompt = prompt
        self.agent_path = agent_path

    def run(self):
        import subprocess
        import sys
        try:
            proc = subprocess.Popen(
                [sys.executable, self.agent_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            proc.stdin.write(self.prompt + "\n")
            proc.stdin.close()
            for line in proc.stdout:
                self.log_signal.emit(line.rstrip())
            proc.wait()
            if proc.returncode != 0:
                err = proc.stderr.read()
                self.log_signal.emit(f"[Agent Error] {err}")
        except Exception as e:
            self.log_signal.emit(f"[Agent Exception] {str(e)}")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Playwright MCP Desktop UI Automation")
        self.resize(600, 500)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.status_label = QLabel("Status: Idle")
        self.layout.addWidget(self.status_label)

        self.start_btn = QPushButton("Start MCP Server")
        self.stop_btn = QPushButton("Stop MCP Server")
        self.layout.addWidget(self.start_btn)
        self.layout.addWidget(self.stop_btn)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Type your message or automation prompt here...")
        self.prompt_input.setFixedHeight(70)
        self.prompt_input.setStyleSheet("""
            QTextEdit {
                border-radius: 8px;
                border: 1px solid #b0b0b0;
                font-size: 15px;
                padding: 8px;
                background: #f8f8fa;
            }
        """)
        self.layout.addWidget(self.prompt_input)

        self.run_btn = QPushButton("Run Automation")
        self.layout.addWidget(self.run_btn)

        self.clear_btn = QPushButton("Clear Chat & Tools")
        self.layout.addWidget(self.clear_btn)
        self.clear_btn.clicked.connect(self.clear_areas)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setPlaceholderText("Agent and user chat will appear here...")
        self.chat_area.setStyleSheet("background: #f8f8fa; border-radius: 8px; border: 1px solid #e0e0e0; font-size: 15px; padding: 8px;")
        self.layout.addWidget(QLabel("Chat"))
        self.layout.addWidget(self.chat_area)

        self.tools_area = QTextEdit()
        self.tools_area.setReadOnly(True)
        self.tools_area.setPlaceholderText("Tool calls and step details will appear here...")
        self.tools_area.setStyleSheet("background: #f4f7fa; border-radius: 8px; border: 1px solid #e0e0e0; font-size: 14px; padding: 8px;")
        self.layout.addWidget(QLabel("Tool Calls"))
        self.layout.addWidget(self.tools_area)

        self.mcp_controller = MCPServerController()
        self.mcp_controller.status_changed.connect(self.update_status)

        self.start_btn.clicked.connect(self.mcp_controller.start_server)
        self.stop_btn.clicked.connect(self.mcp_controller.stop_server)
        self.run_btn.clicked.connect(self.run_automation)

    def clear_areas(self):
        self.chat_area.clear()
        self.tools_area.clear()
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Playwright MCP Desktop UI Automation")
        self.resize(600, 500)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.status_label = QLabel("Status: Idle")
        self.layout.addWidget(self.status_label)

        self.start_btn = QPushButton("Start MCP Server")
        self.stop_btn = QPushButton("Stop MCP Server")
        self.layout.addWidget(self.start_btn)
        self.layout.addWidget(self.stop_btn)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Type your message or automation prompt here...")
        self.prompt_input.setFixedHeight(70)
        self.prompt_input.setStyleSheet("""
            QTextEdit {
                border-radius: 8px;
                border: 1px solid #b0b0b0;
                font-size: 15px;
                padding: 8px;
                background: #f8f8fa;
            }
        """)


        self.layout.addWidget(self.prompt_input)
        self.run_btn = QPushButton("Run Automation")
        self.layout.addWidget(self.run_btn)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setPlaceholderText("Agent and user chat will appear here...")
        self.chat_area.setStyleSheet("background: #f8f8fa; border-radius: 8px; border: 1px solid #e0e0e0; font-size: 15px; padding: 8px;")
        self.layout.addWidget(QLabel("Chat"))
        self.layout.addWidget(self.chat_area)

        self.tools_area = QTextEdit()
        self.tools_area.setReadOnly(True)
        self.tools_area.setPlaceholderText("Tool calls and step details will appear here...")
        self.tools_area.setStyleSheet("background: #f4f7fa; border-radius: 8px; border: 1px solid #e0e0e0; font-size: 14px; padding: 8px;")
        self.layout.addWidget(QLabel("Tool Calls"))
        self.layout.addWidget(self.tools_area)

        self.mcp_controller = MCPServerController()
        self.mcp_controller.status_changed.connect(self.update_status)

        self.start_btn.clicked.connect(self.mcp_controller.start_server)
        self.stop_btn.clicked.connect(self.mcp_controller.stop_server)
        self.run_btn.clicked.connect(self.run_automation)

    def handle_agent_log(self, line):
        if "Tool calls:" in line:
            self.tools_area.append(line)
            QApplication.processEvents()
        else:
            self.chat_area.append(line)
            QApplication.processEvents()

    def update_status(self, status):
        self.status_label.setText(f"Status: {status}")
        self.chat_area.append(f"[MCP] {status}")

    def run_automation(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Input Required", "Please enter a prompt for UI automation.")
            return
        self.chat_area.append(f"[Prompt] {prompt}")
        agent_path = os.environ.get("AGENT_PATH")
        self.agent_thread = AgentRunner(prompt, agent_path)
        self.agent_thread.log_signal.connect(self.handle_agent_log)
        self.chat_area.append("[Agent] Starting agent and initializing... (please wait)")
        self.agent_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
