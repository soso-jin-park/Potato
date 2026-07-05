"""
main_window.py
메인 윈도우 진입점
헤더 + 사이드바 + 대시보드 조립
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSizePolicy, QStackedWidget, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('비행교육원 MRO 시스템')
        self.resize(1440, 900)
        self.setStyleSheet(MAIN_QSS)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.page_requested.connect(self._on_page)
        body.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_dashboard())  # idx 0
        self._stack.addWidget(PartsPage())              # idx 1  parts
        self._stack.addWidget(InOutPage())              # idx 2  inout
        self._stack.addWidget(SafetyStockPage())        # idx 3  safety_stock
        self._stack.addWidget(AircraftPage())            # idx 4  aircraft
        self._stack.addWidget(MaintHistoryPage())       # idx 5  maint_history
        self._stack.addWidget(MaintSchedulePage())      # idx 6  maint_schedule
        self._page_idx = {
            'dashboard':      0,
            'parts':          1,
            'inout':          2,
            'safety_stock':   3,
            'aircraft':       4,
            'maint_history':  5,
            'maint_schedule': 6,
        }
        body.addWidget(self._stack, 1)

        root.addLayout(body, 1)
        self._all_parts = []  # 전체 부품 캐시
        self._load_data()

    # ── 헤더 ─────────────────────────────────────────────────────
    def _build_header(self):
        bar = QFrame()
        bar.setObjectName('headerBar')
        bar.setFixedHeight(110)
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(10)

        # 사이드바 토글
        toggle = QPushButton('☰')
        toggle.setObjectName('headerToggle')
        toggle.setToolTip('메뉴 접기/펼치기')
        toggle.clicked.connect(
            lambda: self._sidebar.setVisible(not self._sidebar.isVisible())
        )
        h.addWidget(toggle)

        # 로고 이미지 (비율 유지하며 축소)
        logo_img = QLabel()
        logo_img.setFixedSize(190, 70)
        logo_img.setAlignment(Qt.AlignCenter)
        logo_path = 'logo.png'   # ← 로고 파일명 (같은 폴더에 위치)
        import os
        if os.path.exists(logo_path):
            from PyQt5.QtGui import QPixmap
            pix = QPixmap(logo_path).scaled(
                190, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_img.setPixmap(pix)
        else:
            logo_img.setStyleSheet(
                f'border:1px solid {COLOR["border"]}; border-radius:4px;'
                f'background:#e8eef5; color:{COLOR["muted"]}; font-size:9px;'
            )
            logo_img.setText('LOGO')
        h.addWidget(logo_img)

        # 텍스트: | 비행교육원
        school_lbl = QLabel('| 비행교육원')
        school_lbl.setFont(QFont('', 30, QFont.Bold))
        school_lbl.setStyleSheet(f'color:{COLOR["primary"]}; background:transparent;')
        h.addWidget(school_lbl)

        h.addStretch()

        # 브레드크럼
        self._breadcrumb = QLabel('메인화면')
        self._breadcrumb.setStyleSheet(
            f'color:{COLOR["muted"]}; font-size:22px;'
        )
        h.addWidget(self._breadcrumb)

        # 새로고침 버튼
        btn_reload = QPushButton('↺')
        btn_reload.setObjectName('headerIconBtn')
        btn_reload.setToolTip('새로고침')
        btn_reload.setFont(QFont('', 24))
        btn_reload.clicked.connect(self._reload_all)
        h.addWidget(btn_reload)

        # 홈 버튼 (이미지 파일 있으면 아이콘, 없으면 텍스트)
        btn_home = QPushButton()
        btn_home.setObjectName('headerIconBtn')
        btn_home.setToolTip('홈')
        btn_home.setFixedSize(44, 44)
        btn_home.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        home_path = 'home.png'
        if os.path.exists(home_path):
            from PyQt5.QtGui import QPixmap, QIcon
            btn_home.setIcon(QIcon(QPixmap(home_path).scaled(
                22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )))
            btn_home.setIconSize(btn_home.size())
            btn_home.setText('')
        else:
            btn_home.setFont(QFont('', 24))
            btn_home.setText('🏠')
        h.addWidget(btn_home)

        return bar

    # ── 대시보드 ─────────────────────────────────────────────────
    def _build_dashboard(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#d0d7e2; border-radius:2px; margin:2px; }
            QSplitter::handle:hover { background:#4a90d9; }
        """)

        # 왼쪽: 필터 + 부품 테이블
        self._dash_left = DashboardLeft()
        left_card = Card('부품 재고 현황', self._dash_left)
        left_card.setMinimumWidth(600)
        splitter.addWidget(left_card)

        # 오른쪽: 항공기 카드 (목록 위 / 상세 아래 — 클릭 시 펼침)
        self._aircraft_card = AircraftCard()
        ac_wrap = Card('항공기 주기정비 현황', self._aircraft_card)
        ac_wrap.setMinimumWidth(420)
        splitter.addWidget(ac_wrap)

        splitter.setSizes([900, 500])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        outer.addWidget(splitter)
        return page

    # ── 데이터 로드 ──────────────────────────────────────────────
    def _load_data(self):
        # 이전 스레드가 실행 중이면 완료될 때까지 대기
        if hasattr(self, '_loader') and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()
        self._loader = DataLoader()
        self._loader.parts_loaded.connect(self._on_parts)
        self._loader.aircraft_loaded.connect(self._on_aircraft)
        self._loader.error.connect(
            lambda k, m: print(f'[{k}] 로드 실패: {m}')
        )
        self._loader.start()

    def _on_parts(self, parts):
        print(f"✅ [Main] 부품 데이터 수신 성공! 개수: {len(parts)}개")
        self._all_parts = parts
        inventory.parts = parts
        self._dash_left.update_aircraft_filter(inventory.get_aircraft_types())

        # 부품관리 페이지(idx 1)는 항상 갱신 (백그라운드 동기화)
        parts_page = self._stack.widget(1)
        if parts_page and hasattr(parts_page, '_load'):
            parts_page._load()

        # 현재 보이는 페이지가 따로 있으면 추가 갱신
        cur_idx = self._stack.currentIndex()
        if cur_idx not in (0, 1):   # 대시보드·부품관리는 위에서 처리됨
            cur_page = self._stack.widget(cur_idx)
            if cur_page:
                if hasattr(cur_page, '_load'):
                    cur_page._load()
                elif hasattr(cur_page, '_refresh'):
                    cur_page._refresh()
                print(f"🔊 [Main] 현재 페이지(idx={cur_idx}) 리렌더링 완료.")

    def _on_aircraft(self, aircraft_list):
        print(f"✅ [Main] 항공기 데이터 수신 성공! 개수: {len(aircraft_list)}개")
        inventory.aircraft_list = aircraft_list
        self._aircraft_card.load_list(aircraft_list)
        # 기체 선택/뒤로가기 시그널 - 중복 연결 방지
        try:
            self._aircraft_card._list_view.aircraft_selected.disconnect(self._on_aircraft_selected)
            self._aircraft_card.aircraft_back.disconnect(self._on_aircraft_back)
        except Exception:
            pass
        self._aircraft_card._list_view.aircraft_selected.connect(self._on_aircraft_selected)
        self._aircraft_card.aircraft_back.connect(self._on_aircraft_back)
        self._dash_left.update_aircraft_filter(inventory.get_aircraft_types())
        parts_page_widget = self._stack.widget(1)
        if parts_page_widget and hasattr(parts_page_widget, '_load'):
            parts_page_widget._load()

    def _on_aircraft_selected(self, aircraft_id: str):
        """기체 선택 시 해당 기종 BOM 부품을 좌측 테이블에 표시"""
        from api import fetch_bom_parts
        try:
            ac = next(
                (a for a in inventory.aircraft_list if a.get('id') == aircraft_id), None
            )
            if not ac:
                return

            # 좌측 필터/검색 초기화 (BOM 부품 전체 표시)
            self._dash_left.reset()

            # DB 기종명 변환: 'DA-40 NG' → 'DA-40NG', 'DA-42 NG' → 'DA-42NG'
            ac_type = ac.get('type', '').replace(' ', '')
            bom_parts = fetch_bom_parts(ac_type)

            if bom_parts:
                inventory.parts = bom_parts
                print(f"✅ [Main] {aircraft_id}({ac_type}) BOM 부품 {len(bom_parts)}개 표시")
            else:
                print(f"⚠️ [Main] {ac_type} BOM 데이터 없음 - 전체 부품 유지")
        except Exception as e:
            print(f"❌ [Main] BOM 연동 실패: {e}")

    def _on_aircraft_back(self):
        """기체 상세 뒤로가기 시 전체 부품 복원 + 필터 초기화"""
        self._dash_left.reset()
        if self._all_parts:
            inventory.parts = self._all_parts
        else:
            self._load_data()

    def _reload_all(self):
        """새로고침: 현재 페이지 필터 초기화 + 처음 화면 + 데이터 재로드
        대시보드(0)도 항상 같이 갱신됨 (_load_data → _on_parts/aircraft 콜백)
        """
        cur_idx = self._stack.currentIndex()

        # ── 대시보드(0): 기체 선택 해제 + 필터 초기화 ──
        if cur_idx == 0:
            self._aircraft_card._detail_view.setVisible(False)
            self._aircraft_card._list_view.setVisible(True)
            self._aircraft_card.setSizes([self._aircraft_card.height(), 0])
            self._dash_left.reset()
            if self._all_parts:
                inventory.parts = self._all_parts

        # ── 그 외 페이지: reset() → 필터/정렬 초기화 + _load() 호출 ──
        else:
            cur_page = self._stack.widget(cur_idx)
            if cur_page and hasattr(cur_page, 'reset'):
                cur_page.reset()
                print(f"🔊 [Main] 페이지(idx={cur_idx}) reset 완료.")

        # ── 백그라운드: 부품·항공기 전체 데이터 재로드 → 대시보드도 갱신 ──
        self._load_data()

    def _reload_aircraft(self):
        from api import fetch_aircraft_status
        try:
            self._on_aircraft(fetch_aircraft_status())
        except Exception as e:
            print(f'항공기 새로고침 실패: {e}')

    def _on_page(self, page_id: str):
        idx = self._page_idx.get(page_id, 0)
        self._stack.setCurrentIndex(idx)
        breadcrumb_map = {
            'dashboard':      '메인화면',
            'parts':          '재고관리 > 부품관리',
            'inout':          '재고관리 > 입출고관리',
            'safety_stock':   '재고관리 > 안전재고관리',
            'aircraft':       '항공기관리 > 기체관리',
            'maint_history':  '항공기관리 > 정비이력',
            'maint_schedule': '항공기관리 > 주기정비현황',
        }
        self._breadcrumb.setText(breadcrumb_map.get(page_id, ''))


# main_window.py 파일의 가장 최하단 진입점 부분

if __name__ == '__main__':
    from PyQt5.QtCore import QTimer  # 👈 미세 시차 처리를 위해 상단이나 여기에 임포트 추가
    
    app = QApplication(sys.argv)
    
    # 1. 메인 윈도우 객체 생성
    win = MainWindow()
    
    # 2. 전체화면으로 시작
    win.showMaximized()
    print("🔊 [Main] 비행교육원 MRO 시스템 GUI 창 강제 팝업 완료.")
    
    # 3. 0.1초(100ms) 뒤에 Supabase 데이터를 읽어오는 쓰레드를 실행합니다.
    #    창이 온전히 다 켜진 후 쓰레드가 돌기 때문에 무한 대기 현상 없이 창이 무조건 열립니다.
    QTimer.singleShot(100, win._load_data)
    
    sys.exit(app.exec_())