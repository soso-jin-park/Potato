"""
main_window.py
메인 윈도우 진입점 — 헤더 + 사이드바 + 대시보드 조립
[Linux] 이미지 경로를 __file__ 기준 절대경로로 변경
"""
import sys
import os
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QSplitter
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon

from styles import MAIN_QSS, COLOR
from inventory import inventory
from widget_aircraft import AircraftCard
from ui_components import DataLoader, Card, Sidebar, DashboardLeft
from page_parts import PartsPage
from page_inout import InOutPage
from page_maint_history import MaintHistoryPage
from page_aircraft import AircraftPage
from page_maint_schedule import MaintSchedulePage
from page_safety_stock import SafetyStockPage

# 이 파일 위치 기준으로 리소스 경로 계산 (Linux/Windows 공통)
BASE_DIR = Path(__file__).resolve().parent


def _res(filename: str) -> str:
    """BASE_DIR 기준 절대경로 반환"""
    return str(BASE_DIR / filename)


def _build_header(win: 'MainWindow') -> QFrame:
    """헤더 바 생성 — MainWindow 인스턴스 참조 필요"""
    bar = QFrame()
    bar.setObjectName('headerBar')
    bar.setFixedHeight(110)
    h = QHBoxLayout(bar)
    h.setContentsMargins(16, 0, 16, 0)
    h.setSpacing(10)

    toggle = QPushButton('☰')
    toggle.setObjectName('headerToggle')
    toggle.setToolTip('메뉴 접기/펼치기')
    toggle.clicked.connect(
        lambda: win._sidebar.setVisible(not win._sidebar.isVisible()))
    h.addWidget(toggle)

    # 로고 (절대경로)
    logo_img = QLabel()
    logo_img.setFixedSize(190, 70)
    logo_img.setAlignment(Qt.AlignCenter)
    logo_path = _res('logo.png')
    if os.path.exists(logo_path):
        pix = QPixmap(logo_path).scaled(
            190, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_img.setPixmap(pix)
    else:
        logo_img.setStyleSheet(
            f'border:1px solid {COLOR["border"]}; border-radius:4px;'
            f'background:#e8eef5; color:{COLOR["muted"]}; font-size:9px;')
        logo_img.setText('LOGO')
    h.addWidget(logo_img)

    school_lbl = QLabel('| 비행교육원')
    school_lbl.setFont(QFont('', 30, QFont.Bold))
    school_lbl.setStyleSheet(
        f'color:{COLOR["primary"]}; background:transparent;')
    h.addWidget(school_lbl)
    h.addStretch()

    win._breadcrumb = QLabel('메인화면')
    win._breadcrumb.setStyleSheet(f'color:{COLOR["muted"]}; font-size:22px;')
    h.addWidget(win._breadcrumb)

    btn_reload = QPushButton('↺')
    btn_reload.setObjectName('headerIconBtn')
    btn_reload.setToolTip('새로고침')
    btn_reload.setFont(QFont('', 24))
    btn_reload.clicked.connect(win._reload_all)
    h.addWidget(btn_reload)

    # 홈 버튼 (절대경로)
    btn_home = QPushButton()
    btn_home.setObjectName('headerIconBtn')
    btn_home.setToolTip('홈')
    btn_home.setFixedSize(44, 44)
    btn_home.clicked.connect(lambda: win._stack.setCurrentIndex(0))
    home_path = _res('home.png')
    if os.path.exists(home_path):
        btn_home.setIcon(QIcon(QPixmap(home_path).scaled(
            22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        btn_home.setIconSize(btn_home.size())
    else:
        btn_home.setFont(QFont('', 24))
        btn_home.setText('🏠')
    h.addWidget(btn_home)

    return bar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('비행교육원 MRO 시스템')
        self.resize(1440, 900)
        self.setStyleSheet(MAIN_QSS)
        self._all_parts = []

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(_build_header(self))

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.page_requested.connect(self._on_page)
        body.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_dashboard())  # 0
        self._stack.addWidget(PartsPage())              # 1
        self._stack.addWidget(InOutPage())              # 2
        self._stack.addWidget(SafetyStockPage())        # 3
        self._stack.addWidget(AircraftPage())           # 4
        self._stack.addWidget(MaintHistoryPage())       # 5
        self._stack.addWidget(MaintSchedulePage())      # 6
        self._page_idx = {
            'dashboard': 0, 'parts': 1, 'inout': 2,
            'safety_stock': 3, 'aircraft': 4,
            'maint_history': 5, 'maint_schedule': 6,
        }
        body.addWidget(self._stack, 1)
        root.addLayout(body, 1)

    def _build_dashboard(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)
        splitter.setStyleSheet(
            'QSplitter::handle{background:#d0d7e2;border-radius:2px;margin:2px;}'
            'QSplitter::handle:hover{background:#4a90d9;}')

        self._dash_left = DashboardLeft()
        left_card = Card('부품 재고 현황', self._dash_left)
        left_card.setMinimumWidth(600)
        splitter.addWidget(left_card)

        self._aircraft_card = AircraftCard()
        ac_wrap = Card('항공기 주기정비 현황', self._aircraft_card)
        ac_wrap.setMinimumWidth(420)
        splitter.addWidget(ac_wrap)

        splitter.setSizes([900, 500])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        outer.addWidget(splitter)
        return page

    def _load_data(self):
        if hasattr(self, '_loader') and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()
        self._loader = DataLoader()
        self._loader.parts_loaded.connect(self._on_parts)
        self._loader.aircraft_loaded.connect(self._on_aircraft)
        self._loader.error.connect(
            lambda k, m: print(f'[{k}] 로드 실패: {m}'))
        self._loader.start()

    def _on_parts(self, parts):
        print(f"✅ [Main] 부품 {len(parts)}개 수신")
        self._all_parts = parts
        inventory.parts = parts
        self._dash_left.update_aircraft_filter(inventory.get_aircraft_types())
        parts_page = self._stack.widget(1)
        if parts_page and hasattr(parts_page, '_load'):
            parts_page._load()
        cur_idx = self._stack.currentIndex()
        if cur_idx not in (0, 1):
            cur_page = self._stack.widget(cur_idx)
            if cur_page:
                if hasattr(cur_page, '_load'):
                    cur_page._load()
                elif hasattr(cur_page, '_refresh'):
                    cur_page._refresh()

    def _on_aircraft(self, aircraft_list):
        print(f"✅ [Main] 항공기 {len(aircraft_list)}개 수신")
        inventory.aircraft_list = aircraft_list
        self._aircraft_card.load_list(aircraft_list)
        try:
            self._aircraft_card._list_view.aircraft_selected.disconnect(
                self._on_aircraft_selected)
            self._aircraft_card.aircraft_back.disconnect(self._on_aircraft_back)
        except Exception:
            pass
        self._aircraft_card._list_view.aircraft_selected.connect(
            self._on_aircraft_selected)
        self._aircraft_card.aircraft_back.connect(self._on_aircraft_back)
        self._dash_left.update_aircraft_filter(inventory.get_aircraft_types())
        parts_page = self._stack.widget(1)
        if parts_page and hasattr(parts_page, '_load'):
            parts_page._load()

    def _on_aircraft_selected(self, aircraft_id: str):
        from api import fetch_bom_parts
        try:
            ac = next(
                (a for a in inventory.aircraft_list
                 if a.get('id') == aircraft_id), None)
            if not ac:
                return
            self._dash_left.reset()
            bom_parts = fetch_bom_parts(ac.get('type', '').replace(' ', ''))
            if bom_parts:
                inventory.parts = bom_parts
        except Exception as e:
            print(f"❌ [Main] BOM 연동 실패: {e}")

    def _on_aircraft_back(self):
        self._dash_left.reset()
        if self._all_parts:
            inventory.parts = self._all_parts
        else:
            self._load_data()

    def _reload_all(self):
        cur_idx = self._stack.currentIndex()
        if cur_idx == 0:
            self._aircraft_card._detail_view.setVisible(False)
            self._aircraft_card._list_view.setVisible(True)
            self._aircraft_card.setSizes([self._aircraft_card.height(), 0])
            self._dash_left.reset()
            if self._all_parts:
                inventory.parts = self._all_parts
        else:
            cur_page = self._stack.widget(cur_idx)
            if cur_page and hasattr(cur_page, 'reset'):
                cur_page.reset()
        self._load_data()

    def _on_page(self, page_id: str):
        self._stack.setCurrentIndex(self._page_idx.get(page_id, 0))
        labels = {
            'dashboard': '메인화면',
            'parts': '재고관리 > 부품관리',
            'inout': '재고관리 > 입출고관리',
            'safety_stock': '재고관리 > 안전재고관리',
            'aircraft': '항공기관리 > 기체관리',
            'maint_history': '항공기관리 > 정비이력',
            'maint_schedule': '항공기관리 > 주기정비현황',
        }
        self._breadcrumb.setText(labels.get(page_id, ''))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.showMaximized()
    QTimer.singleShot(100, win._load_data)
    sys.exit(app.exec_())
