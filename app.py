"""
app.py — Uygulamayı başlatır (PyQt5 event loop).
"""
import sys
from PyQt5 import QtWidgets
from gui_main import MainWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
