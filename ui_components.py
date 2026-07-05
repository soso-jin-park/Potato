"""
ui_components.py
공용 UI 컴포넌트 - DB 연동 버전
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from styles import COLOR
from inventory import inventory
from widget_parts import PartsWidget


class DataLoader(QThread):
    parts_loaded    = pyqtSignal(list)
    aircraft_loaded = pyqtSignal(list)
    error           = pyqtSignal(str, str)

    def run(self):
        from api import fetch_parts, fetch_aircraft_status
        for fn, sig, key in [
            (fetch_parts,           self.parts_loaded,    'parts'),
            (fetch_aircraft_status, self.aircraft_loaded, 'aircraft'),
        ]:
            try:
                sig.emit(fn())
            except Exception as e:
                self.error.emit(key, str(e))


class Card(QFrame):
    def __init__(self, title: str, body: QWidget,
                 refresh_slot=None, parent=None):
        super().__init__(parent)
        self.setObjectName('card')
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        hdr = QFrame()
        hdr.setObjectName('cardHeader')
        hdr.setMinimumHeight(46)
        hh = QHBoxLayout(hdr)
        hh.setContentsMargins(14, 0, 10, 0)

        lbl = QLabel(title)
        lbl.setFont(QFont('', 24, QFont.Bold))
        hh.addWidget(lbl)
        hh.addStretch()

        if refresh_slot:
            btn = QPushButton('↻')
            btn.setToolTip('새로고침')
            btn.clicked.connect(refresh_slot)
            hh.addWidget(btn)

        v.addWidget(hdr)
        v.addWidget(body)


class Sidebar(QFrame):
    page_requested = pyqtSignal(str)

    MENU = [
        ('재고 관리', [
            ('부품 관리',     'parts'),
            ('입출고 관리',   'inout'),
            ('안전재고 관리', 'safety_stock'),
        ]),
        ('항공기 관리', [
            ('기체 관리',     'aircraft'),
            ('정비 이력',     'maint_history'),
            ('주기정비 현황', 'maint_schedule'),
        ]),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('sidebar')
        self.setFixedWidth(220)

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 8, 0, 0)
        v.setSpacing(0)

        self._active_btn = None

        for category, items in self.MENU:
            cat_btn = QPushButton(f'▾  {category}')
            cat_btn.setStyleSheet(
                f'text-align:left; padding:20px 20px; font-weight:bold;'
                f'font-size:20px; color:{COLOR["primary"]};'
                f'background:transparent; border:none;'
            )
            v.addWidget(cat_btn)

            container = QWidget()
            cv = QVBoxLayout(container)
            cv.setContentsMargins(0, 0, 0, 0)
            cv.setSpacing(0)

            for label, page_id in items:
                btn = QPushButton(f'    {label}')
                btn.setStyleSheet(
                    f'text-align:left; padding:16px 16px 16px 36px;'
                    f'border:none; border-left:3px solid transparent;'
                    f'background:transparent; color:{COLOR["text"]}; font-size:21px;'
                )
                btn.clicked.connect(
                    lambda _, pid=page_id, b=btn: self._on_item(pid, b)
                )
                cv.addWidget(btn)

            v.addWidget(container)

            def make_toggle(cont, cb):
                def _toggle():
                    vis = not cont.isVisible()
                    cont.setVisible(vis)
                    t = cb.text()
                    cb.setText(
                        t.replace('▾', '▸') if not vis
                        else t.replace('▸', '▾')
                    )
                return _toggle
            cat_btn.clicked.connect(make_toggle(container, cat_btn))

        v.addStretch()

    def _on_item(self, page_id: str, btn: QPushButton):
        if self._active_btn:
            self._active_btn.setStyleSheet(
                f'text-align:left; padding:16px 16px 16px 36px;'
                f'border:none; border-left:3px solid transparent;'
                f'background:transparent; color:{COLOR["text"]}; font-size:21px;'
            )
        btn.setStyleSheet(
            f'text-align:left; padding:16px 16px 16px 36px;'
            f'border:none; border-left:3px solid {COLOR["accent"]};'
            f'background:#e8f0fb; color:{COLOR["primary"]};'
            f'font-weight:bold; font-size:22px;'
        )
        self._active_btn = btn
        self.page_requested.emit(page_id)


class DashboardLeft(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self._build_filter_bar())
        self._parts = PartsWidget()
        v.addWidget(self._parts, 1)

    def _build_filter_bar(self):
        bar = QFrame()
        bar.setStyleSheet(
            f'background:#fafbfc; border-bottom:1px solid {COLOR["border"]};'
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(10, 8, 10, 8)
        h.setSpacing(6)

        self._cat_combo = QComboBox()
        self._cat_combo.addItems(['전체', '기체', '엔진', '기타'])
        self._cat_combo.setFixedWidth(100)
        self._cat_combo.currentTextChanged.connect(self._on_cat_filter)

        self._search = QLineEdit()
        self._search.setObjectName('searchInput')
        self._search.setPlaceholderText('부품번호 / 명칭 검색')
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._on_search)
        self._search.textChanged.connect(lambda: self._debounce.start(300))

        h.addWidget(self._cat_combo)
        h.addWidget(self._search, 1)
        return bar

    def _on_cat_filter(self, val):
        # '기타' = TRP, MSB, 프로펠러 등 (기체/엔진 외 모든 카테고리)
        inventory.active_tab = val

    def _on_search(self):
        inventory.search_keyword = self._search.text().strip()

    def update_aircraft_filter(self, types: list):
        pass  # 현재 카테고리 필터로 대체

    def reset(self):
        """새로고침 시 필터/검색 초기화"""
        self._cat_combo.setCurrentIndex(0)
        self._search.clear()