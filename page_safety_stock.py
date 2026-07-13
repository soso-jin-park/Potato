"""
page_safety_stock.py
메뉴 > 재고관리 > 안전재고 관리
UI 빌드 담당 — 로직은 page_safety_stock_io.py(SafetyStockIOMixin)
모델/delegate — page_safety_stock_models.py
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QHeaderView, QLineEdit, QComboBox, QSplitter,
    QTableView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from styles import COLOR
from page_safety_stock_models import _OrderModel, _ColorDelegate
from page_safety_stock_io import SafetyStockIOMixin, _status, _pct

ROW_H    = 52
AC_TYPES = ['-- 전체 --', 'DA-40NG', 'DA-42NG']
class SafetyStockPage(SafetyStockIOMixin, QWidget):
    COLS = ['부품번호', '부품명칭', '재고 수량', '안전재고 수량',
            '재고 비율(%)', '재고 상태', '전 분기 단가 (EUR)']

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parts = []
        self._sort_col = -1
        self._sort_asc = True
        self._status_filter = None  # None=부족+경고, '부족', '경고', '정상'
        self._build_ui()
        self._load()
        # 입출고 등 실제 재고 변동 시 자동 재로드
        from inventory import inventory
        inventory.stock_updated.connect(self._load)

    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # 툴바
        tb = QFrame()
        tb.setStyleSheet(
            f'background:#fafbfc; border-bottom:1px solid {COLOR["border"]};'
        )
        th = QHBoxLayout(tb)
        th.setContentsMargins(12, 10, 12, 10)
        th.setSpacing(8)

        self._ac_combo = QComboBox()
        self._ac_combo.addItems(AC_TYPES)
        self._ac_combo.setFixedWidth(140)
        self._ac_combo.currentTextChanged.connect(self._refresh)

        self._search = QLineEdit()
        self._search.setObjectName('searchInput')
        self._search.setPlaceholderText('부품번호 / 명칭 검색')
        self._search.textChanged.connect(self._refresh)

        th.addWidget(self._ac_combo)
        th.addWidget(self._search, 1)
        v.addWidget(tb)

        # 좌우 분할
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#d0d7e2; }
            QSplitter::handle:hover { background:#4a90d9; }
        """)
        splitter.addWidget(self._build_table_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([600, 700])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        v.addWidget(splitter, 1)

    def _build_table_panel(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self._table = QTableWidget()
        self._table.setColumnCount(len(self.COLS))
        self._table.setHorizontalHeaderLabels(self.COLS)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(ROW_H)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        for col in [0, 2, 3, 4, 5, 6]:
            hdr.setSectionResizeMode(col, QHeaderView.Interactive)
        self._table.setColumnWidth(0, 280)
        self._table.setColumnWidth(2, 170)
        self._table.setColumnWidth(3, 200)
        self._table.setColumnWidth(4, 180)
        self._table.setColumnWidth(5, 170)
        self._table.setColumnWidth(6, 260)
        hdr.setMinimumSectionSize(100)

        self._table.doubleClicked.connect(self._on_detail)
        self._table.horizontalHeader().sectionClicked.connect(self._on_header_click)
        v.addWidget(self._table)
        return w

    def _build_right_panel(self):
        panel = QFrame()
        panel.setStyleSheet(
            f'background:white; border-left:1px solid {COLOR["border"]};'
        )
        panel.setMinimumWidth(500)
        panel.setMaximumWidth(750)

        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(14)

        # ── 재고 수량 현황 요약 ──
        summary_lbl = QLabel('재고 수량 현황 요약')
        summary_lbl.setFont(QFont('', 22, QFont.Bold))
        summary_lbl.setStyleSheet(f'color:{COLOR["text"]};')
        v.addWidget(summary_lbl)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(16)
        self._badge_danger = self._make_badge('0\n부족', COLOR['red'])
        self._badge_warn   = self._make_badge('0\n경고', COLOR['orange'])
        self._badge_ok     = self._make_badge('0\n정상', COLOR['green'])

        # 배지 클릭 이벤트 연결
        self._badge_danger.setCursor(Qt.PointingHandCursor)
        self._badge_warn.setCursor(Qt.PointingHandCursor)
        self._badge_ok.setCursor(Qt.PointingHandCursor)
        self._badge_danger.mousePressEvent = lambda e: self._on_badge_click('부족')
        self._badge_warn.mousePressEvent = lambda e: self._on_badge_click('경고')
        self._badge_ok.mousePressEvent = lambda e: self._on_badge_click('정상')

        badge_row.addWidget(self._badge_danger, 1)
        badge_row.addWidget(self._badge_warn, 1)
        badge_row.addWidget(self._badge_ok, 1)
        v.addLayout(badge_row)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet(f'color:{COLOR["border"]};')
        v.addWidget(sep1)

        # ── 다음 발주 필요 부품 ──
        order_lbl = QLabel('다음 발주 필요 부품')
        order_lbl.setFont(QFont('', 21, QFont.Bold))
        order_lbl.setStyleSheet(f'color:{COLOR["text"]};')
        v.addWidget(order_lbl)

        self._order_model = _OrderModel()
        self._order_tbl = QTableView()
        self._order_tbl.setObjectName('orderTbl')
        self._order_tbl.setModel(self._order_model)
        self._order_tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._order_tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._order_tbl.verticalHeader().setVisible(False)
        self._order_tbl.verticalHeader().setDefaultSectionSize(52)
        self._order_tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._order_tbl.setColumnWidth(0, 160)
        self._order_tbl.setColumnWidth(2, 60)
        self._order_tbl.setColumnWidth(3, 120)
        self._order_tbl.setFont(__import__('PyQt5.QtGui', fromlist=['QFont']).QFont('', 20))
        self._order_tbl.setAlternatingRowColors(False)
        self._order_tbl.setItemDelegate(_ColorDelegate(self._order_tbl))
        self._order_tbl.setShowGrid(True)
        v.addWidget(self._order_tbl, 1)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f'color:{COLOR["border"]};')
        v.addWidget(sep2)

        # ── 다음 발주일 ──
        order_date_row = QHBoxLayout()
        order_date_lbl = QLabel('다음 발주일:')
        order_date_lbl.setFont(QFont('', 21, QFont.Bold))
        order_date_lbl.setStyleSheet(f'color:{COLOR["text"]};')
        self._order_date = QLabel('2026년 7월')
        self._order_date.setStyleSheet(
            f'background:#f0f4f8; border:1px solid {COLOR["border"]};'
            f'border-radius:4px; padding:8px 16px; font-size:21px; font-weight:bold;'
            f'color:{COLOR["primary"]};'
        )
        order_date_row.addWidget(order_date_lbl)
        order_date_row.addWidget(self._order_date)
        order_date_row.addStretch()
        v.addLayout(order_date_row)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet(f'border:1px dashed {COLOR["border"]};')
        v.addWidget(sep3)

        # ── 범례 ──
        for color, text in [
            (COLOR['red'],    '부족 - 안전재고 수량 이하'),
            (COLOR['orange'], '경고 - 안전재고 수량 × 1.5 이하'),
            (COLOR['green'],  '정상'),
        ]:
            row = QHBoxLayout()
            dot = QLabel('●')
            dot.setStyleSheet(f'color:{color}; font-size:22px;')
            dot.setFixedWidth(22)
            lbl = QLabel(text)
            lbl.setStyleSheet(f'font-size:20px; color:{COLOR["text"]};')
            row.addWidget(dot)
            row.addWidget(lbl)
            row.addStretch()
            v.addLayout(row)

        return panel

    def _make_badge(self, text, color):
        f = QFrame()
        f.setMinimumSize(140, 120)
        f.setStyleSheet(
            f'background:white; border:3px solid {color}; border-radius:12px;'
        )
        v = QVBoxLayout(f)
        v.setContentsMargins(0, 0, 0, 0)
        v.setAlignment(Qt.AlignCenter)
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFont(QFont('', 28, QFont.Bold))
        lbl.setStyleSheet(f'color:{color}; border:none;')
        v.addWidget(lbl)
        f._color = color  # 원래 색상 저장
        return f

    def _on_badge_click(self, status):
        """배지 클릭 시 발주 필요 부품 테이블 필터링"""
        if self._status_filter == status:
            self._status_filter = None  # 같은 배지 다시 클릭 → 해제
        else:
            self._status_filter = status
        self._refresh()

    def _update_badge_styles(self):
        """선택된 배지 강조 표시"""
        for badge, st in [(self._badge_danger, '부족'),
                          (self._badge_warn, '경고'),
                          (self._badge_ok, '정상')]:
            c = badge._color
            if self._status_filter == st:
                badge.setStyleSheet(
                    f'background:{c}; border:3px solid {c}; border-radius:12px;')
                lbl = badge.findChild(QLabel)
                if lbl:
                    lbl.setStyleSheet(
                        f'color:white; border:none; font-size:28px; font-weight:bold;')
            else:
                badge.setStyleSheet(
                    f'background:white; border:3px solid {c}; border-radius:12px;')
                lbl = badge.findChild(QLabel)
                if lbl:
                    lbl.setStyleSheet(
                        f'color:{c}; border:none; font-size:28px; font-weight:bold;')