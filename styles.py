# -*- coding: utf-8 -*-
# ViperaDev — WhatsApp Broadcast Tool
"""
Qt Style Sheets (QSS) — Açık/Koyu tema ve modern görünüm.
"""
from PyQt5 import QtGui

LIGHT_QSS = """
QWidget { font-family: 'Segoe UI','Inter','Arial'; font-size: 14px; color: #1b1f24; background: #f7f8fa; }
QFrame#Card { background: #ffffff; border: 1px solid #e6e8eb; border-radius: 16px; }
QPushButton { background: #2563eb; color: white; border: none; border-radius: 10px; padding: 10px 14px; font-weight: 600; }
QPushButton:hover { background: #1e4dd8; }
QPushButton:disabled { background: #aab4c3; color: #f3f4f6; }
QPushButton#Secondary { background: #eef2ff; color: #334155; }
QPushButton#Secondary:hover { background: #e0e7ff; }
QLineEdit, QDateTimeEdit { background: #ffffff; border: 1px solid #d1d5db; border-radius: 10px; padding: 8px 10px; }
QPlainTextEdit { background: #0b1220; color: #e5e7eb; border-radius: 12px; padding: 10px; }
QProgressBar { border: 1px solid #e6e8eb; border-radius: 10px; background: #f1f5f9; height: 16px; text-align: center; }
QProgressBar::chunk { border-radius: 10px; background-color: #22c55e; }
QCheckBox { spacing: 8px; } QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #cbd5e1; border-radius: 6px; background: #fff; }
QCheckBox::indicator:checked { background: #2563eb; border-color: #2563eb; }
QLabel#Title { font-size: 22px; font-weight: 700; }
QLabel#Badge { padding: 4px 10px; border-radius: 999px; font-weight: 700; background: #e2e8f0; color:#0f172a; }
QLabel#BadgeOk { background: #dcfce7; color: #166534; }
QLabel#BadgeFail { background: #fee2e2; color: #991b1b; }
QLabel#BadgeInfo { background: #e0e7ff; color: #1e40af; }
"""

DARK_QSS = """
QWidget { font-family: 'Segoe UI','Inter','Arial'; font-size: 14px; color: #e5e7eb; background: #0b1220; }
QFrame#Card { background: #0f172a; border: 1px solid #1f2937; border-radius: 16px; }
QPushButton { background: #3b82f6; color: white; border: none; border-radius: 10px; padding: 10px 14px; font-weight: 600; }
QPushButton:hover { background: #2563eb; }
QPushButton:disabled { background: #334155; color: #94a3b8; }
QPushButton#Secondary { background: #111827; color: #cbd5e1; }
QPushButton#Secondary:hover { background: #1f2937; }
QLineEdit, QDateTimeEdit { background: #0b1220; border: 1px solid #374151; border-radius: 10px; padding: 8px 10px; color: #e5e7eb; }
QPlainTextEdit { background: #0b1220; color: #cbd5e1; border-radius: 12px; padding: 10px; }
QProgressBar { border: 1px solid #334155; border-radius: 10px; background: #111827; height: 16px; text-align: center; }
QProgressBar::chunk { border-radius: 10px; background-color: #22c55e; }
QCheckBox { spacing: 8px; } QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #475569; border-radius: 6px; background: #0b1220; }
QCheckBox::indicator:checked { background: #3b82f6; border-color: #3b82f6; }
QLabel#Title { font-size: 22px; font-weight: 700; }
QLabel#Badge { padding: 4px 10px; border-radius: 999px; font-weight: 700; background: #111827; color:#cbd5e1; }
QLabel#BadgeOk { background: #064e3b; color: #a7f3d0; }
QLabel#BadgeFail { background: #7f1d1d; color: #fecaca; }
QLabel#BadgeInfo { background: #1e1b4b; color: #c7d2fe; }
"""

def apply_theme(app, dark: bool):
    app.setStyleSheet(DARK_QSS if dark else LIGHT_QSS)

def nice_icon(path: str) -> QtGui.QIcon:
    pix = QtGui.QPixmap(path)
    return QtGui.QIcon(pix) if not pix.isNull() else QtGui.QIcon()
