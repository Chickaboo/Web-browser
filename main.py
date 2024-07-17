import sys
import os
import urllib.request
import json
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QToolBar,
    QTabWidget,
    QFileDialog,
    QDialog,
    QLabel,
    QComboBox,
    QStyleFactory,
    QMessageBox,
    QShortcut,
    QMenu,
    QInputDialog,
    QProgressDialog,
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QToolButton,
    QAction,
)
from PyQt5.QtCore import QUrl, QDir, Qt, QThread, pyqtSignal, QSettings, QStandardPaths
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtGui import QKeySequence, QIcon, QDesktopServices, QPixmap, QPalette, QColor
from qtawesome import icon

class DownloadThread(QThread):
    progress_update = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, url, file_path):
        super().__init__()
        self.url = url
        self.file_path = file_path

    def run(self):
        try:
            with urllib.request.urlopen(self.url) as response:
                file_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0

                with open(self.file_path, "wb") as file:
                    while True:
                        chunk = response.read(4096)
                        if not chunk:
                            break
                        downloaded += len(chunk)
                        file.write(chunk)
                        progress = int(downloaded / file_size * 100)
                        self.progress_update.emit(progress)

        except Exception as e:
            print(f"Error downloading file: {e}")

        self.finished.emit()


class SettingsDialog(QDialog):
    def __init__(self, current_search_engine, current_theme):
        super().__init__()

        self.setWindowTitle("Settings")
        self.setWindowIcon(icon("fa.cog")) 

        layout = QVBoxLayout()

        search_engine_label = QLabel("Search Engine:")
        self.search_engine_combobox = QComboBox()

        # Load search engines from configuration file and populate the combobox
        with open("search_engines.json") as f:
            search_engines = json.load(f)
            self.search_engine_combobox.addItems(search_engines.keys())

        self.search_engine_combobox.setCurrentText(current_search_engine)

        theme_label = QLabel("Theme:")
        self.theme_combobox = QComboBox()
        self.theme_combobox.addItems(["Light", "Dark"])
        self.theme_combobox.setCurrentText(current_theme)

        clear_data_button = QPushButton("Clear Cookies and Data")
        clear_data_button.clicked.connect(self.clear_data)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)

        layout.addWidget(search_engine_label)
        layout.addWidget(self.search_engine_combobox)
        layout.addWidget(theme_label)
        layout.addWidget(self.theme_combobox)
        layout.addWidget(clear_data_button)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def save_settings(self):
        selected_search_engine = self.search_engine_combobox.currentText()
        self.current_search_engine = selected_search_engine

        selected_theme = self.theme_combobox.currentText()
        self.current_theme = selected_theme

        self.accept()

    def get_selected_search_engine(self):
        return self.current_search_engine

    def get_selected_theme(self):
        return self.current_theme

    def clear_data(self):
        profile = QWebEngineProfile.defaultProfile()
        profile.clearAllVisitedLinks()
        profile.cookieStore().deleteAllCookies()


class WebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.home_url = "https://www.google.com"

    def set_url(self, url):
        self.load(QUrl(url))

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if navigation_type == QWebEnginePage.NavigationTypeLinkClicked:
            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                self.window().add_new_tab(url)
                return False

        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)


