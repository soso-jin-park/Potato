"""
page_inout.py
메뉴 > 재고관리 > 입출고 관리
UI 빌드 담당 — 로직은 page_inout_io.py(InOutPageIOMixin)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QTableWidget, QHeaderView, QLineEdit, QComboBox, QSplitter
)
from PyQt5.QtCore import Qt

from styles import COLOR
from page_inout_io import InOutPageIOMixin

ROW_H    = 52
AC_TYPES = ['전체', 'DA-40NG', 'DA-42NG']
IN_LABELS  = ['', '부품번호', '부품명칭', '재고 수량', '안전재고 수량', '입고 날짜']
OUT_LABELS = ['', '부품번호', '부품명칭', '재고 수량', '출고 수량',
              '지역', '담당자', '출고 날짜']


class InOutPage(InOutPageIOMixin, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._inbound  = []
        self._outbound = []
        self._sort_in  = (-1, True)
        self._sort_out = (-1, True)
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
        self._ac_combo.addItems(AC_TYPES)
        self._ac_combo.setFixedWidth(130)
        self._ac_combo.currentTextChanged.connect(self._refresh)

        btn_in = QPushButton('+ 입고')
        btn_in.setStyleSheet(
            f'background:{COLOR["primary"]}; color:white; border:none;'
            f'padding:8px 18px; border-radius:4px; font-size:18px;')
        btn_in.clicked.connect(self._on_inbound)

        btn_out = QPushButton('− 출고')
        btn_out.setStyleSheet(
            f'background:{COLOR["secondary"]}; color:white; border:none;'
            f'padding:8px 18px; border-radius:4px; font-size:18px;')
        btn_out.clicked.connect(self._on_outbound)

        btn_del = QPushButton('🗑 삭제')
        btn_del.setStyleSheet(
            f'background:{COLOR["red"]}; color:white; border:none;'
            f'padding:8px 18px; border-radius:4px; font-size:18px;')
        btn_del.clicked.connect(self._on_delete)

        self._search = QLineEdit()
        self._search.setObjectName('searchInput')
        self._search.setPlaceholderText('부품번호 / 명칭 검색')
        self._search.textChanged.connect(self._refresh)

        th.addWidget(self._ac_combo)
        th.addWidget(btn_in)
        th.addWidget(btn_out)
        th.addWidget(btn_del)
        th.addWidget(self._search, 1)
        v.addWidget(tb)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(
            'QSplitter::handle{background:#d0d7e2;}'
            'QSplitter::handle:hover{background:#4a90d9;}')
        splitter.addWidget(self._build_in_panel())
        splitter.addWidget(self._build_out_panel())
        splitter.setSizes([1, 1])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        v.addWidget(splitter, 1)

    def _build_in_panel(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        self._tbl_in = QTableWidget()
        self._tbl_in.setColumnCount(len(IN_LABELS))
        self._tbl_in.setHorizontalHeaderLabels(IN_LABELS)
        self._tbl_in.setSelectionBehavior(QTableWidget.SelectRows)
        self._tbl_in.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tbl_in.verticalHeader().setVisible(False)
        self._tbl_in.verticalHeader().setDefaultSectionSize(ROW_H)
        hdr = self._tbl_in.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        self._tbl_in.setColumnWidth(0, 44)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        for col in [1, 3, 4, 5]:
            hdr.setSectionResizeMode(col, QHeaderView.Interactive)
        self._tbl_in.setColumnWidth(1, 160)
        self._tbl_in.setColumnWidth(3, 160)
        self._tbl_in.setColumnWidth(4, 180)
        self._tbl_in.setColumnWidth(5, 140)
        hdr.setMinimumSectionSize(100)
        hdr.sectionClicked.connect(self._on_in_header)
        v.addWidget(self._tbl_in)
        return w

    def _build_out_panel(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        self._tbl_out = QTableWidget()
        self._tbl_out.setColumnCount(len(OUT_LABELS))
        self._tbl_out.setHorizontalHeaderLabels(OUT_LABELS)
        self._tbl_out.setSelectionBehavior(QTableWidget.SelectRows)
        self._tbl_out.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tbl_out.verticalHeader().setVisible(False)
        self._tbl_out.verticalHeader().setDefaultSectionSize(ROW_H)
        hdr = self._tbl_out.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        self._tbl_out.setColumnWidth(0, 44)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        for col in [1, 3, 4, 5, 6, 7]:
            hdr.setSectionResizeMode(col, QHeaderView.Interactive)
        self._tbl_out.setColumnWidth(1, 160)
        self._tbl_out.setColumnWidth(3, 160)
        self._tbl_out.setColumnWidth(4, 140)
        self._tbl_out.setColumnWidth(5, 140)
        self._tbl_out.setColumnWidth(6, 150)
        self._tbl_out.setColumnWidth(7, 140)
        hdr.setMinimumSectionSize(100)
        hdr.sectionClicked.connect(self._on_out_header)
        v.addWidget(self._tbl_out)
        return w

    def _on_in_header(self, col):
        c, asc = self._sort_in
        self._sort_in = (col, not asc if c == col else True)
        self._refresh()

    def _on_out_header(self, col):
        c, asc = self._sort_out
        self._sort_out = (col, not asc if c == col else True)
        self._refresh()