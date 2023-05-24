from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QFrame, QWidget, QHBoxLayout
from winreg import *

# Constants
DEVICE_KEY = r'SYSTEM\CurrentControlSet\Control\Session Manager\DOS Devices'
LABEL_DEVICE_KEY = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\DriveIcons'

import qtmodern.styles
import qtmodern.windows

class DriveMapper(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("P: Virtual Drive Mapper")
        self.setFixedSize(450, 220)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout(self.central_widget)
        self.status_label = QLabel("Status")
        layout.addWidget(self.status_label)

        status_layout = QHBoxLayout()
        self.status_text = QLineEdit(self.central_widget)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("background-color: gray")
        status_layout.addWidget(self.status_text)

        self.btn_delete = QPushButton("Delete", self.central_widget)
        self.btn_delete.clicked.connect(self.delete_key)
        status_layout.addWidget(self.btn_delete)
        layout.addLayout(status_layout)

        self.choose_txt = QLabel("Choose Projects Folder: ")
        layout.addWidget(self.choose_txt)

        browse_layout = QHBoxLayout()
        self.browse_field = QLineEdit(self.central_widget)
        browse_layout.addWidget(self.browse_field)

        self.btn_browse = QPushButton("Browse", self.central_widget)
        self.btn_browse.clicked.connect(self.get_folder_path)
        browse_layout.addWidget(self.btn_browse)

        layout.addLayout(browse_layout)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(self.line)

        self.btn_cancel = QPushButton("Close", self.central_widget)
        self.btn_cancel.clicked.connect(self.close)
        layout.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton("Apply", self.central_widget)
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self.add_key)
        layout.addWidget(self.btn_apply)
        self.browse_field.textChanged.connect(self.toggle_state)
        self.check_status()

    def get_folder_path(self):
        folder_selected = QFileDialog.getExistingDirectory(self, "Select Directory")
        self.browse_field.setText(folder_selected)

    def check_status(self):
        try:
            key = OpenKey(HKEY_LOCAL_MACHINE, DEVICE_KEY, 0, KEY_ALL_ACCESS)
            result = QueryValueEx(key, "P:")
        except FileNotFoundError:
            self.status_text.setText("No mapped drive found.")
        else:
            drive_path = result[0].replace("\\??\\", "")
            self.status_text.setText(f"Drive P: is mapped to {drive_path}")

    def create_key(self):
        folder = Path(self.browse_field.text())
        key = OpenKey(HKEY_LOCAL_MACHINE, DEVICE_KEY, 0, KEY_ALL_ACCESS)
        SetValueEx(key, "P:", 0, REG_SZ, f"\\??\\{folder}")
        CloseKey(key)
        self.check_status()

    def add_key(self):
        try:
            key = CreateKey(HKEY_LOCAL_MACHINE, DEVICE_KEY)
            DeleteValue(key, "P:")
            CloseKey(key)
        except WindowsError:
            self.create_key()
        else:
            self.create_key()

    def delete_key(self):
        try:
            key = OpenKey(HKEY_LOCAL_MACHINE, DEVICE_KEY, 0, KEY_ALL_ACCESS)
            DeleteValue(key, "P:")
            CloseKey(key)
        except WindowsError:
            pass
        self.check_status()

    def toggle_state(self):
        if self.browse_field.text():
            self.btn_apply.setEnabled(True)
        else:
            self.btn_apply.setEnabled(False)

if __name__ == '__main__':
    app = QApplication([])
    qtmodern.styles.dark(app)
    mw=qtmodern.windows.ModernWindow(DriveMapper())
    mw.show()
    app.exec_()


