import sys
import psutil
import pymem
import pymem.process
import webbrowser
import atexit
import os, sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLineEdit
from PySide6.QtGui import QPixmap, QFont, QIcon
from PySide6.QtCore import Qt, QTimer

GAME_PROCESS = "UmamusumePrettyDerby.exe"
PATCH_SIZE = 16

pm = None
original_bytes = None
patch_address = 0


class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Uma FPS Unlocker")
        self.setFixedSize(520, 420)
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        # Background
        bg = QLabel(self)
        bg.setPixmap(QPixmap(resource_path("background.jpg")))
        bg.setGeometry(0, 0, 520, 420)
        bg.setScaledContents(True)

        # Glass panel
        panel = QLabel(self)
        panel.setGeometry(100, 80, 320, 260)
        panel.setStyleSheet("""
        background-color: rgba(0,0,0,120);
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,40);
        """)

        # Title
        title = QLabel("Uma FPS Unlocker", self)
        title.setGeometry(0, 95, 520, 40)
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color:white; background:transparent;")

        # Status
        self.status = QLabel("Waiting for game...", self)
        self.status.setGeometry(0, 140, 520, 30)
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.status.setStyleSheet("color:orange; background:transparent;")

        # FPS input
        self.fps = QLineEdit("60", self)
        self.fps.setGeometry(210, 180, 100, 30)
        self.fps.setAlignment(Qt.AlignCenter)

        button_style = """
        QPushButton {
            background-color: rgba(30,30,30,200);
            color: white;
            border-radius: 8px;
            padding: 5px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: rgba(255,121,198,200);
        }
        QPushButton:pressed {
            background-color: rgba(200,80,150,200);
        }
        """

        btn60 = QPushButton("60", self)
        btn60.setGeometry(170, 220, 50, 30)
        btn60.setStyleSheet(button_style)
        btn60.clicked.connect(lambda: self.fps.setText("60"))

        btn120 = QPushButton("120", self)
        btn120.setGeometry(230, 220, 50, 30)
        btn120.setStyleSheet(button_style)
        btn120.clicked.connect(lambda: self.fps.setText("120"))

        btn240 = QPushButton("240", self)
        btn240.setGeometry(290, 220, 50, 30)
        btn240.setStyleSheet(button_style)
        btn240.clicked.connect(lambda: self.fps.setText("240"))

        apply_btn = QPushButton("Apply Patch", self)
        apply_btn.setGeometry(200, 260, 120, 35)
        apply_btn.setStyleSheet(button_style)
        apply_btn.clicked.connect(self.apply_patch)

        # Credit
        self.credit = QLabel("Made by HaruShinono", self)
        self.credit.setGeometry(0, 390, 520, 20)
        self.credit.setAlignment(Qt.AlignCenter)
        self.credit.setStyleSheet("""
        color:#ff79c6;
        background:transparent;
        text-decoration: underline;
        font-weight:bold;
        """)
        self.credit.setCursor(Qt.PointingHandCursor)

        self.credit.enterEvent = self.credit_hover
        self.credit.leaveEvent = self.credit_leave
        self.credit.mousePressEvent = self.open_github

        # Timer detect game
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_game)
        self.timer.start(3000)

        self.check_game()

    def credit_hover(self, event):
        self.credit.setStyleSheet("""
        color:white;
        background:transparent;
        text-decoration: underline;
        font-weight:bold;
        """)

    def credit_leave(self, event):
        self.credit.setStyleSheet("""
        color:#ff79c6;
        background:transparent;
        text-decoration: underline;
        font-weight:bold;
        """)

    def open_github(self, event):
        webbrowser.open("https://github.com/HaruShinono")

    def game_running(self):
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] == GAME_PROCESS:
                return True
        return False

    def check_game(self):
        if self.game_running():
            self.status.setText("Game detected")
            self.status.setStyleSheet("color:#7CFC00; background:transparent;")
        else:
            self.status.setText("Waiting for game...")
            self.status.setStyleSheet("color:orange; background:transparent;")

    def apply_patch(self):
        global pm, original_bytes, patch_address
        if not self.game_running():
            self.status.setText("Game not running")
            self.status.setStyleSheet("color:red; background:transparent;")
            return

        try:

            fps = int(self.fps.text())
            pm = pymem.Pymem(GAME_PROCESS)
            base = pymem.process.module_from_name(
                pm.process_handle,
                "UnityPlayer.dll"
            ).lpBaseOfDll

            # FPS patch
            addr_fps = base + 0x1C165AC
            pm.write_int(addr_fps, fps)

            # NOP patch
            patch_address = base + 0x60390
            original_bytes = pm.read_bytes(patch_address, PATCH_SIZE)
            pm.write_bytes(patch_address, b"\x90" * PATCH_SIZE, PATCH_SIZE)
            self.status.setText(f"FPS set to {fps}")
            self.status.setStyleSheet("color:#7CFC00; background:transparent;")
        except Exception as e:
            print(e)
            self.status.setText(f"Patch failed")
            self.status.setStyleSheet("color:red; background:transparent;")


def restore_patch():
    global pm, original_bytes, patch_address
    if pm and original_bytes and patch_address:
        try:
            pm.write_bytes(patch_address, original_bytes, len(original_bytes))
            print("Original bytes restored.")

        except Exception as e:
            print(f"Restore failed: {e}")


atexit.register(restore_patch)
app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())