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
    hdr = t.horizontalHeader()
    # 부품명칭(1)만 남은 공간 채우고, 나머지는 개별 너비 지정
    hdr.setSectionResizeMode(1, QHeaderView.Stretch)
    for c in (0, 2, 3, 4):
        hdr.setSectionResizeMode(c, QHeaderView.Interactive)
    # 컬럼: 부품번호 / 부품명칭(stretch) / 재고 수량 / 안전재고 수량 / 정비종류
    t.setColumnWidth(0, 200)   # 부품번호
    t.setColumnWidth(2, 130)   # 재고 수량
    t.setColumnWidth(3, 160)   # 안전재고 수량
    t.setColumnWidth(4, 220)   # 정비종류
    hdr.setMinimumSectionSize(100)
    # 정렬 활성화 (헤더 클릭 시 오름/내림차순)
    t.setSortingEnabled(True)
    t.setStyleSheet('font-size:20px;')
    return t


def _section_label(text):
    lbl = QLabel(text)
    lbl.setFont(QFont('', 20, QFont.Bold))
    lbl.setStyleSheet(f'color:{COLOR["primary"]}; padding:6px 0;')
    lbl.setFixedHeight(38)
    return lbl


from page_maint_schedule_io import MaintScheduleIOMixin

class MaintSchedulePage(MaintScheduleIOMixin, QWidget):
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