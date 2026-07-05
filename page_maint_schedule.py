"""
page_maint_schedule.py
메뉴 > 항공기 관리 > 주기정비 현황 - 와이어프레임(img_15) 기준
좌: 기종별 기체 목록 + 선택 기체 상세
우 상단: 기체 주기 정비 | 엔진 주기 정비
우 하단: 프로펠러 | TRP | MSB 잔여 상태
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QLineEdit, QSplitter, QScrollArea,
    QGridLayout, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from styles import COLOR
from api import fetch_aircraft_status, fetch_bom_parts

ROW_H = 52


def _part_table(cols):
    t = QTableWidget()
    t.setColumnCount(len(cols))
    t.setHorizontalHeaderLabels(cols)
    t.setEditTriggers(QTableWidget.DoubleClicked)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(ROW_H)
    t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    t.setStyleSheet('font-size:20px;')
    return t


def _section_label(text):
    lbl = QLabel(text)
    lbl.setFont(QFont('', 20, QFont.Bold))
    lbl.setStyleSheet(f'color:{COLOR["primary"]}; padding:6px 0;')
    lbl.setFixedHeight(38)
    return lbl


class MaintSchedulePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ac_list  = []
        self._selected = None
        self._build_ui()
        self._load()

    def _build_ui(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # ── 좌측 패널 ──
        h.addWidget(self._build_left_panel())

        # ── 우측: 필터 + 4개 테이블 ──
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)

        # 필터 바
        tb = QFrame()
        tb.setStyleSheet(
            f'background:#fafbfc; border-bottom:1px solid {COLOR["border"]};'
        )
        th = QHBoxLayout(tb)
        th.setContentsMargins(12, 10, 12, 10)
        th.setSpacing(8)

        self._ac_combo = QComboBox()
        self._ac_combo.addItems(['-- 전체 --', 'DA-40NG', 'DA-42NG'])
        self._ac_combo.setFixedWidth(140)
        self._ac_combo.currentTextChanged.connect(self._on_ac_filter)

        self._type_combo = QComboBox()
        self._type_combo.addItems([
            '-- 전체 --',
            '항공기 100 HRS', '항공기 200 HRS', '항공기 1000 HRS', '항공기 2000 HRS',
            "ENG' 100 HRS", "ENG' 300 HRS", "ENG' 600 HRS", "ENG' 900 HRS",
            'TRP_100H', 'Annual', 'Propeller(2600시간&72개월)', 'Governor(2400시간&72개월)',
        ])
        self._type_combo.setFixedWidth(260)
        self._type_combo.currentTextChanged.connect(self._on_filter)

        self._search = QLineEdit()
        self._search.setObjectName('searchInput')
        self._search.setPlaceholderText('부품번호 / 명칭 검색')
        self._search.textChanged.connect(self._on_filter)

        th.addWidget(self._ac_combo)
        th.addWidget(self._type_combo)
        th.addWidget(self._search, 1)
        rv.addWidget(tb)

        # 테이블 영역 스크롤
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        cv = QVBoxLayout(content)
        cv.setContentsMargins(12, 12, 12, 12)
        cv.setSpacing(12)

        # 상단: 기체 주기 정비 | 엔진 주기 정비
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        left_top = QVBoxLayout()
        left_top.addWidget(_section_label('기체 주기 정비'))
        COLS = ['부품번호', '부품명칭', '재고 수량', '안전재고 수량', '정비종류']
        self._tbl_airframe = _part_table(COLS)
        self._tbl_airframe.doubleClicked.connect(
            lambda idx, t=self._tbl_airframe: self._on_double_click(t, idx))
        left_top.addWidget(self._tbl_airframe)
        lw = QWidget()
        lw.setLayout(left_top)
        top_row.addWidget(lw, 1)

        right_top = QVBoxLayout()
        right_top.addWidget(_section_label('엔진 주기 정비'))
        self._tbl_engine = _part_table(COLS)
        self._tbl_engine.doubleClicked.connect(
            lambda idx, t=self._tbl_engine: self._on_double_click(t, idx))
        right_top.addWidget(self._tbl_engine)
        rw = QWidget()
        rw.setLayout(right_top)
        top_row.addWidget(rw, 1)

        cv.addLayout(top_row)

        # 하단: 프로펠러 | TRP | MSB
        bot_row = QHBoxLayout()
        bot_row.setSpacing(12)

        prop_v = QVBoxLayout()
        prop_v.addWidget(_section_label('프로펠러'))
        self._tbl_prop = _part_table(COLS)
        self._tbl_prop.doubleClicked.connect(
            lambda idx, t=self._tbl_prop: self._on_double_click(t, idx))
        prop_v.addWidget(self._tbl_prop)
        pw = QWidget()
        pw.setLayout(prop_v)
        bot_row.addWidget(pw, 2)

        trp_v = QVBoxLayout()
        trp_v.addWidget(_section_label('TRP'))
        self._tbl_trp = _part_table(COLS)
        self._tbl_trp.doubleClicked.connect(
            lambda idx, t=self._tbl_trp: self._on_double_click(t, idx))
        trp_v.addWidget(self._tbl_trp)
        tw = QWidget()
        tw.setLayout(trp_v)
        bot_row.addWidget(tw, 2)

        # MSB 잔여 상태
        msb_v = QVBoxLayout()
        msb_v.addWidget(_section_label('MSB 잔여 상태(도래 여부)'))
        self._msb_panel = QWidget()
        self._msb_panel.setStyleSheet(
            f'background:#f8fafc; border:1px solid {COLOR["border"]}; border-radius:4px;'
        )
        self._msb_layout = QVBoxLayout(self._msb_panel)
        self._msb_layout.setContentsMargins(10, 10, 10, 10)
        self._msb_layout.setSpacing(6)
        msb_v.addWidget(self._msb_panel)
        mw = QWidget()
        mw.setLayout(msb_v)
        bot_row.addWidget(mw, 1)

        cv.addLayout(bot_row)
        scroll.setWidget(content)
        rv.addWidget(scroll, 1)

        h.addWidget(right, 1)

    def _build_left_panel(self):
        panel = QFrame()
        panel.setFixedWidth(340)
        panel.setStyleSheet(
            f'background:#f8fafc; border-right:1px solid {COLOR["border"]};'
        )
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # 선택 기체 상세
        self._detail_frame = QFrame()
        self._detail_frame.setStyleSheet(
            f'background:white; border-bottom:1px solid {COLOR["border"]};'
        )
        dv = QVBoxLayout(self._detail_frame)
        dv.setContentsMargins(14, 14, 14, 14)
        dv.setSpacing(12)

        # 기체번호 + 기종
        hdr_row = QHBoxLayout()
        self._detail_icon = QLabel('✈')
        self._detail_icon.setStyleSheet('font-size:22px; color:#555;')
        self._detail_reg = QLabel('-')
        self._detail_reg.setFont(QFont('', 22, QFont.Bold))
        self._detail_reg.setStyleSheet(f'color:{COLOR["primary"]};')
        self._detail_type = QLabel('')
        self._detail_type.setStyleSheet(
            f'color:white; background:{COLOR["secondary"]};'
            f'border-radius:3px; padding:3px 10px; font-size:18px; font-weight:bold;'
        )
        hdr_row.addWidget(self._detail_icon)
        hdr_row.addWidget(self._detail_reg)
        hdr_row.addStretch()
        hdr_row.addWidget(self._detail_type)
        dv.addLayout(hdr_row)

        # 주기 정비 탭 + 남은 시간
        tab_row = QHBoxLayout()
        tab_btn = QPushButton('기체')
        tab_btn.setFixedHeight(26)
        tab_btn.setStyleSheet(
            f'background:#e8eef5; color:{COLOR["primary"]}; border:1px solid {COLOR["border"]};'
            f'border-radius:3px; padding:2px 10px; font-size:16px;'
        )
        self._detail_remain = QLabel('주기 정비까지 남은 시간 : -')
        self._detail_remain.setStyleSheet(f'font-size:18px; color:{COLOR["text"]};')
        tab_row.addWidget(tab_btn)
        tab_row.addWidget(self._detail_remain)
        tab_row.addStretch()
        dv.addLayout(tab_row)

        # 누적 비행시간
        self._detail_total = QLabel('기체 누적 비행시간 : -')
        self._detail_total.setStyleSheet(
            f'background:#f0f4f8; border:1px solid {COLOR["border"]};'
            f'border-radius:4px; padding:8px 12px; font-size:20px;'
        )
        dv.addWidget(self._detail_total)

        v.addWidget(self._detail_frame)

        # 기체 목록 테이블 (기종/기체번호 1열)
        self._ac_table = QTableWidget()
        self._ac_table.setColumnCount(1)
        self._ac_table.setHorizontalHeaderLabels(['기체번호'])
        self._ac_table.setEditTriggers(QTableWidget.DoubleClicked)
        self._ac_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._ac_table.verticalHeader().setVisible(False)
        self._ac_table.verticalHeader().setDefaultSectionSize(52)
        hdr = self._ac_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        self._ac_table.setStyleSheet('font-size:20px;')
        self._ac_table.itemSelectionChanged.connect(self._on_table_select)
        v.addWidget(self._ac_table, 1)
        return panel

    def reset(self):
        """필터/검색/선택 초기화 후 데이터 재로드"""
        self._ac_combo.setCurrentIndex(0)
        self._type_combo.setCurrentIndex(0)
        self._search.clear()
        self._selected = None
        self._load()

    def _load(self):
        try:
            self._ac_list = fetch_aircraft_status()
        except Exception as e:
            print(f'❌ [MaintSchedulePage] 로드 실패: {e}')
            self._ac_list = []
        self._build_left_list()

    def _build_left_list(self):
        """기체 목록을 테이블로 표시 - 기체/기종 추가 시 자동 반영"""
        self._ac_table.setRowCount(0)
        for ac in self._ac_list:
            row = self._ac_table.rowCount()
            self._ac_table.insertRow(row)
            self._ac_table.setRowHeight(row, 44)

            reg_item = QTableWidgetItem(ac.get('id', ''))
            reg_item.setTextAlignment(Qt.AlignCenter)
            reg_item.setData(Qt.UserRole, ac)

            pct = ac.get('pct', 100)
            color = ('#dc3545' if pct < 30 else
                     '#fd7e14' if pct < 50 else COLOR['text'])
            reg_item.setForeground(QColor(color))
            self._ac_table.setItem(row, 0, reg_item)

    def _on_table_select(self):
        """테이블 행 선택 시 기체 상세 표시"""
        rows = self._ac_table.selectedItems()
        if not rows:
            return
        ac = self._ac_table.item(self._ac_table.currentRow(), 0).data(Qt.UserRole)
        if ac:
            self._on_select(ac)

    def _on_select(self, ac: dict):
        self._selected = ac
        reg   = ac.get('id', '')
        atype = ac.get('type', '')
        total = ac.get('total_hours', 0)
        next_h = ac.get('next_inspection', 0)

        self._detail_reg.setText(reg)
        self._detail_type.setText(atype)
        self._detail_remain.setText(f'주기 정비까지 남은 시간 : {next_h:.0f} H')
        self._detail_total.setText(f'기체 누적 비행시간 : {total:,.1f}H')

        # BOM 부품 로드
        ac_model = atype.replace(' ', '')
        try:
            parts = fetch_bom_parts(ac_model)
        except Exception:
            parts = []

        # 카테고리별 분류
        airframe, engine, propeller, trp = [], [], [], []
        msb_days = ac.get('msb_remaining')

        for p in parts:
            interval = p.get('inspection_interval', '') or ''
            type_t = p.get('maintenance_type', '') or ''
            combined = (interval + type_t).upper()

            if 'PROPELLER' in combined or '프로펠러' in combined or 'GOVERNOR' in combined:
                propeller.append(p)
            elif 'TRP' in combined:
                trp.append(p)
            elif 'ENG' in combined:
                engine.append(p)
            else:
                airframe.append(p)

        # 정비종류(type_combo) 필터 적용
        mtype_f = self._type_combo.currentText()
        def _apply_filter(parts):
            if mtype_f == '-- 전체 --':
                return parts
            return [p for p in parts
                    if mtype_f == (p.get('maintenance_type', '') or '').strip()
                    or mtype_f == (p.get('inspection_interval', '') or '').strip()]

        kw = self._search.text().strip().lower()
        def _apply_search(parts):
            if not kw:
                return parts
            return [p for p in parts
                    if kw in (p.get('part_no', '') or '').lower()
                    or kw in (p.get('name', '') or '').lower()]

        self._fill_table(self._tbl_airframe, _apply_search(_apply_filter(airframe)))
        self._fill_table(self._tbl_engine,   _apply_search(_apply_filter(engine)))
        self._fill_table(self._tbl_prop,     _apply_search(_apply_filter(propeller)))
        self._fill_table(self._tbl_trp,      _apply_search(_apply_filter(trp)))
        self._update_msb(msb_days)

    def _fill_table(self, tbl: QTableWidget, parts: list):
        # doubleClicked는 _build_ui에서 한 번만 연결 — 여기서 재연결 안 함
        tbl.setRowCount(len(parts))
        for row, p in enumerate(parts):
            qty  = p.get('qty', 0)
            safe = p.get('safe_qty', 0)
            bg   = (QColor('#f8d7da') if qty == 0 else
                    QColor('#fff3cd') if qty <= safe else
                    QColor('white'))
            cells = [
                p.get('part_no', ''), p.get('name', ''),
                str(qty), str(safe),
                p.get('maintenance_type', '') or p.get('inspection_interval', ''),
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignLeft | Qt.AlignVCenter if col in (0, 1, 4)
                    else Qt.AlignCenter
                )
                if col == 2:
                    item.setBackground(bg)
                tbl.setItem(row, col, item)

    def _on_double_click(self, tbl, index):
        item = tbl.item(index.row(), 0)
        if not item:
            return

        # 선택 행 데이터 수집
        part_data = {
            'part_no':  tbl.item(index.row(), 0).text() if tbl.item(index.row(), 0) else '',
            'name':     tbl.item(index.row(), 1).text() if tbl.item(index.row(), 1) else '',
            'qty':      tbl.item(index.row(), 2).text() if tbl.item(index.row(), 2) else '0',
            'safe_qty': tbl.item(index.row(), 3).text() if tbl.item(index.row(), 3) else '0',
            'maintenance_type': tbl.item(index.row(), 4).text() if tbl.item(index.row(), 4) else '',
        }

        from dialogs_maint import MaintScheduleDialog
        from PyQt5.QtWidgets import QDialog
        dlg = MaintScheduleDialog(item_data=part_data, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            if self._selected:
                self._on_select(self._selected)

    def _update_msb(self, days):
        while self._msb_layout.count():
            item = self._msb_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if days is None:
            lbl = QLabel('데이터 없음')
            lbl.setStyleSheet(f'color:{COLOR["muted"]}; font-size:15px;')
            self._msb_layout.addWidget(lbl)
            return

        color = ('#dc3545' if days < 150 else
                 '#fd7e14' if days < 300 else '#28a745')
        lbl = QLabel(f'{days} DAY')
        lbl.setFont(QFont('', 20, QFont.Bold))
        lbl.setStyleSheet(f'color:{color};')
        lbl.setAlignment(Qt.AlignCenter)

        status = ('⚠️ 도래 임박' if days < 150 else
                  '주의' if days < 300 else '정상')
        st_lbl = QLabel(status)
        st_lbl.setStyleSheet(f'color:{color}; font-size:14px; font-weight:bold;')
        st_lbl.setAlignment(Qt.AlignCenter)

        self._msb_layout.addWidget(lbl)
        self._msb_layout.addWidget(st_lbl)
        self._msb_layout.addStretch()

    def _on_ac_filter(self, ac_type: str):
        """기종 선택 시 좌측 기체 목록 필터링"""
        self._ac_table.setRowCount(0)
        for ac in self._ac_list:
            t = ac.get('type', '').replace(' ', '')
            if ac_type != '-- 전체 --' and t != ac_type.replace(' ', ''):
                continue
            row = self._ac_table.rowCount()
            self._ac_table.insertRow(row)
            self._ac_table.setRowHeight(row, 52)
            pct = ac.get('pct', 100)
            color = ('#dc3545' if pct < 30 else
                     '#fd7e14' if pct < 50 else COLOR['text'])
            reg_item = QTableWidgetItem(ac.get('id', ''))
            reg_item.setTextAlignment(Qt.AlignCenter)
            reg_item.setData(Qt.UserRole, ac)
            reg_item.setForeground(QColor(color))
            self._ac_table.setItem(row, 0, reg_item)
        # 선택 초기화
        self._selected = None

    def _on_filter(self):
        """정비종류 필터 적용해서 중앙 테이블 재표시"""
        if not self._selected:
            return
        self._on_select(self._selected)