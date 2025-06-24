from PySide6.QtWidgets import (QApplication, QStyleFactory, QMainWindow, QWidget, QVBoxLayout,
							   QPushButton, QHBoxLayout, QStackedWidget, QFrame, QLineEdit, QMessageBox, QComboBox,
							   QSlider, QCheckBox, QGroupBox, QCalendarWidget, QLabel, QFileDialog, QPlainTextEdit,
							   QSystemTrayIcon, QMenu, QListWidget, QListWidgetItem, QSpacerItem,
							   QSizePolicy, QFrame, QDateTimeEdit, QGraphicsDropShadowEffect, QCalendarWidget,
							   QScrollBar, QStyledItemDelegate, QTableView, QInputDialog, QHeaderView, QScrollArea,
							   QDialog, QTextEdit, QStyleOptionViewItem)
from PySide6.QtCore import (QPropertyAnimation, QEasingCurve, Qt, QDate, QTime, QDateTime, Signal, Slot, QSize, QObject,
							QPoint, QTimer, QEvent, QPointF, QPersistentModelIndex, QRect, QThread)
from PySide6.QtGui import (QIcon, QAction, QPixmap, QColor, QLinearGradient, QPainter, QMouseEvent,
						   QPainter, QFontMetrics, QTextCharFormat, QPen, QCursor,QPalette, QCloseEvent)
import sys
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType
from camel.messages import BaseMessage
from camel.types import RoleType
from camel.utils import print_text_animated
import requests
import json
import os
from dotenv import load_dotenv
import logging
from PIL import Image