class SearchEngine(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chicken Web-Browser V2")
        self.setWindowIcon(QIcon("assets/browser.png"))
        self.resize(1200, 800)
        self.web_views = []

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.update_tab_title)

        self.new_tab_button = QToolButton()
        self.new_tab_button.setIcon(icon("fa.plus"))
        self.new_tab_button.setToolTip("New Tab")
        self.new_tab_button.clicked.connect(self.add_new_tab)

        self.back_button = QToolButton()
        self.back_button.setIcon(icon("fa.arrow-left"))
        self.back_button.setToolTip("Go Back")
        self.back_button.clicked.connect(self.navigate_back)

        self.forward_button = QToolButton()
        self.forward_button.setIcon(icon("fa.arrow-right"))
        self.forward_button.setToolTip("Go Forward")
        self.forward_button.clicked.connect(self.navigate_forward)

        self.home_button = QToolButton()
        self.home_button.setIcon(icon("fa.home"))  
        self.home_button.setToolTip("Go Home")
        self.home_button.clicked.connect(self.load_home)

        self.news_button = QToolButton()
        self.news_button.setIcon(icon("fa.newspaper-o"))
        self.news_button.setToolTip("Go to News")
        self.news_button.clicked.connect(self.load_news)

        self.refresh_button = QToolButton()
        self.refresh_button.setIcon(icon("fa.refresh"))
        self.refresh_button.setToolTip("Refresh Page")
        self.refresh_button.clicked.connect(self.refresh_page)

        self.address_bar = QLineEdit()
        self.address_bar.setObjectName("AddressBar")
        self.address_bar.setPlaceholderText("Enter URL or search...")
        self.address_bar.returnPressed.connect(self.load_url)

        self.settings_button = QToolButton()
        self.settings_button.setIcon(icon("fa.cogs"))
        self.settings_button.setToolTip("Open Settings")
        self.settings_button.clicked.connect(self.open_settings)

        self.download_button = QToolButton()
        self.download_button.setIcon(icon("fa.download"))
        self.download_button.setToolTip("Download Page")
        self.download_button.clicked.connect(self.download_page)

        self.find_button = QToolButton()
        self.find_button.setIcon(icon("fa.search"))
        self.find_button.setToolTip("Find on Page")
        self.find_button.clicked.connect(self.find_on_page)

        self.bookmark_button = QToolButton()
        self.bookmark_button.setIcon(icon("fa.bookmark"))
        self.bookmark_button.setToolTip("Manage Bookmarks")
        self.bookmark_button.clicked.connect(self.show_bookmark_dock)

        self.search_engine = "Google"
        self.current_find_text = ""
        self.current_theme = "Light"
        self.bookmarks = self.load_bookmarks()

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(10)
        toolbar_layout.addWidget(self.new_tab_button)
        toolbar_layout.addWidget(self.back_button)
        toolbar_layout.addWidget(self.forward_button)
        toolbar_layout.addWidget(self.home_button)
        toolbar_layout.addWidget(self.news_button)
        toolbar_layout.addWidget(self.refresh_button)
        toolbar_layout.addWidget(self.address_bar)
        toolbar_layout.addWidget(self.settings_button)
        toolbar_layout.addWidget(self.download_button)
        toolbar_layout.addWidget(self.find_button)
        toolbar_layout.addWidget(self.bookmark_button)

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

        self.bookmark_dock = QDockWidget("Bookmarks")
        self.bookmark_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.bookmark_list = QListWidget()
        self.bookmark_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.bookmark_list.itemDoubleClicked.connect(self.load_bookmark)
        self.bookmark_dock.setWidget(self.bookmark_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.bookmark_dock)
        self.bookmark_dock.hide()

        self.bookmark_menu = QMenu()
        self.bookmark_menu.addAction(
            QAction("Add Bookmark", self, triggered=self.bookmark_current_page)
        )
        self.bookmark_menu.addAction(
            QAction("Remove Bookmark", self, triggered=self.remove_bookmark)
        )
        self.load_search_engines()
        self.populate_bookmark_list()
        self.add_new_tab()
        self.load_home()

        self.tab_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self.show_tab_context_menu)

        new_tab_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_T), self)
        new_tab_shortcut.activated.connect(self.add_new_tab)

        close_tab_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_W), self)
        close_tab_shortcut.activated.connect(self.close_current_tab)

        find_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_F), self)
        find_shortcut.activated.connect(self.find_on_page)

        self.apply_theme(self.current_theme)

    def apply_theme(self, theme):
        if theme == "Dark":
            app.setStyle("Fusion")
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(35, 35, 35))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            app.setPalette(palette)
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #353535;
                    color: #ffffff;
                }
                QToolBar {
                    background-color: #444444;
                }
                QTabWidget::pane {
                    border: 1px solid #444444;
                }
                QTabBar::tab {
                    background: #555555;
                    border: 1px solid #444444;
                    padding: 5px;
                    border-radius: 3px;
                    transition: background 0.3s ease;
                }
                QTabBar::tab:selected {
                    background: #777777;
                }
                QLineEdit {
                    background: #555555;
                    color: #ffffff;
                    border: 1px solid #777777;
                    border-radius: 3px;
                    padding: 5px;
                }
                QToolButton {
                    background: #444444;
                    color: #ffffff;
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                    transition: background 0.3s ease;
                }
                QToolButton:hover {
                    background: #555555;
                }
                QListWidget {
                    background: #353535;
                    color: #ffffff;
                }
            """)
        elif theme == "Light":
            app.setStyle("Fusion")
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.WindowText, Qt.black)
            palette.setColor(QPalette.Base, Qt.white)
            palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
            palette.setColor(QPalette.ToolTipBase, Qt.black)
            palette.setColor(QPalette.ToolTipText, Qt.black)
            palette.setColor(QPalette.Text, Qt.black)
            palette.setColor(QPalette.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ButtonText, Qt.black)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.white)
            app.setPalette(palette)
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QToolBar {
                    background-color: #e0e0e0;
                }
                QTabWidget::pane {
                    border: 1px solid #e0e0e0;
                }
                QTabBar::tab {
                    background: #d0d0d0;
                    border: 1px solid #e0e0e0;
                    padding: 5px;
                    border-radius: 3px;
                    transition: background 0.3s ease;
                }
                QTabBar::tab:selected {
                    background: #c0c0c0;
                }
                QLineEdit {
                    background: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                    border-radius: 3px;
                    padding: 5px;
                }
                QToolButton {
                    background: #e0e0e0;
                    color: #000000;
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                    transition: background 0.3s ease;
                }
                QToolButton:hover {
                    background: #d0d0d0;
                }
                QListWidget {
                    background: #f0f0f0;
                    color: #000000;
                }
            """)

    def remove_bookmark(self):
        selected_items = self.bookmark_list.selectedItems()
        if selected_items:
            for item in selected_items:
                bookmark = item.text()
                self.bookmarks.remove(bookmark)
                self.bookmark_list.takeItem(self.bookmark_list.row(item))
            self.save_bookmarks(self.bookmarks)

    def load_search_engines(self):
        with open("search_engines.json") as f:
            self.search_engines = json.load(f)

    def add_new_tab(self, url=None):
        web_view = QWebEngineView()
        self.web_views.append(web_view)

        web_view.page().urlChanged.connect(self.update_address_bar)

        tab_index = self.tab_widget.addTab(web_view, "New Tab")
        self.tab_widget.setCurrentIndex(tab_index)

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)

    def close_current_tab(self):
        current_index = self.tab_widget.currentIndex()
        self.close_tab(current_index)

    def navigate_back(self):
        current_web_view = self.tab_widget.currentWidget()
        current_web_view.back()

    def navigate_forward(self):
        current_web_view = self.tab_widget.currentWidget()
        current_web_view.forward()

    def load_home(self):
        current_web_view = self.tab_widget.currentWidget()
        current_web_view.page().setUrl(QUrl(self.get_search_engine_url()))
        self.update_address_bar()

    def load_news(self):
        current_web_view = self.tab_widget.currentWidget()
        current_web_view.page().setUrl(QUrl("https://citizenfreepress.com/"))

    def refresh_page(self):
        current_web_view = self.tab_widget.currentWidget()
        current_web_view.reload()

    def load_url(self):
        url = self.address_bar.text()
        if not url.startswith("http"):
            url = f"http://{url}"
        current_web_view = self.tab_widget.currentWidget()
        current_web_view.page().setUrl(QUrl(url))

    def update_address_bar(self):
        current_web_view = self.tab_widget.currentWidget()
        current_url = current_web_view.page().url().toString()
        self.address_bar.setText(current_url)

    def open_settings(self):
        dialog = SettingsDialog(self.search_engine, self.current_theme)
        if dialog.exec_() == QDialog.Accepted:
            self.search_engine = dialog.get_selected_search_engine()
            self.current_theme = dialog.get_selected_theme()
            self.apply_theme(self.current_theme)
            self.load_home()

    def download_page(self):
        current_web_view = self.tab_widget.currentWidget()
        current_url = current_web_view.page().url().toString()

        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_path, _ = file_dialog.getSaveFileName(
            self, "Save Page", QDir.homePath(), "HTML Files (*.html)"
        )
        if file_path:
            current_web_view.page().toHtml(
                lambda html: self.download_page_async(current_url, html, file_path)
            )

    def download_page_async(self, url, html, file_path):
        download_thread = DownloadThread(url, file_path)
        download_thread.progress_update.connect(self.show_download_progress)
        download_thread.finished.connect(self.download_finished)
        download_thread.start()

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html)

    def show_download_progress(self, progress):
        progress_dialog = QProgressDialog(
            f"Downloading... {progress}%", "Cancel", 0, 100, self
        )
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setValue(progress)

    def download_finished(self):
        QMessageBox.information(
            self, "Download Complete", "The file has been downloaded successfully."
        )

    def find_on_page(self):
        current_web_view = self.tab_widget.currentWidget()

        text, ok = QInputDialog.getText(
            self,
            "Find on Page",
            "Find Text:",
            QLineEdit.Normal,
            self.current_find_text,
        )
        if ok and text:
            self.current_find_text = text
            current_web_view.findText(text, QWebEnginePage.FindFlags(0))

    def show_tab_context_menu(self, pos):
        menu = QMenu(self)
        new_tab_action = menu.addAction("New Tab")
        new_tab_action.triggered.connect(self.add_new_tab)

        duplicate_tab_action = menu.addAction("Duplicate Tab")
        duplicate_tab_action.triggered.connect(self.duplicate_current_tab)

        close_tab_action = menu.addAction("Close Tab")
        close_tab_action.triggered.connect(self.close_current_tab)

        bookmark_page_action = menu.addAction("Bookmark Page")
        bookmark_page_action.triggered.connect(self.bookmark_current_page)

        menu.exec_(self.tab_widget.mapToGlobal(pos))

    def duplicate_current_tab(self):
        current_web_view = self.tab_widget.currentWidget()
        current_url = current_web_view.page().url().toString()
        self.add_new_tab(current_url)

    def update_tab_title(self, index):
        current_web_view = self.tab_widget.widget(index)
        current_title = current_web_view.page().title()
        self.tab_widget.setTabText(
            index, current_title if current_title else "Untitled"
        )

    def show_bookmark_dock(self):
        self.bookmark_dock.show()

    def load_bookmarks(self):
        settings = QSettings("MyBrowser", "Bookmarks")
        bookmarks = settings.value("bookmarks", [])
        return bookmarks

    def save_bookmarks(self, bookmarks):
        settings = QSettings("MyBrowser", "Bookmarks")
        settings.setValue("bookmarks", bookmarks)

    def populate_bookmark_list(self):
        self.bookmark_list.clear()
        for bookmark in self.bookmarks:
            item = QListWidgetItem(bookmark)
            self.bookmark_list.addItem(item)

    def bookmark_current_page(self):
        current_web_view = self.tab_widget.currentWidget()
        current_url = current_web_view.page().url().toString()
        current_title = current_web_view.page().title()

        bookmark = f"{current_title} ({current_url})"
        if bookmark not in self.bookmarks:
            self.bookmarks.append(bookmark)
            self.save_bookmarks(self.bookmarks)
            self.populate_bookmark_list()

    def load_bookmark(self, item):
        bookmark_url = item.text().split("(")[1].split(")")[0]
        self.add_new_tab(bookmark_url)


    def remove_bookmark(self):
        selected_items = self.bookmark_list.selectedItems()
        if selected_items:
            for item in selected_items:
                bookmark = item.text()
                self.bookmarks.remove(bookmark)
                self.bookmark_list.takeItem(self.bookmark_list.row(item))
            self.save_bookmarks(self.bookmarks)

    def load_home(self):
        current_web_view = self.tab_widget.currentWidget()
        homepage_path = os.path.join(os.path.dirname(__file__), "homepage.html")
        homepage_url = QUrl.fromLocalFile(homepage_path)
        homepage_url.setQuery(f"theme={self.current_theme}")
        current_web_view.page().setUrl(homepage_url)
        self.address_bar.setText("Home")  # Set the address bar text to "Home"



if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/browser.png"))
    app.setApplicationName("Search Engine")
    app.setStyle("Fusion")
    window = SearchEngine()
    window.show()
    sys.exit(app.exec_())
