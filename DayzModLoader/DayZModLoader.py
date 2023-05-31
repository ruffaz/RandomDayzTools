# Desc: A GUI for loading mods for DayZ Standalone server, and a useful switch to launch dayzdiag_x64.exe as server-client 
# Uses Junctions to populate the Server folder with mods from the Workshop amd local mods folders
# Lots of hardcoded assumptions that suit the purpose of the author


__author__ = "Az"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "ruffazguts@gmail.com"
__status__ = "Proto"

import sys, json, os, subprocess, shlex, re, copy
from subprocess import CalledProcessError
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox, QInputDialog, QTableWidget, QMainWindow, QComboBox, QLabel, QPushButton, QHeaderView,QVBoxLayout, QHBoxLayout, QGroupBox
from json_io  import load_mods, save_mods, load_paths, save_paths, load_configs
from server_options import ServerOptions

import qtmodern.styles
import qtmodern.windows

class ModLoaderMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DZMod Loader")
        self.setMinimumWidth(1000)
        # Create an instance of ModLoaderApp
        self.mod_loader_app = ModLoaderApp()
        # Set the central widget of the main window to ModLoaderApp
        self.setCentralWidget(self.mod_loader_app)

class ModLoaderApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DZModLoader")
        # Pathing for json data
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        self.MODS_JSON_PATH = os.path.join(script_dir, "data", "mods.json")
        self.PATHS_JSON_PATH = os.path.join(script_dir, "data", "paths.json")
        # Initialize 
        self.mods = {}
        self.paths = {}
        # Load data
        self.mods = load_mods(self.MODS_JSON_PATH)
        self.server_path, self.workshop_path = "", ""
        self.server_path, self.workshop_path = load_paths(self.PATHS_JSON_PATH)
        self.configs = load_configs(self.MODS_JSON_PATH)
        self.last_mod_path = ""
        self.previous_mod_list_name = ""
        self.server_flags = ""
        self.setMinimumWidth(1000) 
        self.init_ui()
        self.shortened_path_mapping = {}
        # Initialize paths dictionary
        self.paths = {}
        self.create_data_folder()

    def init_ui(self):

        self.mod_list_table = QTableWidget()
        self.mod_list_table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.mod_list_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.mod_list_table.setColumnCount(2)
        self.mod_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mod_list_table.setHorizontalHeaderLabels(["Mod Lists", "Server Options"])

        self.mod_list_table.verticalHeader().setVisible(False)
        self.mod_list_table.setCurrentCell(0, 0)
        self.mod_list_table.currentCellChanged.connect(self.update_mod_and_config_tables)
        self.mod_list_table.itemChanged.connect(self.rename_mod_list)
        self.mod_list_table.itemDoubleClicked.connect(self.store_previous_mod_list_name)
        self.mod_list_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.mod_list_table.setMinimumWidth(400)
        self.mod_list_table.setMaximumWidth(int(self.width() * 0.3))

        mod_list_label = QLabel("Available Mod Lists:")
        create_modlist_button = QPushButton("Create New", self)
        create_modlist_button.clicked.connect(self.create_new_mod_list)
        delete_modlist_button = QPushButton("Delete Selected", self)
        delete_modlist_button.clicked.connect(self.delete_mod_list)
        duplicate_modlist_button = QPushButton("Duplicate Selected", self)
        duplicate_modlist_button.clicked.connect(self.duplicate_mod_list)

        self.mod_table = QTableWidget(self)
        self.mod_table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.mod_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.mod_table.setColumnCount(3)
        self.mod_table.setHorizontalHeaderLabels(["Mod Name", "Source", "Remove from Modlist"])

        self.mod_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mod_table.verticalHeader().setVisible(False)
        self.mod_table.setCurrentCell(0, 0)
        self.mod_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.mod_table.setMinimumWidth(300)
        self.mod_table.setMaximumWidth(int(self.width() * 1))

        add_mods_button = QPushButton("Add mods", self)
        add_mods_button.clicked.connect(self.add_mods)

        self.select_workshop_button = QPushButton(f"Workshop Path ({self.workshop_path})" if self.workshop_path else "Workshop Path")
        self.select_workshop_button.clicked.connect(self.browse_workshop_path)
        self.select_server_button = QPushButton(f"Server Path ({self.server_path})" if self.server_path else "Server Path")
        self.select_server_button.clicked.connect(self.browse_server_path)


        self.function_combobox = QComboBox()
        self.function_combobox.addItem("Server Only")
        self.function_combobox.addItem("Diag_x64 Combo")
        self.function_combobox.addItem("Client Only")
        default_index = 1
        self.function_combobox.setCurrentIndex(default_index)

        self.function_combobox.currentIndexChanged.connect(self.update_start_button_text)

        self.mods_label = QLabel(self)
        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(lambda: self.server_commandline(self.mod_list_table.currentItem().text()) if self.mod_list_table.currentItem() else QMessageBox.warning(self, "Warning", "Please select a mod list before starting the server."))

        layout = QVBoxLayout()
        layout.addWidget(self.function_combobox)
        layout.addWidget(self.mods_label)
        layout.addWidget(self.start_button)


        # Add mod list names to the table
        mod_names = list(self.mods.keys())
        self.mod_list_table.setRowCount(len(mod_names))
        for i, mod_name in enumerate(mod_names):
            item = QtWidgets.QTableWidgetItem(mod_name)
            self.mod_list_table.setItem(i, 0, item)
            mod_list = self.mods[mod_name]
            dzconfig_path = mod_list.get("dz_config")
            button_text = os.path.basename(dzconfig_path) if dzconfig_path else "Select dzConfig"
            dzconfig_button = QPushButton(button_text)
            dzconfig_button.clicked.connect(lambda checked, mod_list_item=item, row=i: self.select_dz_config(mod_list_item, row))
            self.mod_list_table.setCellWidget(i, 1, dzconfig_button)

        for row in range(self.mod_list_table.rowCount()):
            button = QPushButton("Options")
            button.clicked.connect(lambda _, r=row: self.show_server_options(r))
            self.mod_list_table.setCellWidget(row, 1, button)

       
        # modlist layout
        modlist_vbox = QVBoxLayout()
        modlist_vbox.addWidget(mod_list_label)
        modlist_vbox.addWidget(self.mod_list_table)
        modlist_button_hbox = QHBoxLayout()
        modlist_button_hbox.addWidget(create_modlist_button)
        modlist_button_hbox.addWidget(delete_modlist_button)
        modlist_button_hbox.addWidget(duplicate_modlist_button)
        modlist_vbox.addLayout(modlist_button_hbox)

        # mod layout server_options_vbox.addWidget(self.mods_label)
        mods_vbox = QVBoxLayout()
        mods_vbox.addWidget(self.mods_label)
        mods_vbox.addWidget(self.mod_table)
        mod_button_hbox = QHBoxLayout()
        mod_button_hbox.addWidget(add_mods_button)
        mods_vbox.addLayout(mod_button_hbox)

        # Server options
        server_box = QGroupBox("Server Options")
        server_options_vbox = QHBoxLayout(server_box)
       
        server_options_vbox.addWidget(self.select_workshop_button)
        server_options_vbox.addWidget(self.select_server_button)

        server_checkbox_hbox = QHBoxLayout()
        server_options_vbox.addLayout(server_checkbox_hbox)
        server_options_vbox.addWidget(self.function_combobox)
        server_options_vbox.addWidget(self.mods_label)
        server_options_vbox.addWidget(self.start_button)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

        # Add widgets to main layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addSpacerItem(QtWidgets.QSpacerItem(0, 40))  # Add 20 pixels of vertical space
        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(modlist_vbox)
        hbox.addLayout(mods_vbox)
        vbox.addLayout(hbox)
        vbox.addSpacerItem(QtWidgets.QSpacerItem(0, 0))  # Add 20 pixels of vertical space
        vbox.addWidget(server_box)
        self.setLayout(vbox)
        
        # Version label not auto
        version_label = QLabel("Version: 1.0.1") 
        version_label.setAlignment(Qt.AlignRight) 
        vbox.addWidget(version_label)


