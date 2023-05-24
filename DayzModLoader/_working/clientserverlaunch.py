import os
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit

class DayZLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Define the window size and title
        self.setGeometry(100, 100, 400, 200)
        self.setWindowTitle('DayZDiag Launcher')

        # Create a central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create a folder selection button and label
        folder_layout = QHBoxLayout()
        folder_label = QLabel('DayZDiag_x64 Folder:')
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        folder_button = QPushButton('Select Folder', self)
        folder_button.clicked.connect(self.selectFolder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(folder_button)

        # Add the folder selection widgets to the layout
        layout.addLayout(folder_layout)

        # Add a launch button to the layout
        launch_button = QPushButton('Launch DayZ', self)
        launch_button.clicked.connect(self.launchDayZ_Diag)
        layout.addWidget(launch_button)

        # Show the window
        self.show()

    def selectFolder(self):
        # Use a file dialog to select the folder containing DayZDiag_x64.exe
        folder_path = QFileDialog.getExistingDirectory(self, "Select DayZDiag_x64 Folder")
        self.folder_edit.setText(folder_path)

    def launchDayZ_Diag(self):
        # Get the DayZDiag_x64 folder path
        folder_path = self.folder_edit.text()

        # Path to DayZDiag_x64.exe
        dayz_path = os.path.join(folder_path, "DayZDiag_x64.exe")

        # Mods to load
        MODS = "E:\\SteamLibrary\\steamapps\\common\\DayZServer\\@CF;E:\\SteamLibrary\\steamapps\\common\\DayZServer\\@Community-Online-Tools;E:\\SteamLibrary\\steamapps\\common\\DayZServer\\@SkyZ;E:\\SteamLibrary\\steamapps\\common\\DayZServer\\@korovy"

        # Diag server config
        SERVERCFG = "E:\\SteamLibrary\\steamapps\\common\\DayZServer\\serverDZ_korovy.cfg"

        # Mission path (diag server)
        MISSION = "E:\\SteamLibrary\\steamapps\\common\\DayZServer\\mpmissions\\mission.Korovy"

        # Local host IP
        LOCALHOST = "127.0.0.1:2302"

        # Change the current working directory to the DayZDiag_x64 folder
        os.chdir(folder_path)

        # Start DayZDiag_x64.exe with the specified arguments
        os.system(f'start {dayz_path} -nonavmesh -mod={MODS} -profiles=!ClientDiagLogs -battleye=0 -connect={LOCALHOST}')
        os.system(f'start {dayz_path} -nonavmesh -server -noPause -doLogs -mission={MISSION} -config={SERVERCFG} -profiles=!ServerDiagLogs -mod={MODS}')

def main():
    app = QApplication([])
    launcher = DayZLauncher()
    app.exec_()

if __name__ == '__main__':
    main()

