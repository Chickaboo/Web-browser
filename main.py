import sys
from PyQt5.QtWidgets import QApplication
from search_engine import SearchEngine

if __name__ == '__main__':
    app = QApplication(sys.argv)
    search_engine = SearchEngine()
    search_engine.show()
    sys.exit(app.exec_())
