import sys, json, os, subprocess, shlex, re
from subprocess import CalledProcessError
from pathlib import Path
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt 
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox, QInputDialog, QTableWidget, QCheckBox
from json_io  import load_mods, save_mods, store_dz_config, load_configs, load_paths, save_paths
from server_options import ServerOptions

class ModLoaderApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DZServer Loader")

        # Constants
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        self.MODS_JSON_PATH = os.path.join(script_dir, "data", "mods.json")
        self.PATHS_JSON_PATH = os.path.join(script_dir, "data", "paths.json")
        # Initialize mods dictionary
        self.mods = {}
        # Load JSON file things
        self.mods = load_mods(self.MODS_JSON_PATH)
        self.configs = load_configs(self.MODS_JSON_PATH)
        # Initialize server path and workshop path
        self.server_path, self.workshop_path = load_paths(self.PATHS_JSON_PATH)
        self.server_path, self.workshop_path = "", ""
        #misc declarations
        self.last_mod_path = ""
        self.previous_mod_list_name = ""
        self.server_flags = ""
        self.setMinimumWidth(1000) 
        self.init_ui()
        self.shortened_path_mapping = {}
        self.paths = {}

    def init_ui(self):

        hbox = QtWidgets.QHBoxLayout()
        # Create widgets
        self.mod_list_table = QTableWidget()
        self.mod_list_table.setColumnCount(3)
        self.mod_list_table.setHorizontalHeaderLabels(["Mod Lists","DZConfig", "Server Options"])
        self.mod_list_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.mod_list_table.verticalHeader().setVisible(False)
        self.mod_list_table.setCurrentCell(0, 0)
        self.mod_list_table.currentCellChanged.connect(self.update_mod_and_config_tables)
        # doubleclinkin rename
        self.mod_list_table.itemChanged.connect(self.rename_mod_list)
        self.mod_list_table.itemDoubleClicked.connect(self.store_previous_mod_list_name)
        # modlist buttons
        mod_list_label = QtWidgets.QLabel("Available mod lists:")
        create_modlist_button = QtWidgets.QPushButton("Create new mod list", self)
        create_modlist_button.clicked.connect(self.create_new_mod_list)
        delete_modlist_button = QtWidgets.QPushButton("Delete selected mod list", self)
        delete_modlist_button.clicked.connect(self.delete_mod_list)
        # mod table
        self.mod_table = QTableWidget(self)
        self.mod_table.setColumnCount(3)
        self.mod_table.setHorizontalHeaderLabels(["Mod Name", "Source", ""])
        self.mod_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        self.mod_table.setColumnWidth(0, 200)
        self.mod_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.mod_table.verticalHeader().setVisible(False)
        # mod table buttons
        add_mods_button = QtWidgets.QPushButton("Add mods", self)
        add_mods_button.clicked.connect(self.add_mods)
        remove_mods_button = QtWidgets.QPushButton("Remove selected mods", self)
        remove_mods_button.clicked.connect(self.remove_selected_mod)
        self.select_workshop_button = QtWidgets.QPushButton(f"Select Workshop Path ({self.workshop_path})" if self.workshop_path else "Select Workshop Path")
        self.select_workshop_button.clicked.connect(self.browse_workshop_path)
        self.select_server_button = QtWidgets.QPushButton(f"Select server path ({self.server_path})" if self.server_path else "Select server path")
        self.select_server_button.clicked.connect(self.browse_server_path)
        start_button = QtWidgets.QPushButton("Start server", self)
        start_button.clicked.connect(lambda: self.server_commandline(self.mod_list_table.currentItem().text(), self.server_flags))
        # DZdiag option checkbox
        self.server_checkbox = QtWidgets.QCheckBox("Run as Diag", self)
        self.server_checkbox.setChecked(False)
        self.mods_label = QtWidgets.QLabel(self)
        # Add mod list names to the table
        mod_names = list(self.mods.keys())
        self.mod_list_table.setRowCount(len(mod_names))
        for i, mod_name in enumerate(mod_names):
            item = QtWidgets.QTableWidgetItem(mod_name)
            self.mod_list_table.setItem(i, 0, item)
            mod_list = self.mods[mod_name]
            dzconfig_path = mod_list.get("dz_config")
            button_text = os.path.basename(dzconfig_path) if dzconfig_path else "Select dzConfig"
            dzconfig_button = QtWidgets.QPushButton(button_text)
            dzconfig_button.clicked.connect(lambda checked, mod_list_item=item, row=i: self.select_dz_config(mod_list_item, row))
            self.mod_list_table.setCellWidget(i, 1, dzconfig_button)
        for row in range(self.mod_list_table.rowCount()):
            button = QtWidgets.QPushButton("Options")
            button.clicked.connect(lambda _, r=row: self.show_server_options(r))
            self.mod_list_table.setCellWidget(row, 2, button)

        # Layout widgets
        mod_table_label = QtWidgets.QLabel("Mods in selected list:")

        # Add widgets to modlist layout
        modlist_vbox = QtWidgets.QVBoxLayout()
        modlist_vbox.addWidget(mod_list_label)
        modlist_vbox.addWidget(self.mod_list_table)
        modlist_button_hbox = QtWidgets.QHBoxLayout()
        modlist_button_hbox.addWidget(create_modlist_button)
        modlist_button_hbox.addWidget(delete_modlist_button)
        modlist_vbox.addLayout(modlist_button_hbox)

        # Add widgets to mod layout
        mods_vbox = QtWidgets.QVBoxLayout()
        mods_vbox.addWidget(mod_table_label)
        mods_vbox.addWidget(self.mod_table)
        add_mods_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        remove_mods_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        mod_button_hbox = QtWidgets.QHBoxLayout()
        mod_button_hbox.addWidget(add_mods_button)
        mod_button_hbox.addWidget(remove_mods_button)
        mods_vbox.addLayout(mod_button_hbox)

        # Add server and label widgets
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.select_workshop_button)
        vbox.addWidget(self.select_server_button)
        vbox.addWidget(start_button)
        vbox.addWidget(self.server_checkbox)    
        #vbox.addWidget(start_client_button)

        hbox.addLayout(modlist_vbox)
        vbox.addSpacing(20) 
        hbox.addLayout(mods_vbox)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

 # defs
    @property
    def DEFAULT_DZCONFIG_PATH(self):
                if self.server_path:
                    return os.path.join(self.server_path, "serverDZ.cfg")
                return None

    @property
    def DEFAULT_SERVER_PROFILE_PATH(self):
        if self.server_path:
            return os.path.join(self.server_path, "profile")
        return None
    
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
                # extract the target path from the output
                output = self.streamdata.decode()
                target = re.search(r"Substitute Name: (.*)\n", output).group(1).strip()
                return target

        return None
 
    def show_server_options(self, row):
        mod_list_name = self.mod_list_table.item(row, 0).text()
        if not mod_list_name:
            QMessageBox.critical(None, "Error", "Please select a mod list.")
            return

        server_options_dialog = ServerOptions(self)
        server_options = self.mods.get(mod_list_name, {}).get("server_options", {})
        server_options_dialog.set_profiles_path(server_options.get("profiles_path", ""))
        server_options_dialog.set_mission_path(server_options.get("mission_path", ""))

        # Set the checkboxes
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
            # Update the server options in the self.mods dictionary
            self.mods[mod_list_name]["server_options"] = {
                "profiles_path": server_options_dialog.profiles_path_edit.text(),
                "mission_path": server_options_dialog.mission_path_edit.text(),
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

            # Save the updated mods data to the JSON file
            save_mods(self.MODS_JSON_PATH, self.mods)

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
      
    def select_dz_config(self, mod_list_item, row):
        mod_list_name = mod_list_item.text()
        dzconfig_path, _ = QFileDialog.getOpenFileName(self, "Select Server Config file", "", "cfg (*.cfg)")
        if dzconfig_path:
            mod_list = self.mods[mod_list_name]
            mod_list["dz_config"] = dzconfig_path
            save_mods(self.MODS_JSON_PATH, self.mods)
            self.update_mod_and_config_tables()
            # Update the button text
            button = self.mod_list_table.cellWidget(row, 1)
            button.setText(os.path.basename(dzconfig_path))
    
    def setup_mod_table(self):
        self.mod_table.setColumnCount(2)
        self.mod_table.setHorizontalHeaderLabels(["Mod Name", "Mod Path"])
        self.mod_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    def save_server_path(self):
        save_paths(self.PATHS_JSON_PATH, self.server_path, self.workshop_path)

    def save_workshop_path(self):
        save_paths(self.PATHS_JSON_PATH, self.server_path, self.workshop_path)

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
                mod_name = os.path.basename(mod_path)
                mod_symlink_path = os.path.join(self.server_path, mod_name)
                is_symlink = os.path.islink(mod_symlink_path)

                if not self.symlink_exists_in_other_mod_lists(mod_list_name, mod_symlink_path):
                    if not is_symlink:
                        try:
                            subprocess.check_call('mklink /J "%s" "%s"' % (mod_symlink_path, mod_path), shell=True)
                        except CalledProcessError as e:
                            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to create symlink: {e}")
                    else:
                        print(f"Symlink already exists: {mod_symlink_path}")

                # Print the original mod path from the symlink
                original_mod_path = os.readlink(mod_symlink_path)
                print(f"Original mod path: {original_mod_path}")
                mod_list_mods.append(mod_symlink_path)

            mod_list["mods"] = mod_list_mods
            self.mods[mod_list_name] = mod_list
            save_mods(self.MODS_JSON_PATH, self.mods)
            self.update_mod_and_config_tables()

        print("Done adding mods")

    def remove_selected_mod(self):
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
            for path in mod_list_mods:
                if os.path.basename(path) == mod_name:
                    mod_symlink_path = path
                    break

            if not mod_symlink_path:
                QtWidgets.QMessageBox.warning(self, "Error", "Could not find the symlink path for the selected mod.")
                return

            # Remove the mod from the mods dictionary
            mod_list_mods.remove(mod_symlink_path)
            mod_list["mods"] = mod_list_mods
            self.mods[mod_list_name] = mod_list

            # Save the updated mods dictionary to the JSON file
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
      
    def symlink_exists_in_other_mod_lists(self, mod_list_name, symlink):
        for list_name, mod_list in self.mods.items():
            if list_name != mod_list_name:
                for mod in mod_list.get("mods", []):
                    if os.path.basename(symlink) == os.path.basename(mod):
                        return True
                    elif self.is_symlink_or_junction(mod) and os.path.basename(symlink) == os.path.basename(os.readlink(mod)):
                        return True
        return False

    def save_mods(self):
        with open(self.MODS_JSON_PATH, "w") as f:
            json.dump(self.mods, f)
    
    def shorten_mod_path(self, mod_path):
        # Normalize path separators
        mod_path = os.path.normpath(mod_path).replace('\\', '/')
        workshop_path_normalized = os.path.normpath(self.workshop_path).replace('\\', '/')

        if mod_path.startswith(workshop_path_normalized):
            return mod_path.replace(workshop_path_normalized, "!workshop", 1)
        elif mod_path.startswith("P:"):
            return mod_path.replace("P:", "!local", 1)
        return mod_path

    def update_mod_and_config_tables(self):
        mod_list_name = self.get_selected_mod_list_name()
        self.mod_table.setRowCount(0)
        if mod_list_name:
            self.mods_label.setText("Mods in " + mod_list_name + " list:")
            mod_list = self.mods.get(mod_list_name, {})
            mod_list_mods = mod_list.get("mods", [])
            print(f"mod_list_mods: {mod_list_mods}")
            self.mod_table.setRowCount(len(mod_list_mods))

            for row, mod_path in enumerate(mod_list_mods):
                mod_name = os.path.basename(mod_path)
                mod_name_item = QtWidgets.QTableWidgetItem(mod_name)

                # Check if the mod path is a symbolic link or a junction
                is_symlink_or_junction = False
                if os.path.islink(mod_path):
                    is_symlink_or_junction = True
                elif os.path.isdir(mod_path):
                    child = subprocess.Popen(
                        'fsutil reparsepoint query "{}"'.format(mod_path),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True
                    )
                    self.streamdata = child.communicate()[0]
                    rc = child.returncode

                    if rc == 0:
                        is_symlink_or_junction = True

                if is_symlink_or_junction:
                    original_source = os.readlink(mod_path)
                    original_source = original_source.replace('\\\\?\\', '', 1)  # Strip the leading '\\?\\'
                    shortened_original_source = self.shorten_mod_path(original_source)
                    original_source_item = QtWidgets.QTableWidgetItem(shortened_original_source)
                    original_source_item.setData(Qt.UserRole, original_source)  # Store the original symlink path
                    self.mod_table.setItem(row, 1, original_source_item)
                else:
                    mod_path = mod_path.replace('\\\\?\\', '', 1)  # Strip the leading '\\?\\'
                    shortened_mod_path = self.shorten_mod_path(mod_path)
                    mod_path_item = QtWidgets.QTableWidgetItem(shortened_mod_path)
                    self.mod_table.setItem(row, 1, mod_path_item)

                self.mod_table.setItem(row, 0, mod_name_item)
        else:
            self.mods_label.setText("No mod list selected.")

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
            selection = self.mod_list_table.currentIndex()
            if selection.isValid():
                mod_list_name = self.mod_list_table.item(selection.row(), 0).text()
                self.mod_list_table.removeRow(selection.row())
                del self.mods[mod_list_name]
                self.save_mods()

    def create_new_mod_list(self):
        mod_list_name, ok = QInputDialog.getText(self, "Create new mod list", "Enter mod list name:")
        if ok and mod_list_name:
            if mod_list_name in self.mods:
                QMessageBox.critical(self, "Error", "Mod list with the same name already exists.")
            else:
                self.mods[mod_list_name] = {}  # Added empty dictionary here
                save_mods(self.MODS_JSON_PATH, self.mods)
                row_count = self.mod_list_table.rowCount()
                self.mod_list_table.setRowCount(row_count + 1)
                item = QtWidgets.QTableWidgetItem(mod_list_name)
                self.mod_list_table.setItem(row_count, 0, item)
                save_mods(self.MODS_JSON_PATH, self.mods)
                self.update_mod_and_config_tables()
    
    @staticmethod
    def remove_prefix(s, prefix):
        return s[len(prefix):] if s.startswith(prefix) else s
    
    def server_commandline(self, mod_list_name, server_flags):
        mod_list_name = self.get_selected_mod_list_name()
        if not mod_list_name:
            QMessageBox.critical(None, "Error", "Please select a mod list.")
            return

        mod_list = self.mods[mod_list_name]
        mod_list_mods = mod_list.get("mods", [])
        if not mod_list_mods:
            QMessageBox.critical(None, "Error", "The selected mod list is empty.")
            return

        # Combine all the mod names into a single string, surrounded by double quotes
        stripped_mod_paths = [self.remove_prefix(mod_path, "\\\\?\\").replace('\\', '/', -1) for mod_path in mod_list_mods]
        mod_names = ";".join(stripped_mod_paths)
        # Get server options
        server_options = self.mods.get(mod_list_name, {}).get("server_options", {})
        mission_path = server_options.get("mission_path", "")
        profiles_path = server_options.get("profiles_path", "")
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

        # Get the path to the dzconfig.cfg file
        dz_config_path = server_options.get("dz_config", "")


        # Construct the command line with defaults because we need dzdiag to run as server
        mission_path = os.path.normpath(mission_path)
        dz_config_path = os.path.normpath(dz_config_path)
        profiles_path = os.path.normpath(profiles_path)
        mod_names = ";".join(os.path.normpath(mod_path) for mod_path in mod_list_mods)

        server_profile_path = self.DEFAULT_SERVER_PROFILE_PATH

        if self.server_checkbox.isChecked():
            server_exe = "DayZDiag_x64.exe"
        else:
            server_exe = "DayZServer_x64.exe"

        cmd = (
            f'{server_exe} '
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

       # Show the command line in a message box
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle("Command Line")
        msg_box.setText("The command line to start the server is:")
        msg_box.setDetailedText(cmd)
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg_box.setInformativeText(cmd)  # Show the command line by default
        msg_box.button(QMessageBox.Ok).clicked.connect(lambda: self.run_server_command(cmd))  # Pass the command line to the function
        msg_box.exec_()
    # run the server + client if diag is checked
    def run_server_command(self, cmd):
        mod_list_name = self.get_selected_mod_list_name()
        if not mod_list_name:
            QMessageBox.critical(None, "Error", "Please select a mod list.")
            return

        dayz_folder_path = os.path.abspath(os.path.join(self.workshop_path, "..", "..", "DayZ"))
        print("checking:", dayz_folder_path)

        # Check for diag logic
        if not self.server_checkbox.isChecked():
            dayz_folder_path = self.server_path
            print(dayz_folder_path)
        os.chdir(dayz_folder_path)

        # Split the command string using shlex
        cmd_list = shlex.split(cmd)

        print(f"cmd: {cmd}")
        print(f"cmd_list: {cmd_list}")

        # Use subprocess.Popen to start the server process
        subprocess.Popen(cmd_list, cwd=dayz_folder_path)

        # Launch the client if diag is true
        if self.server_checkbox.isChecked():
            self.client_diagx64_commandline()

    def client_diagx64_commandline(self):
        mod_list_name = self.get_selected_mod_list_name()
        if not mod_list_name:
            QMessageBox.critical(None, "Error", "Please select a mod list.")
            return

        mod_list = self.mods[mod_list_name]
        mod_list_mods = mod_list.get("mods", [])
        if not mod_list_mods:
            QMessageBox.critical(None, "Error", "The selected mod list is empty.")
            return

        # Combine all the mod names into a single string, add any server options
        stripped_mod_paths = [self.remove_prefix(mod_path, "\\\\?\\").replace('\\', '/', -1) for mod_path in mod_list_mods]
        mod_names = ";".join(stripped_mod_paths)
         # Get server options
        server_options = self.mods.get(mod_list_name, {}).get("server_options", {})
        nonavmesh = server_options.get("nonavmesh", False)

        cmd = (
            f'{("-nonavmesh" if nonavmesh else "")} '
        )

        # Construct the command line with some constants
        cmd = (f'DayZDiag_x64.exe {-nonavmesh} -profiles=!ClientDiagLogs -battleye=0 -connect=localhost:2302 "-mod={mod_names}"')

        # Launch the DayZ client with the command line options
        client_exe_path = os.path.join(self.workshop_path, "..", "..", "DayZ", "DayZDiag_x64.exe")
        print(f"Client executable path: {client_exe_path}")

        os.chdir(os.path.dirname(client_exe_path))
        cmd = cmd.replace("DayZDiag_x64.exe", "").strip()
        import shlex
        cmd_list = shlex.split(cmd)
        cmd_list.insert(0, client_exe_path)
        subprocess.Popen(cmd_list)

    def launch_client(self, cmd):
        client_exe_path = os.path.join(self.workshop_path, "..", "..", "DayZ", "DayZDiag_x64.exe")
        os.chdir(os.path.dirname(client_exe_path))
        cmd = cmd.replace("DayZDiag_x64.exe", "").strip()
        import shlex
        cmd_list = shlex.split(cmd)
        cmd_list.insert(0, client_exe_path)
        subprocess.Popen(cmd_list)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = ModLoaderApp()
    window.show()
    sys.exit(app.exec_())