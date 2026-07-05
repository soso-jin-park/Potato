"""
page_maint_history.py
정비 이력 페이지 (정기/비정기/교체부품 3분할)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QLineEdit, QComboBox, QMessageBox, QLabel, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from styles import COLOR
from api import fetch_maint_history, insert_maint_history, delete_maint_history
from dialogs_maint import MaintHistoryDialog
from page_maint_history_io import MaintHistoryIOMixin

ROW_H = 52
AC_TYPES = ['-- 전체 --', 'DA-40NG', 'DA-42NG']
MAINT_TYPES = [
    '-- 전체 --',
    '항공기 100 HRS', '항공기 200 HRS', '항공기 1000 HRS', '항공기 2000 HRS',
    "ENG' 100 HRS", "ENG' 300 HRS", "ENG' 600 HRS", "ENG' 900 HRS",
    "ENG'교체(1800시간&12년)", 'TRP_100H', 'Annual', 'MSB-E4-043(50시간)']


def _section_lbl(text):
    lbl = QLabel(text)
    lbl.setFont(QFont('', 16, QFont.Bold))
    lbl.setStyleSheet(
        f'color:white; background:{COLOR["primary"]};'
        f'padding:8px 12px; border-radius:4px 4px 0 0;')
    lbl.setFixedHeight(38)
    return lbl


def _make_table(cols, widths, stretch_col, fixed0=True):
    tbl = QTableWidget()
    tbl.setColumnCount(len(cols))
    tbl.setHorizontalHeaderLabels(cols)
    tbl.setSelectionBehavior(QTableWidget.SelectRows)
    tbl.setEditTriggers(QTableWidget.NoEditTriggers)
    tbl.verticalHeader().setVisible(False)
    tbl.verticalHeader().setDefaultSectionSize(ROW_H)
    hdr = tbl.horizontalHeader()
    if fixed0:
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        tbl.setColumnWidth(0, 44)
    hdr.setSectionResizeMode(stretch_col, QHeaderView.Stretch)
    for c, w in widths.items():
        hdr.setSectionResizeMode(c, QHeaderView.Interactive)
        tbl.setColumnWidth(c, w)
    hdr.setMinimumSectionSize(100)
    return tbl


class MaintHistoryPage(MaintHistoryIOMixin, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []
        self._sort_reg = (-1, True)
        self._sort_irr = (-1, True)
        self._build_ui()
        self._load()

    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        tb = QFrame()
        tb.setStyleSheet(
            f'background:#fafbfc; border-bottom:1px solid {COLOR["border"]};')
        th = QHBoxLayout(tb)
        th.setContentsMargins(12, 10, 12, 10); th.setSpacing(8)

        self._ac_combo = QComboBox()
        self._ac_combo.addItems(AC_TYPES); self._ac_combo.setFixedWidth(140)
        self._ac_combo.currentTextChanged.connect(self._refresh)
        self._type_combo = QComboBox()
        self._type_combo.addItems(MAINT_TYPES); self._type_combo.setFixedWidth(180)
        self._type_combo.currentTextChanged.connect(self._refresh)
        self._search = QLineEdit()
        self._search.setObjectName('searchInput')
        self._search.setPlaceholderText('기체번호 / 담당자 검색')
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

        th.addWidget(self._ac_combo); th.addWidget(self._type_combo)
        th.addWidget(self._search, 1); th.addStretch()
        th.addWidget(btn_add); th.addWidget(btn_del)
        v.addWidget(tb)

        sp = QSplitter(Qt.Horizontal); sp.setHandleWidth(5)
        sp.setStyleSheet('QSplitter::handle{background:#d0d7e2}'
                         'QSplitter::handle:hover{background:#4a90d9}')
        sp.addWidget(self._build_regular_panel())
        sp.addWidget(self._build_irregular_panel())
        sp.addWidget(self._build_parts_panel())
        sp.setSizes([450, 450, 450])
        sp.setStretchFactor(0, 1); sp.setStretchFactor(1, 1)
        sp.setStretchFactor(2, 0)
        v.addWidget(sp, 1)

    def _build_regular_panel(self):
        w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        v.addWidget(_section_lbl('정기 정비'))
        self._tbl_reg = _make_table(
            ['', '기체 등록번호', '누적 비행시간', '정비 종류', '주기', '담당자', '날짜'],
            {1: 160, 2: 160, 4: 140, 5: 180, 6: 160}, stretch_col=3)
        self._tbl_reg.itemSelectionChanged.connect(self._on_reg_select)
        self._tbl_reg.horizontalHeader().sectionClicked.connect(self._on_reg_header)
        v.addWidget(self._tbl_reg, 1); return w

    def _build_irregular_panel(self):
        w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        v.addWidget(_section_lbl('비정기 정비'))
        self._tbl_irr = _make_table(
            ['', '기체 등록번호', '누적 비행시간', '정비 종류', '담당자', '날짜'],
            {1: 160, 2: 160, 4: 180, 5: 160}, stretch_col=3)
        self._tbl_irr.itemSelectionChanged.connect(self._on_irr_select)
        self._tbl_irr.horizontalHeader().sectionClicked.connect(self._on_irr_header)
        v.addWidget(self._tbl_irr, 1); return w

    def _build_parts_panel(self):
        w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        v.addWidget(_section_lbl('교체 부품 목록'))
        self._tbl_parts = _make_table(
            ['부품번호', '부품명칭', '교체 수량'],
            {0: 140, 2: 120}, stretch_col=1, fixed0=False)
        v.addWidget(self._tbl_parts, 1); return w

    @staticmethod
    def _is_regular(mt: str) -> bool:
        return any(k in mt for k in [
            'HRS', '100', '200', '300', '600', '900',
            '1000', '1800', '2000', 'TRP', 'Annual', 'MSB'])

    def _load(self):
        try:
            self._history = fetch_maint_history()
        except Exception as e:
            print(f'❌ [MaintHistoryPage] 로드 실패: {e}')
            self._history = []
        self._refresh()

    def reset(self):
        """필터/검색/정렬 초기화 후 데이터 재로드"""
        self._ac_combo.setCurrentIndex(0)
        self._type_combo.setCurrentIndex(0)
        self._search.clear()
        self._sort_reg = (-1, True)
        self._sort_irr = (-1, True)
        self._tbl_parts.setRowCount(0)
        self._load()

    def _on_reg_header(self, col):
        c, a = self._sort_reg
        self._sort_reg = (col, not a if c == col else True); self._refresh()

    def _on_irr_header(self, col):
        c, a = self._sort_irr
        self._sort_irr = (col, not a if c == col else True); self._refresh()

    def _refresh(self):
        ac = self._ac_combo.currentText()
        mtype = self._type_combo.currentText()
        kw = self._search.text().strip().lower()
        from inventory import inventory
        amap = {a.get('id', ''): a.get('type', '').replace(' ', '')
                for a in inventory.aircraft_list}

        def _mac(r):
            if ac == '-- 전체 --': return True
            reg = r.get('aircraft_id', '') or ''
            t = amap.get(reg, '').replace(' ', ''); tgt = ac.replace(' ', '')
            if t and t == tgt: return True
            return (reg.replace(' ', '').replace('-', '').upper()
                    == tgt.replace('-', '').upper())

        def _mmt(r):
            if mtype == '-- 전체 --': return True
            val = (r.get('maint_type', '') or '').strip()
            return val == mtype or val.replace(' ', '') == mtype.replace(' ', '')

        f = [r for r in self._history
             if _mac(r) and _mmt(r)
             and (not kw
                  or kw in (r.get('aircraft_id', '') or '').lower()
                  or kw in (r.get('technician', '') or '').lower())]
        self._fill_reg([r for r in f if self._is_regular(r.get('maint_type', ''))])
        self._fill_irr([r for r in f if not self._is_regular(r.get('maint_type', ''))])
        self._tbl_parts.setRowCount(0)

    def _on_add(self):
        dlg = MaintHistoryDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            if isinstance(d, list):
                # 파일 업로드로 다건 등록
                for rec in d:
                    try:
                        result = insert_maint_history(rec)
                        self._history.insert(0, result)
                    except Exception:
                        pass
            else:
                try:
                    result = insert_maint_history(d)
                    self._history.insert(0, result)
                except Exception as e:
                    print(f'❌ 등록 실패: {e}')
                    self._history.insert(0, d)
            self._load()

    def _on_delete(self):
        ids = set()
        for tbl in [self._tbl_reg, self._tbl_irr]:
            for row in range(tbl.rowCount()):
                it = tbl.item(row, 0)
                if it and it.checkState() == Qt.Checked:
                    ids.add(it.data(Qt.UserRole).get('id'))
        if not ids:
            QMessageBox.information(self, '알림', '삭제할 항목을 체크하세요.')
            return
        if QMessageBox.question(
                self, '삭제 확인', f'{len(ids)}개 삭제하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            delete_maint_history(list(ids))
        except Exception as e:
            print(f'❌ 삭제 실패: {e}')
        self._history = [r for r in self._history if r.get('id') not in ids]
        self._refresh()