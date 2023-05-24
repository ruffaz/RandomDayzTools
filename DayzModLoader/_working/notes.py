*client normal
move -nonavemsh into client parameter and also connect=localhost


*diag
needs additional parameter missions=missions folder
all mods and paths must be absolute

*server 
define ip address?
move dzconfig browser and field into parameters dialog
make the dzconfigbutton a "run modlist" button -> dialog that opens with two buttons run server + run client


def launch_dayz_diag(self):
    mod_list_name = self.get_selected_mod_list_name()
    if not mod_list_name:
        QMessageBox.critical(None, "Error", "Please select a mod list.")
        return

    mod_list = self.mods[mod_list_name]
    mod_list_mods = mod_list.get("mods", [])
    if not mod_list_mods:
        QMessageBox.critical(None, "Error", "The selected mod list is empty.")
        return

    mission_name = mod_list.get("mission_name", "")
    if not mission_name:
        QMessageBox.critical(None, "Error", "Mission name not found.")
        return

    stripped_mod_paths = [self.remove_prefix(mod_path, "\\\\?\\").replace('\\', '/', -1) for mod_path in mod_list_mods]
    mods = ";".join(stripped_mod_paths)

    diag_folder_path = os.path.join(self.server_path, "..", "DayZ", "DayZDiag_x64")
    dayz_path = os.path.join(diag_folder_path, "DayZDiag_x64.exe")

    server_cfg = os.path.join(self.server_path, "serverDZ.cfg")
    mission = os.path.join(self.server_path, "mpmissions", mission_name)

    localhost = "127.0.0.1:2302"

    os.chdir(diag_folder_path)

    os.system(f'start {dayz_path} -nonavmesh -mod={mods} -profiles=!ClientDiagLogs -battleye=0 -connect={localhost}')
    os.system(f'start {dayz_path} -nonavmesh -server -noPause -doLogs -mission={mission} -config={server_cfg} -profiles=!ServerDiagLogs -mod={mods}')
