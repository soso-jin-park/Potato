"""
page_inout.py
메뉴 > 재고관리 > 입출고 관리 - 와이어프레임(img_00) 기준
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QLineEdit, QComboBox, QLabel, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from styles import COLOR
from api import fetch_inbound, fetch_outbound, insert_inbound, insert_outbound
from dialogs_inout import InboundDialog, OutboundDialog

ROW_H    = 52
AC_TYPES = ['전체', 'DA-40NG', 'DA-42NG']

IN_LABELS  = ['', '부품번호', '부품명칭', '재고 수량', '안전재고 수량', '입고 날짜']
OUT_LABELS = ['', '부품번호', '부품명칭', '재고 수량', '출고 수량', '지역', '담당자', '출고 날짜']
IN_KEYS    = ['', 'part_no', 'name', 'qty', '', 'date']
OUT_KEYS   = ['', 'part_no', 'name', 'qty', 'qty', 'region', 'technician', 'date']


class InOutPage(QWidget):
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
        tb.setStyleSheet(f'background:#fafbfc; border-bottom:1px solid {COLOR["border"]};')
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
            f'padding:8px 18px; border-radius:4px; font-size:18px;'
        )
        btn_in.clicked.connect(self._on_inbound)

        btn_out = QPushButton('− 출고')
        btn_out.setStyleSheet(
            f'background:{COLOR["secondary"]}; color:white; border:none;'
            f'padding:8px 18px; border-radius:4px; font-size:18px;'
        )
        btn_out.clicked.connect(self._on_outbound)

        self._search = QLineEdit()
        self._search.setObjectName('searchInput')
        self._search.setPlaceholderText('부품번호 / 명칭 검색')
        self._search.textChanged.connect(self._refresh)

        th.addWidget(self._ac_combo)
        th.addWidget(btn_in)
        th.addWidget(btn_out)
        th.addWidget(self._search, 1)
        v.addWidget(tb)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#d0d7e2; }
            QSplitter::handle:hover { background:#4a90d9; }
        """)
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
        if col == 0:
            return
        c, asc = self._sort_in
        self._sort_in = (col, not asc if c == col else True)
        self._refresh()

    def _on_out_header(self, col):
        if col == 0:
            return
        c, asc = self._sort_out
        self._sort_out = (col, not asc if c == col else True)
        self._refresh()

    def _load(self):
        try:
            self._inbound = fetch_inbound()
        except Exception as e:
            print(f'❌ [InOutPage] 입고 로드 실패: {e}')
        try:
            self._outbound = fetch_outbound()
        except Exception as e:
            print(f'❌ [InOutPage] 출고 로드 실패: {e}')
        self._refresh()

    def _refresh(self):
        kw = self._search.text().strip().lower()

        # ── 입고 테이블 ──
        in_data = [
            r for r in self._inbound
            if not kw or kw in r.get('part_no', '').lower()
            or kw in r.get('name', '').lower()
        ]
        in_col, in_asc = self._sort_in
        if 0 < in_col < len(IN_KEYS) and IN_KEYS[in_col]:
            in_data.sort(key=lambda r: str(r.get(IN_KEYS[in_col], '')), reverse=not in_asc)
        for col, lbl in enumerate(IN_LABELS):
            h = self._tbl_in.horizontalHeaderItem(col)
            if h:
                h.setText(lbl + (' ▲' if in_asc else ' ▼') if col == in_col else lbl)

        self._tbl_in.setRowCount(len(in_data))
        for row, r in enumerate(in_data):
            self._tbl_in.setRowHeight(row, ROW_H)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            chk.setData(Qt.UserRole, r)
            self._tbl_in.setItem(row, 0, chk)

            cells = [
                r.get('part_no', ''), r.get('name', ''),
                str(r.get('qty', 0)), '',
                r.get('date', ''),
            ]
            aligns = [
                Qt.AlignLeft | Qt.AlignVCenter,
                Qt.AlignLeft | Qt.AlignVCenter,
                Qt.AlignCenter, Qt.AlignCenter,
                Qt.AlignCenter,
            ]
            for i, (text, align) in enumerate(zip(cells, aligns)):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setData(Qt.UserRole, r)
                self._tbl_in.setItem(row, i + 1, item)

        # ── 출고 테이블 ──
        out_data = [
            r for r in self._outbound
            if not kw or kw in r.get('part_no', '').lower()
            or kw in r.get('name', '').lower()
        ]
        out_col, out_asc = self._sort_out
        if 0 < out_col < len(OUT_KEYS) and OUT_KEYS[out_col]:
            out_data.sort(key=lambda r: str(r.get(OUT_KEYS[out_col], '')), reverse=not out_asc)
        for col, lbl in enumerate(OUT_LABELS):
            h = self._tbl_out.horizontalHeaderItem(col)
            if h:
                h.setText(lbl + (' ▲' if out_asc else ' ▼') if col == out_col else lbl)

        self._tbl_out.setRowCount(len(out_data))
        for row, r in enumerate(out_data):
            self._tbl_out.setRowHeight(row, ROW_H)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            chk.setData(Qt.UserRole, r)
            self._tbl_out.setItem(row, 0, chk)

            cells = [
                r.get('part_no', ''), r.get('name', ''),
                str(r.get('qty', 0)), str(r.get('qty', 0)),
                r.get('region', ''), r.get('technician', ''),
                r.get('date', ''),
            ]
            aligns = [
                Qt.AlignLeft | Qt.AlignVCenter,
                Qt.AlignLeft | Qt.AlignVCenter,
                Qt.AlignCenter, Qt.AlignCenter,
                Qt.AlignCenter, Qt.AlignCenter,
                Qt.AlignCenter,
            ]
            for i, (text, align) in enumerate(zip(cells, aligns)):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setData(Qt.UserRole, r)
                self._tbl_out.setItem(row, i + 1, item)

    def _on_inbound(self):
        dlg = InboundDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            if isinstance(d, list):
                for rec in d:
                    try:
                        r = insert_inbound(rec)
                        self._inbound.insert(0, r)
                    except Exception:
                        pass
            else:
                try:
                    result = insert_inbound(d)
                    self._inbound.insert(0, result)
                except Exception as e:
                    print(f'❌ [InOutPage] 입고 등록 실패: {e}')
                    self._inbound.insert(0, d)
            self._refresh()
            self._sync_parts()

    def _on_outbound(self):
        dlg = OutboundDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            if isinstance(d, list):
                for rec in d:
                    try:
                        r = insert_outbound(rec)
                        self._outbound.insert(0, r)
                    except Exception:
                        pass
            else:
                try:
                    result = insert_outbound(d)
                    self._outbound.insert(0, result)
                except Exception as e:
                    print(f'❌ [InOutPage] 출고 등록 실패: {e}')
                    self._outbound.insert(0, d)
            self._refresh()
            self._sync_parts()

    def reset(self):
        """필터/검색/정렬 초기화 후 데이터 재로드"""
        self._ac_combo.setCurrentIndex(0)
        self._search.clear()
        self._sort_in  = (-1, True)
        self._sort_out = (-1, True)
        self._load()

    def _sync_parts(self):
        """입출고 후 부품 재고를 다시 로드하여 전역 상태 갱신"""
        try:
            from api import fetch_parts
            from inventory import inventory
            fresh = fetch_parts()
            inventory.parts = fresh
            print(f"✅ [InOutPage] 부품 재고 동기화 완료: {len(fresh)}개")
        except Exception as e:
            print(f"❌ [InOutPage] 부품 재고 동기화 실패: {e}")