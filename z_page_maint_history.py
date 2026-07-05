"""
page_maint_history.py
메뉴 > 항공기 관리 > 정비 이력 - 와이어프레임(img_04) 기준
3개 테이블:
  좌: 정기 정비 (□/기체등록번호/누적비행시간/정비종류/주기/담당자/날짜)
  중: 비정기 정비 (□/기체등록번호/누적비행시간/정비종류/담당자/날짜)
  우: 교체 부품 목록 (부품번호/부품명칭/교체수량)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QDialog, QLineEdit, QComboBox, QMessageBox, QLabel, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
import pandas as pd
from styles import COLOR
from api import fetch_maint_history, insert_maint_history, delete_maint_history
from dialogs_maint import MaintHistoryDialog

ROW_H = 52
AC_TYPES = ['-- 전체 --', 'DA-40NG', 'DA-42NG']
MAINT_TYPES = [
    '-- 전체 --',
    '항공기 100 HRS', '항공기 200 HRS', '항공기 1000 HRS', '항공기 2000 HRS',
    "ENG' 100 HRS", "ENG' 300 HRS", "ENG' 600 HRS", "ENG' 900 HRS",
    "ENG'교체(1800시간&12년)", 'TRP_100H', 'Annual', 'MSB-E4-043(50시간)',
]


def _section_lbl(text):
    lbl = QLabel(text)
    lbl.setFont(QFont('', 16, QFont.Bold))
    lbl.setStyleSheet(
        f'color:white; background:{COLOR["primary"]};'
        f'padding:8px 12px; border-radius:4px 4px 0 0;'
    )
    lbl.setFixedHeight(38)
    return lbl


class MaintHistoryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []
        self._sort_reg = (-1, True)
        self._sort_irr = (-1, True)
        self._build_ui()
        self._load()

    # ── UI 구성 ──────────────────────────────────────────────────
    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ── 툴바 ──
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

        self._type_combo = QComboBox()
        self._type_combo.addItems(MAINT_TYPES)
        self._type_combo.setFixedWidth(180)
        self._type_combo.currentTextChanged.connect(self._refresh)

        self._search = QLineEdit()
        self._search.setObjectName('searchInput')
        self._search.setPlaceholderText('기체번호 / 담당자 검색')
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

        btn_excel = QPushButton()
        btn_excel.setIcon(QIcon('excel.png'))
        btn_excel.setFixedSize(32, 32)
        btn_excel.setStyleSheet('QPushButton { border: none; padding: 0px; }')
        btn_excel.setToolTip('CSV로 내보내기')
        btn_excel.clicked.connect(self._on_excel)

        th.addWidget(self._ac_combo)
        th.addWidget(self._type_combo)
        th.addWidget(self._search, 1)
        th.addStretch()
        th.addWidget(btn_excel)
        th.addWidget(btn_add)
        th.addWidget(btn_del)
        v.addWidget(tb)

        # ── 3개 테이블 스플리터 ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#d0d7e2; }
            QSplitter::handle:hover { background:#4a90d9; }
        """)
        splitter.addWidget(self._build_regular_panel())
        splitter.addWidget(self._build_irregular_panel())
        splitter.addWidget(self._build_parts_panel())
        splitter.setSizes([450, 450, 450])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        v.addWidget(splitter, 1)

    # ── 정기 정비 패널 ──────────────────────────────────────────
    def _build_regular_panel(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(_section_lbl('정기 정비'))

        self._tbl_reg = QTableWidget()
        cols = ['', '기체 등록번호', '누적 비행시간', '정비 종류',
                '주기', '담당자', '날짜']
        self._tbl_reg.setColumnCount(len(cols))
        self._tbl_reg.setHorizontalHeaderLabels(cols)
        self._tbl_reg.setSelectionBehavior(QTableWidget.SelectRows)
        self._tbl_reg.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tbl_reg.verticalHeader().setVisible(False)
        self._tbl_reg.verticalHeader().setDefaultSectionSize(ROW_H)

        hdr = self._tbl_reg.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        self._tbl_reg.setColumnWidth(0, 44)
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)
        for col in [1, 2, 4, 5, 6]:
            hdr.setSectionResizeMode(col, QHeaderView.Interactive)
        self._tbl_reg.setColumnWidth(1, 160)
        self._tbl_reg.setColumnWidth(2, 160)
        self._tbl_reg.setColumnWidth(4, 140)
        self._tbl_reg.setColumnWidth(5, 180)
        self._tbl_reg.setColumnWidth(6, 160)
        hdr.setMinimumSectionSize(60)

        self._tbl_reg.itemSelectionChanged.connect(self._on_reg_select)
        self._tbl_reg.horizontalHeader().sectionClicked.connect(
            self._on_reg_header)
        v.addWidget(self._tbl_reg, 1)
        return w

    # ── 비정기 정비 패널 ────────────────────────────────────────
    def _build_irregular_panel(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(_section_lbl('비정기 정비'))

        self._tbl_irr = QTableWidget()
        cols = ['', '기체 등록번호', '누적 비행시간', '정비 종류',
                '담당자', '날짜']
        self._tbl_irr.setColumnCount(len(cols))
        self._tbl_irr.setHorizontalHeaderLabels(cols)
        self._tbl_irr.setSelectionBehavior(QTableWidget.SelectRows)
        self._tbl_irr.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tbl_irr.verticalHeader().setVisible(False)
        self._tbl_irr.verticalHeader().setDefaultSectionSize(ROW_H)

        hdr = self._tbl_irr.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        self._tbl_irr.setColumnWidth(0, 44)
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)
        for col in [1, 2, 4, 5]:
            hdr.setSectionResizeMode(col, QHeaderView.Interactive)
        self._tbl_irr.setColumnWidth(1, 160)
        self._tbl_irr.setColumnWidth(2, 160)
        self._tbl_irr.setColumnWidth(4, 180)
        self._tbl_irr.setColumnWidth(5, 160)
        hdr.setMinimumSectionSize(60)

        self._tbl_irr.itemSelectionChanged.connect(self._on_irr_select)
        self._tbl_irr.horizontalHeader().sectionClicked.connect(
            self._on_irr_header)
        v.addWidget(self._tbl_irr, 1)
        return w

    # ── 교체 부품 목록 패널 ─────────────────────────────────────
    def _build_parts_panel(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(_section_lbl('교체 부품 목록'))

        self._tbl_parts = QTableWidget()
        cols = ['부품번호', '부품명칭', '교체 수량']
        self._tbl_parts.setColumnCount(len(cols))
        self._tbl_parts.setHorizontalHeaderLabels(cols)
        self._tbl_parts.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tbl_parts.verticalHeader().setVisible(False)
        self._tbl_parts.verticalHeader().setDefaultSectionSize(ROW_H)

        hdr = self._tbl_parts.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(0, QHeaderView.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.Interactive)
        self._tbl_parts.setColumnWidth(0, 140)
        self._tbl_parts.setColumnWidth(2, 120)
        hdr.setMinimumSectionSize(60)

        v.addWidget(self._tbl_parts, 1)
        return w

    # ── 정기/비정기 판별 ────────────────────────────────────────
    @staticmethod
    def _is_regular(maint_type: str) -> bool:
        kw = ['HRS', '100', '200', '300', '600', '900',
              '1000', '1800', '2000', 'TRP', 'Annual', 'MSB']
        return any(k in maint_type for k in kw)

    # ── 데이터 로드 ─────────────────────────────────────────────
    def _load(self):
        try:
            self._history = fetch_maint_history()
        except Exception as e:
            print(f'❌ [MaintHistoryPage] 로드 실패: {e}')
            self._history = []
        self._refresh()

    # ── 헤더 클릭 정렬 ─────────────────────────────────────────
    def _on_reg_header(self, col):
        c, asc = self._sort_reg
        self._sort_reg = (col, not asc if c == col else True)
        self._refresh()

    def _on_irr_header(self, col):
        c, asc = self._sort_irr
        self._sort_irr = (col, not asc if c == col else True)
        self._refresh()

    # ── 테이블 갱신 ─────────────────────────────────────────────
    def _refresh(self):
        ac = self._ac_combo.currentText()
        mtype = self._type_combo.currentText()
        kw = self._search.text().strip().lower()

        from inventory import inventory
        ac_type_map = {
            a.get('id', ''): a.get('type', '').replace(' ', '')
            for a in inventory.aircraft_list
        }

        def _match_type(r):
            if ac == '-- 전체 --':
                return True
            reg = r.get('aircraft_id', '') or ''
            ac_type = ac_type_map.get(reg, '').replace(' ', '')
            target = ac.replace(' ', '')
            if ac_type and ac_type == target:
                return True
            reg_norm = reg.replace(' ', '').replace('-', '').upper()
            tgt_norm = target.replace('-', '').upper()
            return reg_norm == tgt_norm

        def _match_mtype(r):
            if mtype == '-- 전체 --':
                return True
            val = (r.get('maint_type', '') or '').strip()
            if val == mtype:
                return True
            return val.replace(' ', '') == mtype.replace(' ', '')

        filtered = [
            r for r in self._history
            if _match_type(r)
            and _match_mtype(r)
            and (not kw
                 or kw in (r.get('aircraft_id', '') or '').lower()
                 or kw in (r.get('technician', '') or '').lower())
        ]

        regular = [r for r in filtered
                    if self._is_regular(r.get('maint_type', ''))]
        irregular = [r for r in filtered
                     if not self._is_regular(r.get('maint_type', ''))]

        self._fill_reg_table(regular)
        self._fill_irr_table(irregular)
        self._tbl_parts.setRowCount(0)

    # ── 정기 정비 테이블 채우기 ─────────────────────────────────
    def _fill_reg_table(self, regular):
        REG_KEYS = ['', 'aircraft_id', 'flight_hrs', 'maint_type',
                    'inspection_interval', 'technician', 'date']
        rc, ra = self._sort_reg
        if 0 < rc < len(REG_KEYS) and REG_KEYS[rc]:
            regular.sort(
                key=lambda r: str(r.get(REG_KEYS[rc], '')),
                reverse=not ra)

        REG_LABELS = ['', '기체 등록번호', '누적 비행시간', '정비 종류',
                      '주기', '담당자', '날짜']
        for col, lbl in enumerate(REG_LABELS):
            h = self._tbl_reg.horizontalHeaderItem(col)
            if h:
                arrow = (' ▲' if ra else ' ▼') if col == rc else ''
                h.setText(lbl + arrow)

        self._tbl_reg.setRowCount(len(regular))
        for row, r in enumerate(regular):
            self._tbl_reg.setRowHeight(row, ROW_H)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setFlags(
                Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
                | Qt.ItemIsSelectable)
            chk.setData(Qt.UserRole, r)
            self._tbl_reg.setItem(row, 0, chk)

            cells = [
                (r.get('aircraft_id', ''), Qt.AlignCenter),
                (f"{r.get('flight_hrs', 0):,.0f} H", Qt.AlignCenter),
                (r.get('maint_type', ''),
                 Qt.AlignLeft | Qt.AlignVCenter),
                (r.get('inspection_interval', '') or '-',
                 Qt.AlignCenter),
                (r.get('technician', ''), Qt.AlignCenter),
                (r.get('date', ''), Qt.AlignCenter),
            ]
            for col, (text, align) in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setData(Qt.UserRole, r)
                self._tbl_reg.setItem(row, col + 1, item)

    # ── 비정기 정비 테이블 채우기 ───────────────────────────────
    def _fill_irr_table(self, irregular):
        IRR_KEYS = ['', 'aircraft_id', 'flight_hrs', 'maint_type',
                    'technician', 'date']
        ic, ia = self._sort_irr
        if 0 < ic < len(IRR_KEYS) and IRR_KEYS[ic]:
            irregular.sort(
                key=lambda r: str(r.get(IRR_KEYS[ic], '')),
                reverse=not ia)

        IRR_LABELS = ['', '기체 등록번호', '누적 비행시간', '정비 종류',
                      '담당자', '날짜']
        for col, lbl in enumerate(IRR_LABELS):
            h = self._tbl_irr.horizontalHeaderItem(col)
            if h:
                arrow = (' ▲' if ia else ' ▼') if col == ic else ''
                h.setText(lbl + arrow)

        self._tbl_irr.setRowCount(len(irregular))
        for row, r in enumerate(irregular):
            self._tbl_irr.setRowHeight(row, ROW_H)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setFlags(
                Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
                | Qt.ItemIsSelectable)
            chk.setData(Qt.UserRole, r)
            self._tbl_irr.setItem(row, 0, chk)

            cells = [
                (r.get('aircraft_id', ''), Qt.AlignCenter),
                (f"{r.get('flight_hrs', 0):,.0f} H", Qt.AlignCenter),
                (r.get('maint_type', ''),
                 Qt.AlignLeft | Qt.AlignVCenter),
                (r.get('technician', ''), Qt.AlignCenter),
                (r.get('date', ''), Qt.AlignCenter),
            ]
            for col, (text, align) in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setData(Qt.UserRole, r)
                self._tbl_irr.setItem(row, col + 1, item)

    # ── 행 선택 → 교체 부품 목록 표시 ──────────────────────────
    def _on_reg_select(self):
        rows = set(i.row() for i in self._tbl_reg.selectedItems())
        if not rows:
            return
        item = self._tbl_reg.item(list(rows)[0], 0)
        self._show_parts(item.data(Qt.UserRole) if item else None)

    def _on_irr_select(self):
        rows = set(i.row() for i in self._tbl_irr.selectedItems())
        if not rows:
            return
        item = self._tbl_irr.item(list(rows)[0], 0)
        self._show_parts(item.data(Qt.UserRole) if item else None)

    def _show_parts(self, record):
        if not record:
            return
        parts = record.get('parts', [])
        self._tbl_parts.setRowCount(len(parts))
        for row, p in enumerate(parts):
            self._tbl_parts.setRowHeight(row, ROW_H)
            texts = [
                p.get('part_no', '') or str(p.get('part_id', '')),
                p.get('name', ''),
                str(p.get('qty', 1)),
            ]
            for col, text in enumerate(texts):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self._tbl_parts.setItem(row, col, item)

    # ── CSV 내보내기 ────────────────────────────────────────────
    def _on_excel(self):
        file, _ = QFileDialog.getSaveFileName(
            self, 'CSV로 내보내기', '',
            'CSV Files (*.csv);;All Files (*)')
        if not file:
            return
        try:
            reg_data = []
            for i in range(self._tbl_reg.rowCount()):
                r = self._tbl_reg.item(i, 0).data(Qt.UserRole)
                reg_data.append([
                    r.get('aircraft_id', ''),
                    r.get('flight_hrs', 0),
                    r.get('maint_type', ''),
                    r.get('inspection_interval', ''),
                    r.get('technician', ''),
                    r.get('date', ''),
                ])
            df_reg = pd.DataFrame(reg_data, columns=[
                '기체 등록번호', '누적 비행시간', '정비 종류',
                '주기', '담당자', '날짜'])

            irr_data = []
            for i in range(self._tbl_irr.rowCount()):
                r = self._tbl_irr.item(i, 0).data(Qt.UserRole)
                irr_data.append([
                    r.get('aircraft_id', ''),
                    r.get('flight_hrs', 0),
                    r.get('maint_type', ''),
                    r.get('technician', ''),
                    r.get('date', ''),
                ])
            df_irr = pd.DataFrame(irr_data, columns=[
                '기체 등록번호', '누적 비행시간', '정비 종류',
                '담당자', '날짜'])

            with open(file, 'w', newline='', encoding='utf-8-sig') as f:
                f.write('정기 정비\n')
                df_reg.to_csv(f, index=False)
                f.write('\n비정기 정비\n')
                df_irr.to_csv(f, index=False)

            QMessageBox.information(
                self, 'CSV 내보내기',
                'CSV 파일로 내보내기가 완료되었습니다.')
        except Exception as e:
            QMessageBox.critical(
                self, 'CSV 내보내기 실패',
                f'오류가 발생했습니다:\n{str(e)}')

    # ── 등록 ────────────────────────────────────────────────────
    def _on_add(self):
        dlg = MaintHistoryDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            try:
                result = insert_maint_history(d)
                self._history.insert(0, result)
            except Exception as e:
                print(f'❌ [MaintHistoryPage] 등록 실패: {e}')
                self._history.insert(0, d)
            self._load()

    # ── 삭제 ────────────────────────────────────────────────────
    def _on_delete(self):
        ids = set()
        for tbl in [self._tbl_reg, self._tbl_irr]:
            for row in range(tbl.rowCount()):
                item = tbl.item(row, 0)
                if item and item.checkState() == Qt.Checked:
                    ids.add(item.data(Qt.UserRole).get('id'))
        if not ids:
            QMessageBox.information(
                self, '알림', '삭제할 항목을 체크하세요.')
            return
        reply = QMessageBox.question(
            self, '삭제 확인',
            f'{len(ids)}개 정비 이력을 삭제하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            delete_maint_history(list(ids))
        except Exception as e:
            print(f'❌ [MaintHistoryPage] 삭제 실패: {e}')
        self._history = [
            r for r in self._history if r.get('id') not in ids]
        self._refresh()