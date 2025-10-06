"""
app.py — Uygulamayı başlatır (tema uygular).
"""
import sys
from PyQt5 import QtWidgets
from gui_main import MainWindow
from styles import apply_theme

def main():
    app = QtWidgets.QApplication(sys.argv)
    apply_theme(app, True)  # başlangıçta koyu tema
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
