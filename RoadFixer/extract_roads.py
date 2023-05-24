import os
import shutil
import sys
import json
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QProgressBar, QFileDialog

CONFIG_FILE = "paths_config.json"

class ExtractRoadsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.load_paths()

            # Define the DayZ installation path variables
        self.dayz_path = "DEFAULT_DAYZ_PATH"
        self.dayz_path_edit = QLineEdit(self)
        self.dayz_path_edit.setText(self.dayz_path)
        self.dayz_path_edit.setReadOnly(True)
        self.dayz_path_button = QPushButton("Browse", self)
        self.dayz_path_button.clicked.connect(self.browse_dayz_path)

        # Define the PBO extraction path
        self.pbo_extraction_path = QLineEdit(self)
        self.pbo_extraction_browse_button = QPushButton("Browse", self)
        self.pbo_extraction_browse_button.clicked.connect(self.browse_pbo_extraction_path)

        # Define the roads paths message
        self.roads_paths_message = QLineEdit(self)
        self.roads_paths_message.setReadOnly(True)

        # Define the extract button
        self.extract_button = QPushButton("Extract", self)
        self.extract_button.clicked.connect(self.extract_roads)

        # Define the cancel button
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.close)

        # Define progress bars
        self.dz_roads_progress = QProgressBar(self)
        self.bliss_roads_progress = QProgressBar(self)

        # Define the layout
        grid = QGridLayout()
        grid.addWidget(QLabel("DayZ Installation Path:"), 0, 0)
        grid.addWidget(self.dayz_path_edit, 0, 1)
        grid.addWidget(self.dayz_path_button, 0, 2)
        grid.addWidget(QLabel("PBO Extraction Path:"), 1, 0)
        grid.addWidget(self.pbo_extraction_path, 1, 1)
        grid.addWidget(self.pbo_extraction_browse_button, 1, 2)
        grid.addWidget(QLabel("Roads to extract are here:"), 2, 0)
        grid.addWidget(self.roads_paths_message, 2, 1, 1, 2)
        grid.addWidget(self.dz_roads_progress, 3, 0)
        grid.addWidget(self.bliss_roads_progress, 3, 1)
        grid.addWidget(self.extract_button, 4, 0)
        grid.addWidget(self.cancel_button, 4, 1)

        self.setLayout(grid)

    def load_paths(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.dayz_path = config.get("dayz_path", "DEFAULT_DAYZ_PATH")
                self.extraction_path = config.get("extraction_path", "")
        else:
            self.dayz_path = "DEFAULT_DAYZ_PATH"
            self.extraction_path = ""

    def save_paths(self):
        config = {
            "dayz_path": self.dayz_path,
            "extraction_path": self.pbo_extraction_path.text()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    def browse_dayz_path(self):
        # (existing code)
        self.save_paths()

    def browse_pbo_extraction_path(self):
        # (existing code)
        self.save_paths()

    def browse_dayz_path(self):
        self.dayz_path = QFileDialog.getExistingDirectory(self, "Select DayZ Installation Path")
        self.dayz_path_edit.setText(self.dayz_path)
        self.update_roads_paths_message()

    def browse_pbo_extraction_path(self):
        selected_path = QFileDialog.getExistingDirectory(self, "Select PBO Extraction Path")
        if selected_path:
            self.pbo_extraction_path.setText(selected_path)
            self.update_roads_paths_message()

    def update_roads_paths_message(self):
        if self.dayz_path and self.pbo_extraction_path.text():
            self.roads_paths_message.setText(os.path.join(self.pbo_extraction_path.text(), "roads"))

    def extract_roads(self):
        if not self.dayz_path or not self.pbo_extraction_path.text():
            return

        output_path = os.path.join(self.pbo_extraction_path.text(), "roads")
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        dz_roads_pbo = os.path.join(self.dayz_path, "Addons", "structures_roads.pbo")
        bliss_roads_pbo = os.path.join(self.dayz_path, "Bliss", "Addons", "structures_roads_bliss.pbo")

        # Extract DZ roads
        self.dz_roads_progress.setValue(0)
        self.dz_roads_progress.setMaximum(50)
        temp_dz_roads = os.path.join(self.pbo_extraction_path.text(), "temp", "dz_roads")
        os.system(f'extractpbo -P -Y "{dz_roads_pbo}" "{temp_dz_roads}"')
        shutil.copytree(os.path.join(temp_dz_roads, "DZ", "structures", "roads", "Parts"), os.path.join(output_path, "dz_roads"))
        self.dz_roads_progress.setValue(50)

        # Extract Bliss roads if they exist
        if os.path.exists(bliss_roads_pbo):
            self.bliss_roads_progress.setValue(0)
            self.bliss_roads_progress.setMaximum(50)
            temp_bliss_roads = os.path.join(self.pbo_extraction_path.text(), "temp", "bliss_roads")
            os.system(f'extractpbo -P -Y "{bliss_roads_pbo}" "{temp_bliss_roads}"')
            shutil.copytree(os.path.join(temp_bliss_roads, "DZ", "structures_bliss", "roads", "Parts"), os.path.join(output_path, "bliss_roads"))
            self.bliss_roads_progress.setValue(50)

        # Remove temporary directories
        shutil.rmtree(os.path.join(self.pbo_extraction_path.text(), "temp", "dz_roads"), ignore_errors=True)
        shutil.rmtree(os.path.join(self.pbo_extraction_path.text(), "temp", "bliss_roads"), ignore_errors=True)

    # (remaining code here)


        # Close the window
        self.close()

    def close(self):
        self.destroy()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = ExtractRoadsWidget()
    widget.setWindowTitle("Extract Vanilla Binarized Roads")
    widget.show()
    sys.exit(app.exec_())
