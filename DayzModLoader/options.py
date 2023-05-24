from PyQt5.QtWidgets import *


class Example(QWidget):
    def __init__(self):
        super().__init__()

        self.show_options = QCheckBox("Show options")
        self.server_checkbox = QCheckBox("Run as DiagX64")
        self.start_button = QPushButton("Start Server")

        # Create a layout for the loader box
        loader_layout = QVBoxLayout()
        loader_layout.addWidget(self.show_options)
        loader_layout.addWidget(self.server_checkbox)
        loader_layout.addWidget(self.start_button)

        # Create a layout for the options box
        options_layout = QVBoxLayout()
        options_layout.addWidget(QPushButton("Check for Updates"))
        options_layout.addWidget(QPushButton("What is this?"))
        options_layout.addWidget(QPushButton("Browse for !Workshop Path"))
        options_layout.addWidget(QPushButton("Browse for Server Path"))

        self.loader_box = QGroupBox("Loader")
        self.loader_box.setLayout(loader_layout)

        self.options_box = QGroupBox("Options")
        self.options_box.setLayout(options_layout)

        # Wrap loader_box and options_box in another widget
        wrapper = QWidget()

        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.addWidget(self.loader_box)
        wrapper_layout.addWidget(self.options_box)

        main_layout = QVBoxLayout()
        main_layout.addWidget(wrapper)

        self.setLayout(main_layout)
        self.show_options.stateChanged.connect(self.loader_box.setVisible)
        self.loader_box.setVisible(False)


if __name__ == "__main__":
    app = QApplication([])
    window = Example()
    window.show()
    app.exec_()
