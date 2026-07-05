"""
page_aircraft.py
메뉴 > 항공기 관리 > 기체 관리
UI 빌드 담당 — 로직은 page_aircraft_io.py(AircraftPageIOMixin)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QTableWidget, QHeaderView, QSplitter,
    QLineEdit, QComboBox, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from styles import COLOR
from page_aircraft_io import AircraftPageIOMixin

ROW_H = 52


class AircraftPage(AircraftPageIOMixin, QWidget):
    _COLS_DATA = [
        ('', None),
        ('기체등록번호', 'id'),
        ('기체명칭/모델', None),
        ('기종', 'type'),
        ('제조년도', None),
        ('위치', None),
        ('누적비행시간', 'total_hours'),
        ('점검날짜', None),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._aircraft = []
        self._selected = None
        self._sort_col = -1
        self._sort_asc = True
        self._build_ui()
        self._load()

    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        tb = QFrame()
        tb.setStyleSheet(
            f'background:#fafbfc; border-bottom:1px solid {COLOR["border"]};')
        th = QHBoxLayout(tb)
        th.setContentsMargins(12, 10, 12, 10)
        th.setSpacing(8)

        self._ac_combo = QComboBox()
        self._ac_combo.addItems(['-- 전체 --', 'DA-40NG', 'DA-42NG'])
        self._ac_combo.setFixedWidth(140)
        self._ac_combo.currentTextChanged.connect(self._refresh)

        self._search = QLineEdit()
        self._search.setObjectName('searchInput')
        self._search.setPlaceholderText('기체번호 검색')
        self._search.textChanged.connect(self._refresh)

        btn_add = QPushButton('+ 등록')
        btn_add.setStyleSheet(
            f'background:{COLOR["primary"]}; color:white; border:none;'
            f'padding:8px 18px; border-radius:4px; font-size:18px;')
        btn_add.clicked.connect(self._on_add)

        btn_del = QPushButton('🗑 삭제')
        btn_del.setStyleSheet(
            f'background:{COLOR["red"]}; color:white; border:none;'
            f'padding:8px 18px; border-radius:4px; font-size:18px;')
        btn_del.clicked.connect(self._on_delete)

        th.addWidget(self._ac_combo)
        th.addWidget(self._search, 1)
        th.addStretch()
        th.addWidget(btn_add)
        th.addWidget(btn_del)
        v.addWidget(tb)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)
        splitter.setStyleSheet(
            'QSplitter::handle{background:#d0d7e2;}'
            'QSplitter::handle:hover{background:#4a90d9;}')
        splitter.addWidget(self._build_center_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([700, 600])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        v.addWidget(splitter, 1)

    def _build_center_panel(self):
        from PyQt5.QtWidgets import QDialog
        panel = QFrame()
        panel.setStyleSheet('background:white;')
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self._table = QTableWidget()
        self._table.setColumnCount(len(self._COLS_DATA))
        self._table.setHorizontalHeaderLabels(
            [c[0] for c in self._COLS_DATA])
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(ROW_H)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.sectionClicked.connect(self._on_header_click)
        self._table.setColumnWidth(0, 44)
        self._table.setColumnWidth(1, 220)
        self._table.setColumnWidth(3, 200)
        self._table.setColumnWidth(4, 180)
        self._table.setColumnWidth(5, 180)
        self._table.setColumnWidth(6, 220)
        self._table.setColumnWidth(7, 200)
        self._table.cellClicked.connect(self._on_row_click)
        self._table.doubleClicked.connect(self._on_double_click)
        v.addWidget(self._table, 1)
        return panel

    def _build_right_panel(self):
        panel = QFrame()
        panel.setMinimumWidth(550)
        panel.setMaximumWidth(700)
        panel.setStyleSheet(
            f'background:white; border-left:1px solid {COLOR["border"]};')
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        hdr = QFrame()
        hdr.setStyleSheet(
            f'background:#e8eef5; border-bottom:1px solid {COLOR["border"]};')
        hh = QHBoxLayout(hdr)
        hh.setContentsMargins(10, 8, 10, 8)
        lbl = QLabel('부품 목록')
        lbl.setFont(QFont('', 16, QFont.Bold))
        lbl.setStyleSheet(f'color:{COLOR["primary"]};')
        lbl.setAlignment(Qt.AlignCenter)
        hh.addStretch()
        hh.addWidget(lbl)
        hh.addStretch()
        v.addWidget(hdr)

        self._parts_tbl = QTableWidget()
        self._parts_tbl.setColumnCount(2)
        self._parts_tbl.setHorizontalHeaderLabels(['부품번호', '부품명칭'])
        self._parts_tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self._parts_tbl.verticalHeader().setVisible(False)
        self._parts_tbl.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch)
        self._parts_tbl.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Interactive)
        self._parts_tbl.setColumnWidth(0, 300)
        self._parts_tbl.verticalHeader().setDefaultSectionSize(ROW_H)
        v.addWidget(self._parts_tbl, 1)
        return panel
