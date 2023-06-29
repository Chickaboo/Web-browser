from PyQt5.QtCore import QUrl, QDir
from PyQt5.QtWidgets import QMainWindow, QLineEdit, QHBoxLayout, QVBoxLayout, QWidget, QPushButton, QToolBar, QTabWidget, QFileDialog, QDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from settings_dialog import SettingsDialog
import json

class WebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.home_url = "https://www.google.com"

    def set_url(self, url):
        self.load(QUrl(url))


class SearchEngine(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Search Engine")

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        self.new_tab_button = QPushButton("+")
        self.new_tab_button.setObjectName("NewTabButton")
        self.new_tab_button.clicked.connect(self.add_new_tab)

        self.back_button = QPushButton("←")
        self.back_button.setObjectName("NavigationButton")
        self.back_button.setToolTip("Go Back")
        self.back_button.clicked.connect(self.navigate_back)

        self.forward_button = QPushButton("→")
        self.forward_button.setObjectName("NavigationButton")
        self.forward_button.setToolTip("Go Forward")
        self.forward_button.clicked.connect(self.navigate_forward)

        self.home_button = QPushButton("Home")
        self.home_button.setObjectName("ActionButton")
        self.home_button.setToolTip("Go Home")
        self.home_button.clicked.connect(self.load_home)

        self.news_button = QPushButton("News")
        self.news_button.setObjectName("ActionButton")
        self.news_button.setToolTip("Go to News")
        self.news_button.clicked.connect(self.load_news)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("ActionButton")
        self.refresh_button.setToolTip("Refresh Page")
        self.refresh_button.clicked.connect(self.refresh_page)

        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.returnPressed.connect(self.search)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("ActionButton")
        self.settings_button.setToolTip("Open Settings")
        self.settings_button.clicked.connect(self.open_settings)

        self.download_button = QPushButton("Download")
        self.download_button.setObjectName("ActionButton")
        self.download_button.setToolTip("Download Page")
        self.download_button.clicked.connect(self.download_page)

        self.search_engine = "Google"

        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(self.new_tab_button)
        toolbar_layout.addWidget(self.back_button)
        toolbar_layout.addWidget(self.forward_button)
        toolbar_layout.addWidget(self.home_button)
        toolbar_layout.addWidget(self.news_button)
        toolbar_layout.addWidget(self.refresh_button)
        toolbar_layout.addWidget(self.search_bar)
        toolbar_layout.addWidget(self.settings_button)
        toolbar_layout.addWidget(self.download_button)

        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("ToolbarWidget")
        toolbar_widget.setLayout(toolbar_layout)

        toolbar = QToolBar()
        toolbar.addWidget(toolbar_widget)

        self.addToolBar(toolbar)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)

        self.setCentralWidget(central_widget)

        self.load_search_engines()  # Load search engines from configuration file
        self.add_new_tab()
        self.load_home()

    def load_search_engines(self):
        with open('search_engines.json') as f:
            self.search_engines = json.load(f)

    def get_search_engine_url(self):
        default_engine = "Google"  # Default to Google if search engine is not recognized
        return self.search_engines.get(self.search_engine, self.search_engines.get(default_engine))
    
    def add_new_tab(self):
        web_view = QWebEngineView()
        web_view.page().setUrl(QUrl(self.get_search_engine_url()))
        web_view.page().urlChanged.connect(self.update_search_bar_visibility)

        tab_index = self.tab_widget.addTab(web_view, "New Tab")
        self.tab_widget.setCurrentIndex(tab_index)

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)

    def navigate_back(self):
        current_web_view = self.tab_widget.currentWidget()
        current_web_view.back()

    def navigate_forward(self):
        current_web_view = self.tab_widget.currentWidget()
        current_web_view.forward()

    def load_home(self):
        current_web_view = self.tab_widget.currentWidget()
        current_web_view.page().setUrl(QUrl(self.get_search_engine_url()))
        self.update_search_bar_visibility()

    def load_news(self):
        current_web_view = self.tab_widget.currentWidget()
        current_web_view.page().setUrl(QUrl("https://www.fnanews.com"))

    def refresh_page(self):
        current_web_view = self.tab_widget.currentWidget()
        current_web_view.reload()

    def search(self):
        current_web_view = self.tab_widget.currentWidget()
        query = self.search_bar.text()
        if query:
            search_url = f"{self.get_search_engine_url()}/search?q={query}"
            current_web_view.page().setUrl(QUrl(search_url))

    def update_search_bar_visibility(self):
        current_web_view = self.tab_widget.currentWidget()
        current_url = current_web_view.page().url().toString()
        show_search_bar = not current_url.startswith(self.get_search_engine_url())
        self.search_bar.setVisible(show_search_bar)

    def open_settings(self):
        dialog = SettingsDialog(self.search_engine)
        if dialog.exec_() == QDialog.Accepted:
            self.search_engine = dialog.get_selected_search_engine()
            self.load_home()

    def download_page(self):
        current_web_view = self.tab_widget.currentWidget()
        current_url = current_web_view.page().url().toString()

        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_path, _ = file_dialog.getSaveFileName(self, "Save Page", QDir.homePath(), "HTML Files (*.html)")
        if file_path:
            current_web_view.page().toHtml(lambda html: self.save_page(html, file_path))

    def save_page(self, html, file_path):
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html)

        print("Page saved successfully.")
