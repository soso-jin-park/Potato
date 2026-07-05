"""
widget_parts.py
대시보드 좌측 부품 테이블 - 와이어프레임(img_08) 기준
컬럼: 체크박스 / 부품번호 / 부품명칭 / 재고 수량 / 안전재고 수량 / 위치 / 주기
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from inventory import inventory
from styles import COLOR


def _stock_color(qty, safe_qty):
    if qty == 0:
        return QColor('#f8d7da'), QColor('#721c24')
    if qty <= safe_qty:
        return QColor('#fff3cd'), QColor('#856404')
    return QColor('white'), QColor(COLOR['text'])


class PartsWidget(QWidget):
    COLS = [
        ('□',        None),
        ('부품번호',  'part_no'),
        ('부품명칭',  'name'),
        ('재고 수량', 'qty'),
        ('안전재고 수량', 'safe_qty'),
        ('위치',     'location'),
        ('주기',     'inspection_interval'),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_table())

    def _build_table(self):
        self._table = QTableWidget()
        self._table.setColumnCount(len(self.COLS))
        self._table.setHorizontalHeaderLabels([c[0] for c in self.COLS])
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.verticalHeader().setVisible(False)
        hdr = self._table.horizontalHeader()
        # 체크박스 고정
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        self._table.setColumnWidth(0, 32)
        # 부품명칭만 Stretch (남은 공간 채움)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        # 나머지는 Interactive (글자 길이 이상, 사용자가 조절 가능)
        for col in [1, 3, 4, 5, 6]:
            hdr.setSectionResizeMode(col, QHeaderView.Interactive)
        # 각 컬럼 최소 너비를 글자 기준으로 설정
        self._table.setColumnWidth(1, 300)   # 부품번호
        self._table.setColumnWidth(3, 200)    # 재고 수량
        self._table.setColumnWidth(4, 200)   # 안전재고 수량
        self._table.setColumnWidth(5, 200)    # 위치
        self._table.setColumnWidth(6, 400)   # 주기
        hdr.setMinimumSectionSize(60)
        hdr.sectionClicked.connect(self._on_header_click)
        return self._table

    def _connect_signals(self):
        inventory.filter_changed.connect(self.refresh)
        inventory.parts_changed.connect(self.refresh)

    def _on_header_click(self, col):
        key = self.COLS[col][1]
        if key:
            inventory.toggle_sort(key)

    def refresh(self):
        parts    = inventory.get_filtered_parts()
        sort_key = inventory.sort_key
        sort_dir = inventory.sort_dir

        self._table.setRowCount(len(parts))

        for col, (label, key) in enumerate(self.COLS):
            if not key:
                continue
            hdr = self._table.horizontalHeaderItem(col)
            if hdr:
                hdr.setText(
                    label + (' ▲' if sort_dir == 'asc' else ' ▼')
                    if key == sort_key else label
                )

        for row, p in enumerate(parts):
            qty      = p.get('qty', 0)
            safe_qty = p.get('safe_qty', 0)
            bg, fg   = _stock_color(qty, safe_qty)

            cells = [
                '□',
                p.get('part_no', ''),
                p.get('name', ''),
                str(qty),
                str(safe_qty),
                p.get('location', '-'),
                p.get('inspection_interval', ''),
            ]

            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignCenter if col in (0, 3, 4)
                    else Qt.AlignLeft | Qt.AlignVCenter
                )
                # 재고 수량 열만 색상
                if col == 3:
                    item.setBackground(bg)
                    item.setForeground(fg)
                    if qty == 0 or qty <= safe_qty:
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
                self._table.setItem(row, col, item)

        self._table.resizeRowsToContents()