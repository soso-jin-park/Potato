"""
page_aircraft.py
메뉴 > 항공기 관리 > 기체 관리 - 와이어프레임(img_12) 기준
좌: 기종별 기체 목록 제거 / 중앙: 기체 상세 테이블 / 우: 부품 목록
더블클릭: 기체 수정 팝업
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QDialog, QLineEdit, QComboBox, QMessageBox, QScrollArea,
    QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from styles import COLOR
from api import fetch_aircraft_status
from dialogs_aircraft import AircraftDialog, AircraftEditDialog

ROW_H = 52


class AircraftPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._aircraft  = []
        self._selected  = None
        self._sort_col  = -1
        self._sort_asc  = True
        self._build_ui()
        self._load()

    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ── 툴바 ──
        tb = QFrame()
        tb.setStyleSheet(f'background:#fafbfc; border-bottom:1px solid {COLOR["border"]};')
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
            f'padding:8px 18px; border-radius:4px; font-size:18px;'
        )
        btn_add.clicked.connect(self._on_add)

        btn_del = QPushButton('🗑 삭제')
        btn_del.setStyleSheet(
            f'background:{COLOR["red"]}; color:white; border:none;'
            f'padding:8px 18px; border-radius:4px; font-size:18px;'
        )
        btn_del.clicked.connect(self._on_delete)

        th.addWidget(self._ac_combo)
        th.addWidget(self._search, 1)
        th.addStretch()
        th.addWidget(btn_add)
        th.addWidget(btn_del)
        v.addWidget(tb)

        # ── 본문: 중앙+우 스플리터 ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#d0d7e2; }
            QSplitter::handle:hover { background:#4a90d9; }
        """)
        splitter.addWidget(self._build_center_panel())   # ← 기체 목록 테이블
        splitter.addWidget(self._build_right_panel())    # ← 부품 목록
        splitter.setSizes([700, 600])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        v.addWidget(splitter, 1)
    
    _COLS_DATA = [
        ('', None),             # col 0: 체크박스
        ('기체등록번호', 'id'),
        ('기체명칭/모델', None),
        ('기종', 'type'),
        ('제조년도', None),
        ('위치', None),
        ('누적비행시간', 'total_hours'),
        ('점검날짜', None),
    ]

    def _build_center_panel(self):
        panel = QFrame()
        panel.setStyleSheet('background:white;')
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self._table = QTableWidget()
        self._table.setColumnCount(len(self._COLS_DATA))
        self._table.setHorizontalHeaderLabels([c[0] for c in self._COLS_DATA])
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(ROW_H)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)  # 기체명칭 stretch
        hdr.sectionClicked.connect(self._on_header_click)

        self._table.setColumnWidth(0, 44)    # 체크박스
        self._table.setColumnWidth(1, 220)   # 기체등록번호
        self._table.setColumnWidth(3, 200)   # 기종
        self._table.setColumnWidth(4, 180)   # 제조년도
        self._table.setColumnWidth(5, 180)   # 위치
        self._table.setColumnWidth(6, 220)   # 누적비행시간
        self._table.setColumnWidth(7, 200)   # 점검날짜

        self._table.cellClicked.connect(self._on_row_click)
        self._table.doubleClicked.connect(self._on_double_click)
        v.addWidget(self._table, 1)
        return panel

    def _build_right_panel(self):
        panel = QFrame()
        panel.setMinimumWidth(550)
        panel.setMaximumWidth(700)
        panel.setStyleSheet(f'background:white; border-left:1px solid {COLOR["border"]};')
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        hdr = QFrame()
        hdr.setStyleSheet(f'background:#e8eef5; border-bottom:1px solid {COLOR["border"]};')
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
        self._parts_tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._parts_tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self._parts_tbl.setColumnWidth(0, 300)
        self._parts_tbl.verticalHeader().setDefaultSectionSize(ROW_H)
        v.addWidget(self._parts_tbl, 1)
        return panel

    def _load(self):
        try:
            self._aircraft = fetch_aircraft_status()
        except Exception as e:
            print(f'❌ [AircraftPage] 로드 실패: {e}')
            self._aircraft = []
        self._refresh()

    def _get_sort_key(self, ac):
        keys = [None, 'id', None, 'type', None, None, 'total_hours', None]
        col = self._sort_col
        if col < 0 or col >= len(keys) or not keys[col]:
            return ''
        val = ac.get(keys[col], '')
        if col == 6:
            try:
                return float(str(val).replace(',', '').replace('H', '').strip())
            except Exception:
                return 0
        return str(val).lower()

    def _on_header_click(self, col):
        if col == 0:
            return
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._refresh()

    def _refresh(self):
        ac_f = self._ac_combo.currentText()
        kw   = self._search.text().strip().lower()

        filtered = [
            ac for ac in self._aircraft
            if (ac_f == '-- 전체 --' or ac.get('type', '').replace(' ', '') == ac_f.replace(' ', ''))
            and (not kw or kw in ac.get('id', '').lower())
        ]

        if self._sort_col > 0:
            filtered.sort(key=self._get_sort_key, reverse=not self._sort_asc)

        for col, (label, _) in enumerate(self._COLS_DATA):
            h = self._table.horizontalHeaderItem(col)
            if h:
                h.setText(label + (' ▲' if self._sort_asc else ' ▼')
                          if col == self._sort_col else label)

        self._table.setRowCount(len(filtered))
        for row, ac in enumerate(filtered):
            self._table.setRowHeight(row, ROW_H)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            chk.setData(Qt.UserRole, ac)
            self._table.setItem(row, 0, chk)

            total = ac.get('total_hours', 0)
            cells = [
                ac.get('id', ''),
                ac.get('model', '') or ac.get('registration', ''),
                ac.get('type', ''),
                str(ac.get('manufacture_year', '') or '-'),
                ac.get('location', '-') or '-',
                f'{total:,.1f} H',
                '-',
            ]
            aligns = [
                Qt.AlignCenter, Qt.AlignLeft | Qt.AlignVCenter,
                Qt.AlignCenter, Qt.AlignCenter,
                Qt.AlignCenter, Qt.AlignCenter,
                Qt.AlignCenter,
            ]
            for col, (text, align) in enumerate(zip(cells, aligns)):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setData(Qt.UserRole, ac)
                self._table.setItem(row, col + 1, item)

    def _on_row_click(self, row, col):
        item = self._table.item(row, 1)
        if not item:
            return
        ac = item.data(Qt.UserRole)
        self._selected = ac
        # self._inst_date.setText('-')
        # self._inst_time.setText('-')
        # self._inst_loc.setText(ac.get('location', '-') or '-')
        # self._inst_status.setText(ac.get('status', '-') or '-')

        from api import fetch_bom_parts
        try:
            ac_model = ac.get('type', '').replace(' ', '')
            parts = fetch_bom_parts(ac_model)
            seen, unique = set(), []
            for p in parts:
                pno = p.get('part_no', '')
                if pno not in seen:
                    seen.add(pno)
                    unique.append(p)
            self._parts_tbl.setRowCount(len(unique))
            for r, p in enumerate(unique):
                for c, val in enumerate([p.get('part_no', ''), p.get('name', '')]):
                    it = QTableWidgetItem(val)
                    it.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self._parts_tbl.setItem(r, c, it)
        except Exception as e:
            print(f'❌ [AircraftPage] 부품 로드 실패: {e}')

    def _on_double_click(self, index):
        if index.column() == 0:
            return
        item = self._table.item(index.row(), 1)
        ac = item.data(Qt.UserRole) if item else None
        if not ac:
            return
        dlg = AircraftEditDialog(aircraft=ac, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            try:
                from api import update_aircraft
                update_aircraft(ac.get('db_id') or ac.get('id'), d)
            except Exception as e:
                print(f'❌ [AircraftPage] 기체 수정 실패: {e}')
            self._load()

    def _checked_aircraft(self):
        return [
            self._table.item(row, 0).data(Qt.UserRole)
            for row in range(self._table.rowCount())
            if self._table.item(row, 0) and
               self._table.item(row, 0).checkState() == Qt.Checked
        ]

    def _on_add(self):
        dlg = AircraftDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            if isinstance(d, list):
                print(f'✅ [AircraftPage] {len(d)}건 일괄 등록 요청')
                # TODO: insert_aircraft API 연결 시 여기서 일괄 INSERT
            self._load()

    def _on_delete(self):
        selected = self._checked_aircraft()
        if not selected:
            QMessageBox.information(self, '알림', '삭제할 기체를 체크하세요.')
            return
        reply = QMessageBox.question(
            self, '삭제 확인', f'{len(selected)}개 기체를 삭제하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        QMessageBox.information(self, '알림', '기체 삭제 기능은 준비 중입니다.')