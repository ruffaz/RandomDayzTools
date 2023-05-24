from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QGridLayout, QComboBox, QLineEdit, QPushButton, QFileDialog, QSizePolicy, QGroupBox, QHBoxLayout, QScrollArea
from PyQt5.QtGui import QColor, QPalette
import json, sys, re
import qtmodern.styles, qtmodern.windows
from functools import partial


class LightingCondition:
    def __init__(self, name, data):
        self.name = name
        for key, value in data.items():
            setattr(self, key, value)

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("DayzLighting Confgurator")
        self.setMinimumSize(800, 800)
        self.conditions = {}  # {condition_name: LightingCondition}
        self.condition_selector = QComboBox()
        self.load_button = QPushButton("Load")
        button = QPushButton('Update lighting config')
        button.clicked.connect(self.update_lighting_config)

        self.condition_selector.currentTextChanged.connect(self.populate_form)
        self.load_button.clicked.connect(self.load_cpp)

        # Layout
        main_layout = QVBoxLayout()
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Selector Group
        selector_group = QGroupBox("Select Class")
        selector_layout = QHBoxLayout()
        selector_group.setLayout(selector_layout)
        selector_layout.addWidget(self.condition_selector)
        main_layout.addWidget(selector_group)

        # Form Group
        form_group = QGroupBox("Class Parameters")
        form_layout = QVBoxLayout()
        form_group.setLayout(form_layout)
        self.form_layout = QGridLayout()
        form_scroll_area = QScrollArea()
        form_scroll_area.setWidgetResizable(True)
        form_widget = QWidget()
        form_widget.setLayout(self.form_layout)
        form_scroll_area.setWidget(form_widget)
        form_layout.addWidget(form_scroll_area)
        main_layout.addWidget(form_group)

        # Button Group
        button_group = QGroupBox()
        button_layout = QHBoxLayout()
        button_group.setLayout(button_layout)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(button)
        main_layout.addWidget(button_group)
       
        self.line_edits = {}

        self.file_path = None  # No file loaded initially
        self.param_notes = {
        'height': 'Altitude in meters for which this settings applies --',
        'overcast': 'Overcast value for which this settings applies --',
        'sunAngle': 'Angle of sun or moon --',
        'sunOrMoon': 'Boolean switch between sun and moon --',
        'diffuse': 'Facing global light (sun / moon) --',
        'diffuseCloud': 'Facing global light (sun / moon) for cloud --',
        'bidirect': 'Opposite of diffuse --',
        'bidirectCloud': 'Opposite of diffuse for cloud --',
        'ambient': 'Shadows --',
        'ambientCloud': 'Shadows for cloud --',
        'groundReflection': 'Illumination from ground --',
        'groundReflectionCloud': 'Illumination from ground for cloud --',
        'sky': 'Affects color of the fog --',
        'skyAroundSun': 'Halo around sun / moon --',
        'desiredLuminanceCoef': 'Luminance --',
        'desiredLuminanceCoefCloud': 'Luminance for cloud --',
        'EVMin': 'Scene gets darker with higher value (default -2.0) --',
        'EVMax': 'Scene gets brighter with higher value (default 0.0) --',
        'filmGrainIntensity': 'Film grain intensity (applied to lower lum px) --'
}

    def load_cpp(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Lighting File", "", " Files (*.txt)")
        if file_path:
            with open(file_path, "r") as file:
                lines = file.readlines()
            self.file_path = file_path
            self.parse_cpp(lines)
            self.condition_selector.clear()
            self.condition_selector.addItems(self.conditions.keys())

    def update_color_preview(self, r_edit, g_edit, b_edit, color_preview):
        r = float(r_edit.text())
        g = float(g_edit.text())
        b = float(b_edit.text())
        color = QColor(int(r*255), int(g*255), int(b*255))
        palette = color_preview.palette()
        palette.setColor(QPalette.Window, color) 
        color_preview.setPalette(palette)

    def parse_cpp(self, lines):
        condition_name = None
        condition_data = {}
        for line in lines:
            print(f"Processing line: {line}")
            class_match = re.match(r'\s*class\s+(\w+)', line)
            if class_match:
                if condition_name is not None:
                    print(f"End of previous condition {condition_name}, adding it to the dictionary")
                    self.conditions[condition_name] = LightingCondition(condition_name, condition_data)
                # Start of a new condition
                condition_name = class_match.group(1)
                condition_data = {}
                print(f"Start of a new condition: {condition_name}")
            else:
                param_match = re.match(r'\s*(\w+)\s*\[\]\s*=\s*((\{.*\}),*\s*[\d\.]*);', line)
                if param_match:
                    print(f"Found an array parameter line")
                    key = param_match.group(1)
                    value = param_match.group(2)
                    nested_braces_and_floats = re.findall(r'\{([^}]+)\}(,\s*[\d\.]+)*', value)
                    if nested_braces_and_floats:
                        print(f"Nested braces and floats found: {nested_braces_and_floats}")
                        value = []
                        for brace, following_float in nested_braces_and_floats:
                            brace_value = [float(x.strip()) for x in brace.strip('{}').split(',')]
                            value.append(brace_value)
                            if following_float:  # check if there is a following float
                                following_float = float(following_float.strip(', '))
                                value.append(following_float)
                    else:
                        try:
                            value = eval(value)  # Try to evaluate as a Python list
                        except SyntaxError:
                            value = [float(x.strip()) for x in value.split(',')]
                    condition_data[key] = value
                    print(f"Added {key} with value {value} to the condition data")

                else:
                    param_match = re.match(r'\s*(\w+)\s*=\s*([^;]+);', line)
                    if param_match:
                        print(f"Found a regular parameter line")
                        # Regular parameter line, add it to the current condition's data
                        key = param_match.group(1)
                        value = param_match.group(2).strip()
                        try:
                            value = float(value)
                        except ValueError:
                            pass  # Keep it as a string if it can't be converted to a float
                        condition_data[key] = value
                        print(f"Added {key} with value {value} to the condition data")
        if condition_name is not None:
            print(f"End of last condition {condition_name}, adding it to the dictionary")
            self.conditions[condition_name] = LightingCondition(condition_name, condition_data)

    def populate_form(self, condition_name):
        # Clear 
        for i in reversed(range(self.form_layout.count())): 
            self.form_layout.itemAt(i).widget().setParent(None)
        # Populate form 
        condition = self.conditions[condition_name]
        row = 0
        for key, value in condition.__dict__.items():
            if key != 'name':
                note = QLabel(self.param_notes.get(key, ''))
                self.form_layout.addWidget(note, row, 0)
                label = QLabel(key)
                self.form_layout.addWidget(label, row, 1)
                if isinstance(value, (list, tuple)):  # value is a list or tuple
                    print(f"Processing list value: {value}")
                    if any(isinstance(i, (list, tuple)) for i in value):  # check if any item is a list
                        print(f"Nested list found: {value}")
                        for i, component in enumerate(value):
                            if isinstance(component, (list, tuple)): 
                                print(f"Processing nested RGB value: {component}")
                                for j, subcomponent in enumerate(component):
                                    line_edit = QLineEdit(str(subcomponent))
                                    line_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                                    line_edit.setFixedSize(50, 20) 
                                    self.form_layout.addWidget(line_edit, row, i + 2 + j)
                                    print(f"Added QLineEdit for subcomponent {subcomponent} at row {row}, column {i + 2 + j}")
                                # Add color preview
                                if len(component) == 3:  # Only for RGB colors
                                    ldr_value = [min(1, max(0, subcomponent)) for subcomponent in component]  # clamp to [0, 1] not sure how to tackle hdr values
                                    color = QColor(int(ldr_value[0]*255), int(ldr_value[1]*255), int(ldr_value[2]*255))
                                    color_preview = QLabel()
                                    color_preview.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                                    color_preview.setFixedSize(50, 20)
                                    color_preview.setAutoFillBackground(True)
                                    palette = color_preview.palette()
                                    palette.setColor(QPalette.Window, color) 
                                    color_preview.setPalette(palette)
                                    # if multiplier exists, its column index would be (2 + len(component)); color preview comes next
                                    color_preview_col_index = 5
                                    self.form_layout.addWidget(color_preview, row, color_preview_col_index)
                                    print(f"Added color preview for RGB value {component} at row {row}, column {color_preview_col_index}")
                                    r_edit = QLineEdit(str(component[0]))
                                    g_edit = QLineEdit(str(component[1]))
                                    b_edit = QLineEdit(str(component[2]))
                                    r_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                                    g_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                                    b_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                                    r_edit.setFixedSize(50, 20)
                                    g_edit.setFixedSize(50, 20)
                                    b_edit.setFixedSize(50, 20)
                                    self.form_layout.addWidget(r_edit, row, 2)
                                    self.form_layout.addWidget(g_edit, row, 3)
                                    self.form_layout.addWidget(b_edit, row, 4)
                                    # Add the connections for the textChanged signal
                                    r_edit.textChanged.connect(partial(self.update_color_preview, r_edit, g_edit, b_edit, color_preview))
                                    g_edit.textChanged.connect(partial(self.update_color_preview, r_edit, g_edit, b_edit, color_preview))
                                    b_edit.textChanged.connect(partial(self.update_color_preview, r_edit, g_edit, b_edit, color_preview))



                            else:  # Single float value within list (weird ass multiplier)
                                line_edit = QLineEdit(str(component))
                                line_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                                line_edit.setFixedSize(50, 20) 
                                self.form_layout.addWidget(line_edit, row, i + 2 + len(value[0]))
                                print(f"Added QLineEdit for component {component} at row {row}, column {i + 2 + len(value[0])}")
                        # If no multiplier is present, add a disabled QLineEdit
                        if len(value) == 1:
                            line_edit = QLineEdit("0")
                            line_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) 
                            line_edit.setFixedSize(50, 20)
                            line_edit.setEnabled(False)
                            self.form_layout.addWidget(line_edit, row, i + 2 + len(value[0]) + 1)
                            print(f"Added disabled QLineEdit for missing multiplier at row {row}, column {i + 2 + len(value[0]) + 1}")
                        row += 1  # Increment 
                    else:  # Handle simple lists
                        for i, component in enumerate(value):
                            line_edit = QLineEdit(str(component))
                            line_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) 
                            line_edit.setFixedSize(50, 20) 
                            self.form_layout.addWidget(line_edit, row, i + 2)
                            print(f"Added QLineEdit for component {component} at row {row}, column {i + 2}")
                        row += 1 
                else:  # value is single number or string
                    line_edit = QLineEdit(str(value))
                    line_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                    line_edit.setFixedSize(50, 20) 
                    self.form_layout.addWidget(line_edit, row, 2)
                    row += 1  # Increment 

    # Sort out the save and update loop
    def update_lighting_config(self):
        temp_file_path = 'data/temp_file.json'
        loaded_file_path = 'data/loaded_file.json'

        # Write from temp file to the loaded file
        try:
            with open(temp_file_path, 'r') as f:
                data = json.load(f)
            
            with open(loaded_file_path, 'w') as f:
                json.dump(data, f, indent=4)
            
            print("Updated lighting configuration.")
        except FileNotFoundError:
            # Create the file if it doesn't exist
            data = {} 
            with open(loaded_file_path, 'w') as f:
                json.dump(data, f, indent=4)
            
            print(f"Created {loaded_file_path} with default data.")

    def update_and_save(self, line_edit, condition_name, attribute_name):
        # Update the value in self.conditions
        value = line_edit.text()
        if ',' in value:  # This is a tuple
            value = tuple(float(v) for v in value.split(','))
        else:
            value = float(value)
        self.conditions[condition_name].__dict__[attribute_name] = value
        # Save the data to a temporary file
        with open('temp_file.json', 'w') as f:
            json.dump(self.conditions, f, indent=4)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    qtmodern.styles.dark(app)
    mw = qtmodern.windows.ModernWindow(MainWindow())
    mw.show()

    sys.exit(app.exec_())      

