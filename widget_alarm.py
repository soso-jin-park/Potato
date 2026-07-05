"""
widget_parts.py
부품 테이블 위젯 (render.parts.js + render.state.js → PyQt5 변환)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QLabel, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont

from inventory import inventory
from styles import COLOR


# ── 재고 배지 색상 ────────────────────────────────────────────────
def _stock_color(qty, safe_qty):
    if qty == 0:
        return QColor('#f8d7da'), QColor('#721c24')   # bg, fg
    if qty <= safe_qty:
        return QColor('#fff3cd'), QColor('#856404')
    return QColor('#d4edda'), QColor('#155724')


class PartsWidget(QWidget):
    """
    툴바(탭/필터/검색) + 부품 테이블
    """

    COLS = [
        ('No',     None),
        ('주기',   'cycle'),
        ('부품번호', 'part_no'),
        ('부품명칭', 'name'),
        ('재고',   'qty'),
        ('안전재고', 'safe_qty'),
        ('위치',   'location'),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    # ── UI 구성 ──────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # 툴바는 DashboardLeft에서 통합 관리 — 테이블만 추가
        layout.addWidget(self._build_table())

    def _build_toolbar(self):
        bar = QFrame()
        bar.setObjectName('toolbar')
        h = QHBoxLayout(bar)
        h.setContentsMargins(10, 8, 10, 8)
        h.setSpacing(6)

        # 기체 필터 콤보만 유지
        self._combo = QComboBox()
        self._combo.setFixedWidth(110)
        self._combo.currentTextChanged.connect(
            lambda v: setattr(inventory, 'filter_aircraft', v)
        )
        h.addWidget(self._combo)

        # 검색창 1개
        self._search = QLineEdit()
        self._search.setObjectName('searchInput')
        self._search.setPlaceholderText('부품번호 / 명칭 검색')
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._on_search_debounced)
        self._search.textChanged.connect(lambda: self._debounce.start(300))
        h.addWidget(self._search, 1)

        # 추가 버튼
        btn_add = QPushButton('+')
        btn_add.setObjectName('btnAdd')
        btn_add.setToolTip('부품 추가')
        h.addWidget(btn_add)

        return bar

    def _build_table(self):
        self._table = QTableWidget()
        self._table.setColumnCount(len(self.COLS))
        self._table.setHorizontalHeaderLabels([c[0] for c in self.COLS])
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self._table.horizontalHeader().sectionClicked.connect(self._on_header_click)

        # 컬럼 너비
        widths = [40, 130, 160, None, 60, 70, 60]
        for i, w in enumerate(widths):
            if w:
                self._table.setColumnWidth(i, w)

        return self._table

    # ── 시그널 연결 ──────────────────────────────────────────────
    def _connect_signals(self):
        inventory.filter_changed.connect(self.refresh)
        inventory.parts_changed.connect(self.refresh)

    # ── 슬롯 ─────────────────────────────────────────────────────
    def _on_header_click(self, col):
        key = self.COLS[col][1]
        if key:
            inventory.toggle_sort(key)

    def update_aircraft_filter(self, types: list):
        """DashboardLeft의 기체 콤보박스를 통해 외부에서 호출됨 — 여기선 무시"""
        pass

    # ── 테이블 렌더링 ─────────────────────────────────────────────
    def refresh(self):
        parts = inventory.get_filtered_parts()
        self._table.setRowCount(len(parts))

        sort_key = inventory.sort_key
        sort_dir  = inventory.sort_dir

        # 헤더 정렬 표시
        for col, (label, key) in enumerate(self.COLS):
            if key and key == sort_key:
                arrow = ' ▲' if sort_dir == 'asc' else ' ▼'
                self._table.horizontalHeaderItem(col).setText(label + arrow)
            elif key:
                self._table.horizontalHeaderItem(col).setText(label)

        for row, p in enumerate(parts):
            qty      = p.get('qty', 0)
            safe_qty = p.get('safe_qty', 0)
            bg, fg   = _stock_color(qty, safe_qty)

            cells = [
                str(row + 1),
                p.get('cycle', ''),
                p.get('part_no', ''),
                p.get('name', ''),
                str(qty),
                str(safe_qty),
                p.get('location', '-'),
            ]

            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignCenter if col != 3 and col != 6
                    else Qt.AlignLeft | Qt.AlignVCenter
                )
                # 재고 열 색상
                if col == 4:
                    item.setBackground(bg)
                    item.setForeground(fg)
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)

                self._table.setItem(row, col, item)

        self._table.resizeRowsToContents()