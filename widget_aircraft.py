"""
widget_aircraft.py - 와이어프레임(img_08) 기준
- back_clicked 중복 연결 문제 완전 해결
- DetailView를 한 번만 생성, load()로 내용만 갱신
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from inventory import inventory
from styles import COLOR


def _bar_color(pct):
    if pct >= 50: return '#28a745'
    if pct >= 30: return '#fd7e14'
    return '#dc3545'


# ── 기체 행 ───────────────────────────────────────────────────────
class AircraftRow(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, ac: dict, parent=None):
        super().__init__(parent)
        self._ac_id = ac.get('id', '')
        self.setCursor(Qt.PointingHandCursor)
        self._ns = 'border-bottom:1px solid #eee; background:white;'
        self._hs = 'border-bottom:1px solid #eee; background:#eef3fb;'
        self.setStyleSheet(self._ns)

        pct         = ac.get('pct', 0)
        next_insp   = ac.get('next_inspection', 0)
        cycle_hours = max(ac.get('cycle_hours', 100), 1)
        color       = _bar_color(pct)

        v = QVBoxLayout(self)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(3)

        row = QHBoxLayout()
        row.setSpacing(6)

        icon = QLabel('✈')
        icon.setStyleSheet('font-size:13px; color:#555; border:none; background:transparent;')
        icon.setFixedWidth(16)

        id_lbl = QLabel(self._ac_id)
        id_lbl.setFont(QFont('', 14, QFont.Bold))
        c = COLOR['red'] if pct < 30 else COLOR['orange'] if pct < 50 else COLOR['text']
        id_lbl.setStyleSheet(f'color:{c}; border:none; background:transparent;')

        hrs_lbl = QLabel(f'{next_insp:.0f} H')
        hrs_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hrs_lbl.setStyleSheet(
            f'color:{color}; font-size:13px; font-weight:bold;'
            f'border:none; background:transparent;'
        )

        row.addWidget(icon)
        row.addWidget(id_lbl)
        row.addStretch()
        row.addWidget(hrs_lbl)
        v.addLayout(row)

        bar_bg = QFrame()
        bar_bg.setFixedHeight(8)
        bar_bg.setStyleSheet('background:#e0e0e0; border-radius:3px; border:none;')
        bar_bg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        fill_w = QFrame(bar_bg)
        fill_w.setFixedHeight(8)
        fill_w.setStyleSheet(f'background:{color}; border-radius:3px; border:none;')
        fill_w._pct = min(int(next_insp / cycle_hours * 100), 100)

        def make_resize(bg, fill):
            def resizeEvent(e):
                fill.setFixedWidth(max(int(bg.width() * fill._pct / 100), 4))
            return resizeEvent
        bar_bg.resizeEvent = make_resize(bar_bg, fill_w)
        v.addWidget(bar_bg)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self._ac_id)

    def enterEvent(self, e):
        self.setStyleSheet(self._hs)

    def leaveEvent(self, e):
        self.setStyleSheet(self._ns)


# ── 기체 목록 뷰 ──────────────────────────────────────────────────
class AircraftListView(QScrollArea):
    aircraft_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch()
        self.setWidget(self._container)

    def load(self, aircraft_list: list):
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        for ac in aircraft_list:
            row = AircraftRow(ac)
            row.clicked.connect(self.aircraft_selected)
            self._layout.insertWidget(self._layout.count() - 1, row)


# ── 기체 상세 뷰 ─────────────────────────────────────────────────
# 핵심: 위젯을 매번 삭제/생성하지 않고 한 번만 생성 후 내용만 갱신
class AircraftDetailView(QScrollArea):
    back_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

        self._container = QWidget()
        self._root = QVBoxLayout(self._container)
        self._root.setContentsMargins(10, 10, 10, 10)
        self._root.setSpacing(6)
        self._root.setAlignment(Qt.AlignTop)
        self.setWidget(self._container)

        # ── 고정 위젯들 (한 번만 생성) ──
        # 헤더
        hdr_w = QWidget()
        hdr_w.setObjectName('detailHdr')
        hdr_w.setFixedHeight(44)
        hdr_w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hdr_w.setStyleSheet('QWidget#detailHdr { background:transparent; border:none; }'
                            'QWidget#detailHdr QLabel { background:transparent; border:none; padding:0; margin:0; }')
        hdr = QHBoxLayout(hdr_w)
        hdr.setContentsMargins(0, 0, 0, 0)
        hdr.setSpacing(6)

        self._id_lbl = QLabel()
        self._id_lbl.setFont(QFont('', 17, QFont.Bold))
        self._id_lbl.setStyleSheet(f'color:{COLOR["primary"]};')

        self._type_badge = QLabel()
        self._type_badge.setFixedHeight(28)
        self._type_badge.setStyleSheet(
            f'color:white; background:{COLOR["secondary"]};'
            f'border-radius:3px; padding:2px 8px; font-size:14px; font-weight:bold; border:none;'
        )

        tab_eng = QPushButton('엔진')
        tab_eng.setFixedHeight(28)
        tab_eng.setStyleSheet(
            f'background:#e8eef5; color:{COLOR["primary"]}; border:1px solid {COLOR["border"]};'
            f'border-radius:3px; padding:0px 10px; font-size:14px;'
        )

        # 뒤로가기 버튼 - 한 번만 연결
        self._btn_back = QPushButton('↩')
        self._btn_back.setObjectName('btnBack')
        self._btn_back.setFixedSize(34, 34)
        self._btn_back.setToolTip('목록으로')
        self._btn_back.clicked.connect(self.back_clicked)  # 한 번만 연결

        hdr.addWidget(self._id_lbl)
        hdr.addWidget(self._type_badge)
        hdr.addWidget(tab_eng)
        hdr.addStretch()
        hdr.addWidget(self._btn_back)
        self._root.addWidget(hdr_w)

        # 주기 정비까지 남은 시간
        self._time_row = self._make_info_row()
        self._root.addWidget(self._time_row['widget'])

        # 기체 누적 비행시간
        self._hrs_row = self._make_info_row()
        self._root.addWidget(self._hrs_row['widget'])

        # 재고 부족 부품 섹션 타이틀
        self._short_title = self._make_section_label('재고 부족 부품')
        self._root.addWidget(self._short_title)

        # 재고 부족 부품 테이블 (가변 높이)
        self._shortage_tbl = QTableWidget()
        self._shortage_tbl.setColumnCount(4)
        self._shortage_tbl.setHorizontalHeaderLabels(['부품번호', '부품명칭', '재고', '위치'])
        self._shortage_tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self._shortage_tbl.verticalHeader().setVisible(False)
        self._shortage_tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._shortage_tbl.setStyleSheet('font-size:15px;')
        self._root.addWidget(self._shortage_tbl)

        # 부족 없음 라벨
        self._ok_lbl = QWidget()
        self._ok_lbl.setObjectName('okBox')
        self._ok_lbl.setFixedHeight(40)
        self._ok_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._ok_lbl.setStyleSheet(
            '#okBox { background:#d4edda; border-radius:4px; }'
            '#okBox QLabel { background:transparent; border:none; font-size:16px; padding:0; margin:0; color:#155724; }'
        )
        ok_h = QHBoxLayout(self._ok_lbl)
        ok_h.setContentsMargins(12, 0, 12, 0)
        ok_h.addWidget(QLabel('✅ 부족 부품 없음'))
        self._root.addWidget(self._ok_lbl)

        # 다음 주기 정비
        self._next_title = self._make_section_label('다음 주기 정비')
        self._root.addWidget(self._next_title)

        self._sched_rows = []
        for _ in range(3):  # 기체 / 엔진 / MSB
            r = self._make_info_row()
            self._root.addWidget(r['widget'])
            self._sched_rows.append(r)

        self._root.addStretch()

    def _make_info_row(self):
        w = QWidget()
        w.setObjectName('infoRow')
        w.setFixedHeight(40)
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        w.setStyleSheet(
            '#infoRow { background:#f0f4f8; border:1px solid ' + COLOR["border"] + '; border-radius:4px; }'
            '#infoRow QLabel { background:transparent; border:none; font-size:16px; padding:0; margin:0; }'
        )
        h = QHBoxLayout(w)
        h.setContentsMargins(10, 0, 10, 0)
        h.setSpacing(6)
        left  = QLabel()
        right = QLabel()
        right.setFont(QFont('', 16, QFont.Bold))
        right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h.addWidget(left)
        h.addStretch()
        h.addWidget(right)
        return {'widget': w, 'left': left, 'right': right}

    def _make_section_label(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont('', 16, QFont.Bold))
        lbl.setFixedHeight(32)
        lbl.setStyleSheet(
            f'color:{COLOR["primary"]}; background:transparent; border:none; padding:0; margin:0;'
        )
        return lbl

    def load(self, ac: dict):
        """위젯 삭제/생성 없이 텍스트/색상만 업데이트"""
        pct   = ac.get('pct', 0)
        color = _bar_color(pct)

        # 헤더
        self._id_lbl.setText(ac.get('id', ''))
        self._type_badge.setText(ac.get('type', ''))

        # 주기 정비까지 남은 시간
        next_insp = ac.get('next_inspection', 0)
        self._time_row['left'].setText('주기 정비까지 남은 시간 :')
        self._time_row['right'].setText(f'{next_insp:.0f} H')
        self._time_row['right'].setStyleSheet(
            f'color:{color}; background:transparent; border:none; font-size:16px; padding:0; margin:0;'
        )

        # 누적 비행시간
        total = ac.get('total_hours', 0)
        self._hrs_row['left'].setText('기체 누적 비행시간 :')
        self._hrs_row['right'].setText(f'{total:,.1f} H')
        self._hrs_row['right'].setStyleSheet(
            f'color:{COLOR["primary"]}; background:transparent; border:none; font-size:16px; padding:0; margin:0;'
        )

        # 재고 부족 부품
        shortage = ac.get('stock_shortage', [])
        if shortage:
            self._shortage_tbl.setVisible(True)
            self._ok_lbl.setVisible(False)
            self._shortage_tbl.setRowCount(len(shortage))
            self._shortage_tbl.setFixedHeight(36 + 34 * len(shortage) + 4)
            for r, s in enumerate(shortage):
                qty = s.get('qty', 0)
                for c, val in enumerate([
                    str(s.get('part_id', '')), '', str(qty), '-'
                ]):
                    it = QTableWidgetItem(val)
                    it.setTextAlignment(Qt.AlignCenter)
                    if c == 2:
                        it.setBackground(QColor('#f8d7da' if qty == 0 else '#fff3cd'))
                        it.setForeground(QColor('#721c24' if qty == 0 else '#856404'))
                    self._shortage_tbl.setItem(r, c, it)
        else:
            self._shortage_tbl.setVisible(False)
            self._ok_lbl.setVisible(True)

        # 다음 주기 정비
        schedules = ac.get('schedules', [])
        sched_vals = [
            f"{s.get('hours', 0):.0f}/{s.get('cycle', 100):.0f}H"
            for s in schedules[:2]
        ]
        msb = ac.get('msb_remaining')
        msb_color = (
            '#dc3545' if msb is not None and msb < 150 else
            '#fd7e14' if msb is not None and msb < 300 else
            COLOR['primary']
        )

        row_data = [
            ('기체 :', sched_vals[0] if len(sched_vals) > 0 else '-', COLOR['primary']),
            ('엔진 :', sched_vals[1] if len(sched_vals) > 1 else '-', COLOR['primary']),
            ('MSB 잔여 상태 (도래 여부) :', f'{msb}DAY' if msb is not None else '-', msb_color),
        ]
        for i, (left, right, vc) in enumerate(row_data):
            self._sched_rows[i]['left'].setText(left)
            self._sched_rows[i]['right'].setText(right)
            self._sched_rows[i]['right'].setStyleSheet(
                f'color:{vc}; background:transparent; border:none; font-size:16px; padding:0; margin:0;'
            )
            self._sched_rows[i]['widget'].setVisible(True)


# ── AircraftCard: 목록 + 상세 스플리터 ──────────────────────────
class AircraftCard(QSplitter):
    aircraft_back = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(Qt.Vertical, parent)
        self.setHandleWidth(4)
        self.setStyleSheet("""
            QSplitter::handle { background:#d0d7e2; border-radius:2px; }
            QSplitter::handle:hover { background:#4a90d9; }
        """)

        self._list_view   = AircraftListView()
        self._detail_view = AircraftDetailView()
        self._detail_view.setVisible(False)

        self.addWidget(self._list_view)
        self.addWidget(self._detail_view)
        self.setStretchFactor(0, 1)
        self.setStretchFactor(1, 0)

        # 시그널 연결 - 각 한 번씩만
        self._list_view.aircraft_selected.connect(self._on_select)
        self._detail_view.back_clicked.connect(self._on_back)

    def load_list(self, aircraft_list: list):
        self._list_view.load(aircraft_list)

    def _on_select(self, aircraft_id: str):
        from api import fetch_aircraft_detail
        try:
            ac = fetch_aircraft_detail(aircraft_id)
            if ac:
                self._detail_view.load(ac)
                self._detail_view.setVisible(True)
                total = self.height()
                self.setSizes([int(total * 0.42), int(total * 0.58)])
        except Exception as e:
            print(f'❌ [AircraftCard] 상세 로드 실패: {e}')

    def _on_back(self):
        self._detail_view.setVisible(False)
        self._list_view.setVisible(True)
        self.setSizes([self.height(), 0])
        self.aircraft_back.emit()