from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
import json

class SettingsDialog(QDialog):
    def __init__(self, current_search_engine):
        super().__init__()

        self.setWindowTitle("Settings")

        layout = QVBoxLayout()

        search_engine_label = QLabel("Search Engine:")
        self.search_engine_combobox = QComboBox()

        # Load search engines from configuration file and populate the combobox
        with open('search_engines.json') as f:
            search_engines = json.load(f)
            self.search_engine_combobox.addItems(search_engines.keys())

        self.search_engine_combobox.setCurrentText(current_search_engine)

        clear_data_button = QPushButton("Clear Cookies and Data")
        clear_data_button.clicked.connect(self.clear_data)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)

        layout.addWidget(search_engine_label)
        layout.addWidget(self.search_engine_combobox)
        layout.addWidget(clear_data_button)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def save_settings(self):
        selected_search_engine = self.search_engine_combobox.currentText()
        self.current_search_engine = selected_search_engine
        self.accept()

    def get_selected_search_engine(self):
        return self.current_search_engine

    def clear_data(self):
        profile = QWebEngineProfile.defaultProfile()
        profile.clearAllVisitedLinks()
        profile.cookieStore().deleteAllCookies()
