import os
import requests
import zipfile
import time
import sys
from PyQt5 import QtWidgets, QtCore

import qtmodern.styles
import qtmodern.windows
DOWNLOAD_URL = 'https://github.com/ruffaz/dayzutilities/raw/OTA/dzserverloaderOTA.zip'

class UpdateThread(QtCore.QThread):
    progress_signal = QtCore.pyqtSignal(str)

    def run(self):
        # Download file into the staging folder
        download_path = os.path.join('staging', 'dzserverloaderOTA.zip')
        self.download_file(download_path)

        # Extract the contents of the ZIP file to the staging folder
        self.extract_zip(download_path, 'staging')

        # Delete the ZIP file
        os.remove(download_path)

    def download_file(self, save_path):
        self.progress_signal.emit(f'Downloading {DOWNLOAD_URL}...')
        response = requests.get(DOWNLOAD_URL, stream=True)
        file_size = int(response.headers.get('Content-Length', 0))
        block_size = 1024
        progress = 0
        last_time = time.time()
        while True:
            data = response.raw.read(block_size)
            if not data:
                break
            progress += len(data)
            with open(save_path, 'ab') as f:
                f.write(data)
            if time.time() - last_time > .07:
                last_time = time.time()
                percent = progress / file_size * 100
                self.progress_signal.emit('Downloading... {:.0f}%'.format(percent))
        self.progress_signal.emit('Download complete!')


    def extract_zip(self, zip_file_path, target_folder):
        self.progress_signal.emit(f'Extracting {zip_file_path}...')
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(target_folder)
        self.progress_signal.emit(f'{zip_file_path} extracted successfully!')

class UpdateDialog(QtWidgets.QDialog):
    def __init__(self):

        super().__init__()
        
        # Create the text box
        self.text_box = QtWidgets.QPlainTextEdit()
        self.text_box.setReadOnly(True)
        self.text_box.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        # Create the "Update" button
        self.update_button = QtWidgets.QPushButton('Update')
        self.update_button.setFixedSize(QtCore.QSize(300, 50))
        self.update_button.clicked.connect(self.update_button_clicked)

        # Create the layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.text_box)
        layout.addWidget(self.update_button)
        self.setLayout(layout)

    def update_button_clicked(self):
        self.update_button.setDisabled(True)
        self.update_thread = UpdateThread()
        self.update_thread.progress_signal.connect(self.log)
        self.update_thread.finished.connect(self.on_update_finished)
        self.update_thread.start()

    def on_update_finished(self):
        self.update_button.setDisabled(False)
        QtWidgets.QMessageBox.information(self, 'Update Complete', 'The update is complete!')

    def log(self, message):
        self.text_box.appendPlainText(message)
        QtWidgets.QApplication.processEvents()

def main():
    # Create staging folder if it doesn't exist
    os.makedirs('staging', exist_ok=True)

    # Create main window
    app = QtWidgets.QApplication(sys.argv)
    qtmodern.styles.dark(app)
    mw = qtmodern.windows.ModernWindow(UpdateDialog())
    mw.setWindowTitle('Updater')
    mw.resize(300, 300)
    mw.show()

    # Start the main event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
    