# defs general

    def update_start_button_text(self, index):
        selected_option = self.function_combobox.currentText()

        if selected_option == "Server Only":
            self.start_button.setText("Start Server")
        elif selected_option == "Diag_x64 Combo":
            self.start_button.setText("Start Diag_x64")
        elif selected_option == "Client Only":
            self.start_button.setText("Start Client")

    def create_data_folder(self):
            data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            if not os.path.exists(data_folder):
                os.makedirs(data_folder)
    @staticmethod
    def remove_prefix(s, prefix):
        return s[len(prefix):] if s.startswith(prefix) else s
       
    def is_symlink_or_junction(self, path):
        if os.path.islink(path):
            return os.readlink(path)
        elif os.path.isdir(path):
            child = subprocess.Popen(
                'fsutil reparsepoint query "{}"'.format(path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
            self.streamdata = child.communicate()[0]
            rc = child.returncode

            if rc == 0:
                # extract target path from the output
                output = self.streamdata.decode()
                target = re.search(r"Substitute Name: (.*)\n", output).group(1).strip()
                return target

        return None
         
    def browse_workshop_path(self):
        workshop_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select workshop path")
        if workshop_path:
            self.workshop_path = workshop_path
            self.paths = {"server_path": self.server_path, "workshop_path": self.workshop_path}
            save_paths(self.PATHS_JSON_PATH, self.paths)
            self.select_workshop_button.setText(f"Select Workshop Path ({self.workshop_path})")
    
    def browse_server_path(self):
        server_path = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Server Path"))
        if server_path:
            self.server_path = server_path
            self.paths["server_path"] = server_path
            save_paths(self.PATHS_JSON_PATH, self.paths)
            self.select_server_button.setText(f"Select server path ({self.server_path})")
         
    def save_server_path(self):
        save_paths(self.PATHS_JSON_PATH, self.server_path, self.workshop_path)

    def save_workshop_path(self):
        save_paths(self.PATHS_JSON_PATH, self.server_path, self.workshop_path)

# defs mods
    def add_mods(self):
        mod_list_name = self.get_selected_mod_list_name()
        if not mod_list_name:
            QMessageBox.critical(self, "Error", "Please select a mod list.")
            return
        
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        file_dialog.setOption(QFileDialog.ShowDirsOnly, True)

        if file_dialog.exec_():
            selected_mod_paths = file_dialog.selectedFiles()
            mod_list = self.mods.get(mod_list_name, {})
            mod_list_mods = mod_list.get("mods", [])

            for mod_path in selected_mod_paths:
                print(mod_path)
                mod_name = os.path.basename(mod_path)
                mod_symlink_path = os.path.join(self.server_path, mod_name)
                is_symlink = os.path.islink(mod_symlink_path)

                if not self.symlink_exists_in_other_mod_lists(mod_list_name, mod_symlink_path):
                    if not is_symlink:
                        if os.path.commonprefix([mod_path, self.server_path]) == self.server_path:
                            QtWidgets.QMessageBox.warning(self, "Error", "Cannot add a mod that is in the server path. Please use mods from the !Workshop folder or your local P: drive.")
                            continue
                        try:
                            subprocess.check_call('mklink /J "%s" "%s"' % (mod_symlink_path, mod_path), shell=True)
                        except subprocess.CalledProcessError as e:
                            if e.returncode != 1:
                                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to create symlink: {e}")

                # Adding this outside the if condition to ensure that the mod path is always added to the mod_list_mods list.
                if mod_path not in mod_list_mods:
                    mod_list_mods.append(mod_path)

            mod_list["mods"] = mod_list_mods
            self.mods[mod_list_name] = mod_list
            save_mods(self.MODS_JSON_PATH, self.mods)

            self.update_mod_and_config_tables()

        print("Done adding mods")

    def remove_selected_mod(self, row):
        mod_list_name = self.get_selected_mod_list_name()
        if not mod_list_name:
            QMessageBox.critical(self, "Error", "Please select a mod list.")
            return

        selection = self.mod_table.currentIndex()
        if selection.isValid():
            row = selection.row()
            mod_name = self.mod_table.item(row, 0).text()

            mod_list = self.mods[mod_list_name]
            mod_list_mods = mod_list.get("mods", [])

            mod_symlink_path = ""
            mod_to_remove = ""
            for path in mod_list_mods:
                if os.path.basename(path) == mod_name:
                    mod_symlink_path = os.path.join(self.server_path, mod_name)
                    mod_to_remove = path
                    break

            if not mod_symlink_path or not mod_to_remove:
                QtWidgets.QMessageBox.warning(self, "Error", "Could not find the symlink path for the selected mod.")
                return

            # Remove the mod from the mods dict
            mod_list_mods.remove(mod_to_remove)
            mod_list["mods"] = mod_list_mods
            self.mods[mod_list_name] = mod_list

            # Save the updated mods dict
            save_mods(self.MODS_JSON_PATH, self.mods)

            # Check if the symlink is used in other mod lists
            if not self.symlink_exists_in_other_mod_lists(mod_list_name, mod_symlink_path):
            # Remove the junction if it's not used in other mod lists
                try:
                    subprocess.run(f'rmdir "{mod_symlink_path}"', shell=True, check=True)
                except subprocess.CalledProcessError as e:
                    QtWidgets.QMessageBox.warning(self, "Error", f"Failed to remove junction: {e}")

            # Update the mod table
        self.update_mod_and_config_tables()
      
    def save_mods(self):
        with open(self.MODS_JSON_PATH, "w") as f:
            json.dump(self.mods, f)

    def shorten_mod_path(self, mod_path):
        # Normalize path separators
        mod_path = os.path.normpath(mod_path).replace('\\', '/')
        print(f"Normalized mod_path: {mod_path}")

        if "!Workshop" in mod_path:
            # If it's a symlink, resolve it
            if os.path.islink(mod_path):
                mod_path = os.readlink(mod_path)
                print(f"Resolved symlink: {mod_path}")
                mod_path = os.path.normpath(mod_path).replace('\\', '/')
                print(f"Normalized symlink: {mod_path}")
            
            try:
                # Extract portion of the path from "@" onward
                mod_path = mod_path[mod_path.index("@"):]
                # Prefix with "!workshop"
                return "!workshop" + mod_path
            except ValueError:
                print(f"Warning: '@' symbol not found in mod_path: {mod_path}")
                return mod_path
        elif mod_path.startswith("P:"):
            return mod_path.replace("P:", "!local", 1)
        return mod_path

    def update_mod_and_config_tables(self):
        mod_list_name = self.get_selected_mod_list_name()
        self.mod_table.setRowCount(0)
        if mod_list_name:
            self.mods_label.setText("Mods in " + mod_list_name + " mod list:")
            mod_list = self.mods.get(mod_list_name, {})
            mod_list_mods = mod_list.get("mods", [])
            self.mod_table.setRowCount(len(mod_list_mods))

            for row, mod_path in enumerate(mod_list_mods):
                mod_name = os.path.basename(mod_path)
                mod_name_item = QtWidgets.QTableWidgetItem(mod_name)

                mod_path = mod_path.replace('\\\\?\\', '', 1)  # Strip the leading '\\?\\'
                shortened_mod_path = self.shorten_mod_path(mod_path)
                mod_path_item = QtWidgets.QTableWidgetItem(shortened_mod_path)
               
                self.mod_table.setItem(row, 0, mod_name_item)
                self.mod_table.setItem(row, 1, mod_path_item)

                button = QPushButton("Remove!")
                button.clicked.connect(lambda _, r=row: self.remove_selected_mod(r))
                self.mod_table.setCellWidget(row, 2, button)
        else:
            self.mods_label.setText("No mod list selected.")
   
# defs modlists
  
    def duplicate_mod_list(self):
        mod_list_name = self.get_selected_mod_list_name()
        if not mod_list_name:
            QMessageBox.critical(self, "Error", "Please select a mod list.")
            return

        new_mod_list_name, ok = QInputDialog.getText(self, "Duplicate Mod List",
                                                    "Enter name for the new mod list:")

        if ok and new_mod_list_name:
            if new_mod_list_name in self.mods:
                QMessageBox.warning(self, "Error", "A mod list with that name already exists.")
                return

            new_mod_list = copy.deepcopy(self.mods[mod_list_name])
            self.mods[new_mod_list_name] = new_mod_list
            save_mods(self.MODS_JSON_PATH, self.mods)

            # Populate new row
            row = self.mod_list_table.rowCount()
            self.mod_list_table.insertRow(row)
            item = QtWidgets.QTableWidgetItem(new_mod_list_name)
            self.mod_list_table.setItem(row, 0, item)
            options_button = QPushButton("Options")
            options_button.clicked.connect(lambda _, r=row: self.show_server_options(r))
            self.mod_list_table.setCellWidget(row, 1, options_button)
            # Select the newly duplicated mod list
            self.mod_list_table.setCurrentCell(row, 0)

    def symlink_exists_in_other_mod_lists(self, mod_list_name, symlink):
        for list_name, mod_list in self.mods.items():
            if list_name != mod_list_name:
                for mod in mod_list.get("mods", []):
                    if os.path.basename(symlink) == os.path.basename(mod):
                        return True
                    elif self.is_symlink_or_junction(mod) and os.path.basename(symlink) == os.path.basename(os.readlink(mod)):
                        return True
        return False
    
    def load_mod_list_names(self):
        mod_names = list(self.mods.keys())
        self.mod_list_table.setRowCount(len(mod_names))
        for i, mod_name in enumerate(mod_names):
            item = QtWidgets.QTableWidgetItem(mod_name)
            self.mod_list_table.setItem(i, 0, item)
            options_button = QPushButton("Options")
            options_button.clicked.connect(lambda _, r=i: self.show_server_options(r))
            self.mod_list_table.setCellWidget(i, 2, options_button)

    def get_selected_mod_list_name(self):
            selection = self.mod_list_table.currentIndex()
            if selection.isValid():
                return self.mod_list_table.model().data(selection)
            return None

    def store_previous_mod_list_name(self, clicked_item):
        self.previous_mod_list_name = clicked_item.text()

    def rename_mod_list(self, edited_item):
        new_mod_list_name = edited_item.text()
        
        if self.previous_mod_list_name:
            if new_mod_list_name in self.mods:
                QMessageBox.critical(self, "Error", "Mod list with the same name already exists.")
                edited_item.setText(self.previous_mod_list_name)  # Revert the change
            else:
                self.mods[new_mod_list_name] = self.mods.pop(self.previous_mod_list_name)
                save_mods(self.MODS_JSON_PATH, self.mods)
            self.previous_mod_list_name = ""  # Reset the previous_mod_list_name attribute

    def delete_mod_list(self):
        mod_list_name = self.get_selected_mod_list_name()
        if not mod_list_name:
            QMessageBox.critical(self, "Error", "Please select a mod list.")
            return

        result = QMessageBox.warning(self, "Delete Mod List",
                                    "Delete the mod list '{mod_list_name}'?.\n "
                                    "This will remove all the mods in the mod list, as well as any junctions or symlinks unique to it ",
                                    QMessageBox.Yes | QMessageBox.No)
        if result == QMessageBox.Yes:
            mod_list = self.mods.get(mod_list_name, {})
            mod_list_mods = mod_list.get("mods", [])

            for mod_path in mod_list_mods:
                # mod_symlink_path
                mod_symlink_path = os.path.join(self.server_path, os.path.basename(mod_path))

                if not self.symlink_exists_in_other_mod_lists(mod_list_name, mod_symlink_path):
                    print(f"Mod path to remove: {mod_symlink_path}")  # printing the mod_symlink_path instead
                    try:
                        subprocess.run(f'rmdir "{mod_symlink_path}"', shell=True, check=True)
                    except subprocess.CalledProcessError as e:
                        QtWidgets.QMessageBox.warning(self, "Error", f"Failed to remove junction: {e}")

            del self.mods[mod_list_name]
            save_mods(self.MODS_JSON_PATH, self.mods)
            self.load_mod_list_names()
            self.update_mod_and_config_tables()

    def create_new_mod_list(self):
        # Eliminate lazy users straight off the bat
        if not self.server_path or not self.workshop_path:
            QMessageBox.warning(self, "Error", "Please define the server path and workshop path before adding a mod list.")
            return
        
        mod_list_name, ok = QInputDialog.getText(self, "Create new mod list", "Enter mod list name:")
        if ok and mod_list_name:
            if mod_list_name in self.mods:
                QMessageBox.warning(self, "Warning", "A mod list with this name already exists.")
                return
            
            # Add the new mod list to the mods dict
            self.mods[mod_list_name] = {"mods": [], "dz_config": ""}
            save_mods(self.MODS_JSON_PATH, self.mods)

            # Populate new row
            row = self.mod_list_table.rowCount()
            self.mod_list_table.insertRow(row)
            item = QtWidgets.QTableWidgetItem(mod_list_name)
            self.mod_list_table.setItem(row, 0, item)
            options_button = QPushButton("Options")
            options_button.clicked.connect(lambda _, r=row: self.show_server_options(r))
            self.mod_list_table.setCellWidget(row, 1, options_button)
            # Select the newly created mod list
            self.mod_list_table.setCurrentCell(row, 0)
    
# defs server run
 
    def show_server_options(self, row):
        mod_list_name = self.mod_list_table.item(row, 0).text()
        if not mod_list_name:
            QMessageBox.critical(None, "Error", "Please select a mod list.")
            return
        server_options_dialog = ServerOptions(self.server_path, self)
        server_options = self.mods.get(mod_list_name, {}).get("server_options", {})

         # default values
        default_profiles_path = os.path.join(self.server_path, "DayzServerProfile")
        default_mission_path = os.path.join(self.server_path, "mpmissions", "dayzOffline.ChernarusPlus")
        default_dz_config = os.path.join(self.server_path, "serverDZ.cfg")
        server_options.setdefault("profiles_path", default_profiles_path)
        server_options.setdefault("mission_path", default_mission_path)
        server_options.setdefault("dz_config", default_dz_config)
            
        server_options_dialog = ServerOptions(self.server_path, self)
        server_options = self.mods.get(mod_list_name, {}).get("server_options", {})
        print("Before setting DZConfig:", server_options.get("dz_config", ""))
        server_options_dialog.set_dzconfig_path_edit(server_options.get("dz_config", ""))
        server_options_dialog.set_profiles_path(server_options.get("profiles_path", ""))
        server_options_dialog.set_mission_path(server_options.get("mission_path", ""))

        # Set checkboxes
        server_options_dialog.nonavmesh_checkbox.setChecked(server_options.get("nonavmesh", False))
        server_options_dialog.nosplash_checkbox.setChecked(server_options.get("nosplash", False))
        server_options_dialog.nopause_checkbox.setChecked(server_options.get("no_pause", False))
        server_options_dialog.nobenchmark_checkbox.setChecked(server_options.get("no_benchmark", False))
        server_options_dialog.filepatching_checkbox.setChecked(server_options.get("file_patching", False))
        server_options_dialog.dologs_checkbox.setChecked(server_options.get("do_logs", False))
        server_options_dialog.scriptdebug_checkbox.setChecked(server_options.get("script_debug", False))
        server_options_dialog.adminlog_checkbox.setChecked(server_options.get("admin_log", False))
        server_options_dialog.netlog_checkbox.setChecked(server_options.get("net_log", False))
        server_options_dialog.scrallowfilewrite_checkbox.setChecked(server_options.get("scr_allow_file_write", False))

        if server_options_dialog.exec_() == QtWidgets.QDialog.Accepted:
            print("Mod list name:", mod_list_name)
            print("Current mods:", self.mods)
            print("DZ Config path:", server_options_dialog.dzconfig_path_edit.text())
            # Update server options
            self.mods[mod_list_name]["server_options"] = {
                
                "profiles_path": server_options_dialog.profiles_path_edit.text(),
                "mission_path": server_options_dialog.mission_path_edit.text(),
                "dz_config": server_options_dialog.dzconfig_path_edit.text(),
                "nonavmesh": server_options_dialog.nonavmesh_checkbox.isChecked(),
                "nosplash": server_options_dialog.nosplash_checkbox.isChecked(),
                "no_pause": server_options_dialog.nopause_checkbox.isChecked(),
                "no_benchmark": server_options_dialog.nobenchmark_checkbox.isChecked(),
                "file_patching": server_options_dialog.filepatching_checkbox.isChecked(),
                "do_logs": server_options_dialog.dologs_checkbox.isChecked(),
                "script_debug": server_options_dialog.scriptdebug_checkbox.isChecked(),
                "admin_log": server_options_dialog.adminlog_checkbox.isChecked(),
                "net_log": server_options_dialog.netlog_checkbox.isChecked(),
                "scr_allow_file_write": server_options_dialog.scrallowfilewrite_checkbox.isChecked()
            }
            print("After accepting DZConfig:", server_options_dialog.dzconfig_path_edit.text())
            self.mods[mod_list_name]["server_options"]["dz_config"] = server_options_dialog.dzconfig_path_edit.text()

            save_mods(self.MODS_JSON_PATH, self.mods)
            self.update_mod_and_config_tables()

    def server_commandline(self, mod_list_name):
        mod_list = self.mods[mod_list_name]
        mod_list_mods = mod_list.get("mods", [])
        if not mod_list_mods:
            QMessageBox.critical(None, "Error", "The selected mod list is empty.")
            return

        # Combine mod names into a single string
        stripped_mod_paths = [self.remove_prefix(mod_path, "\\\\?\\").replace('\\', '/', -1) for mod_path in mod_list_mods]
        mod_names = ";".join(stripped_mod_paths)
        # Get server options
        server_options = self.mods.get(mod_list_name, {}).get("server_options", {})
        mission_path = server_options.get("mission_path", "")
        profiles_path = server_options.get("profiles_path", "")
        dz_config_path = server_options.get("dz_config", "")

        print("DZ Config Path:", dz_config_path)
        nonavmesh = server_options.get("nonavmesh", False)
        nosplash = server_options.get("nosplash", False)
        no_pause = server_options.get("no_pause", False)
        no_benchmark = server_options.get("no_benchmark", False)
        file_patching = server_options.get("file_patching", False)
        do_logs = server_options.get("do_logs", False)
        script_debug = server_options.get("script_debug", False)
        admin_log = server_options.get("admin_log", False)
        net_log = server_options.get("net_log", False)
        scr_allow_file_write = server_options.get("scr_allow_file_write", False)
     
        print("Server Options:", server_options)
        # Construct command line
        mission_path = os.path.normpath(mission_path)
        dz_config_path = os.path.normpath(dz_config_path)
        profiles_path = os.path.normpath(profiles_path)
        mod_names = ";".join(os.path.normpath(mod_path) for mod_path in mod_list_mods)
       
        cmd = (
            f'{("-nonavmesh" if nonavmesh else "")} '
            f'{("-nosplash" if nosplash else "")} '
            f'{("-noPause" if no_pause else "")} '
            f'{("-noBenchmark" if no_benchmark else "")} '
            f'{("-FilePatching" if file_patching else "")} '
            f'{("-dologs" if do_logs else "")} '
            f'{("-scriptDebug=true" if script_debug else "")} '
            f'{("-adminlog" if admin_log else "")} '
            f'{("-netlog" if net_log else "")} '
            f'{("-scrAllowFileWrite" if scr_allow_file_write else "")} '
            f'-server '
            f'-mission="{mission_path}" '
            f'-config="{dz_config_path}" '
            f'-profiles="{profiles_path}" '
            f'"-mod={mod_names}" '
        )

        self.run_server_command(cmd)

    def run_server_command(self, mod_list_name):
        # Fetch the selected option from the combobox
        selected_option = self.function_combobox.currentText()

        if selected_option == "Server Only":
            self.run_server(mod_list_name)
        elif selected_option == "Diag_x64 Combo":
            self.run_server(mod_list_name) # passing to server function for now
        elif selected_option == "Client Only":
            self.run_client()
        else:
            QMessageBox.warning(self, "Error", "Please select a valid option from the combobox.")

    def run_server(self, cmd): # call diag in a hacky way here for now - hostnames in dzconfig are not working
        dayz_folder_path = os.path.abspath(os.path.join(self.workshop_path, "..", "..", "DayZ"))
        print("Checking for DayZ folder:", dayz_folder_path)

        # selected option from the combobox
        selected_option = self.function_combobox.currentText()
        if selected_option == "Diag_x64 Combo":
            cmd = "DayZDiag_x64.exe" + cmd
            cmd_list = shlex.split(cmd)
            # server path here is dayz folder path
            os.chdir(dayz_folder_path)
            print("DayZ folder path:", dayz_folder_path)
            subprocess.Popen(cmd_list, cwd=dayz_folder_path)
            # Call run_diagx64 to run in parallel after subprocess has been launched
            self.run_diagx64()
        else:
            cmd = "DayZServer_x64.exe " + cmd
            cmd_list = shlex.split(cmd)
            # switch to actual server path
            os.chdir(self.server_path)
            print("Server path:", self.server_path)
            subprocess.Popen(cmd_list, cwd=self.server_path)

    def run_diagx64(self):
        mod_list_name = self.get_selected_mod_list_name()
        if not mod_list_name:
            QMessageBox.critical(None, "Error", "Please select a mod list.")
            return

        mod_list = self.mods[mod_list_name]
        mod_list_mods = mod_list.get("mods", [])
        if not mod_list_mods:
            QMessageBox.critical(None, "Error", "The selected mod list is empty.")
            return

       # Combine mod names into a single string, add any server options
        stripped_mod_paths = [self.remove_prefix(mod_path, "\\\\?\\").replace('\\', '/', -1) for mod_path in mod_list_mods]
        mod_names = ";".join(stripped_mod_paths)
        # Get limited options from server_options.json
        server_options = self.mods.get(mod_list_name, {}).get("server_options", {})
        nonavmesh = server_options.get("nonavmesh", False)

         # Construct the command line for the client
        cmd_client = (
            f'DayZDiag_x64.exe {-nonavmesh} -profiles=!ClientDiagLogs -battleye=0 -connect=localhost:2302 "-mod={mod_names}"'
        )

        # Find the client exe to run from this directory
        client_exe_path = os.path.join(self.workshop_path, "..", "..", "DayZ", "DayZDiag_x64.exe")
        print(f"Client executable path: {client_exe_path}")

        os.chdir(os.path.dirname(client_exe_path))
        cmd_client = cmd_client.replace("DayZDiag_x64.exe", "").strip()

        import shlex
        cmd_list_client = shlex.split(cmd_client)
        cmd_list_client.insert(0, client_exe_path)

        client_process = subprocess.Popen(cmd_list_client)
        print(f"Client process started with PID: {client_process.pid}")

    def run_client(self): # special case for dayzEditor
        mod_list_name = self.get_selected_mod_list_name()
        if not mod_list_name:
            QMessageBox.critical(None, "Error", "Please select a mod list.")
            return

        mod_list = self.mods[mod_list_name]
        mod_list_mods = mod_list.get("mods", [])
        if not mod_list_mods:
            QMessageBox.critical(None, "Error", "The selected mod list is empty.")
            return

        # Combine mod names into a single string, add any server options
        stripped_mod_paths = [self.remove_prefix(mod_path, "\\\\?\\").replace('\\', '/', -1) for mod_path in mod_list_mods]
        mod_names = ";".join(stripped_mod_paths)
 
        # Construct the command line with some constants
        cmd = (f'DayZ_x64.exe "-mod={mod_names}"')

        # Find the client exe to run from this directory
        client_exe_path = os.path.join(self.workshop_path, "..", "..", "DayZ", "DayZ_x64.exe")
        print(f"Client executable path: {client_exe_path}")

        os.chdir(os.path.dirname(client_exe_path))
        cmd = cmd.replace("DayZ_x64.exe", "").strip()
        import shlex
        cmd_list = shlex.split(cmd)
        cmd_list.insert(0, client_exe_path)
        subprocess.Popen(cmd_list)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    qtmodern.styles.dark(app)
    mw = qtmodern.windows.ModernWindow(ModLoaderMainWindow())
    mw.show()

    sys.exit(app.exec_())
