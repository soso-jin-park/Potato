# inventory.py
"""
inventory.py
전역 상태 관리 (실제 Supabase DB 스키마 구조 연동 완료)
"""
from PyQt5.QtCore import QObject, pyqtSignal


class InventoryState(QObject):
    # 상태 변경 시그널
    parts_changed      = pyqtSignal(list)
    aircraft_changed   = pyqtSignal(list)
    alarms_changed     = pyqtSignal(list)
    selection_changed  = pyqtSignal(object)   # None or dict
    filter_changed     = pyqtSignal()          # 탭/필터/검색 변경 시 재렌더 트리거
    stock_updated      = pyqtSignal()          # 입출고 등 실제 재고 변동 시

    def __init__(self):
        super().__init__()

        self._parts            = []
        self._aircraft_list    = []
        self._alarms           = []
        self._selected_aircraft = None

        self._active_tab       = '전체'     # 기본 탭 필터 (기체 테이블에 없거나 공통인 경우 고려 전체로 기본값 수정)
        self._filter_aircraft  = '전체'    # 기체 필터
        self._search_keyword   = ''        # 검색어
        self._sort_key         = None      # 'part_number'|'name'|'quantity'|'safety_stock'|'location'
        self._sort_dir         = 'asc'     # 'asc'|'desc'

    # ── getter / setter ──────────────────────────────────────────
    @property
    def parts(self): return self._parts

    @parts.setter
    def parts(self, val):
        self._parts = val
        self.parts_changed.emit(val)

    @property
    def aircraft_list(self): return self._aircraft_list

    @aircraft_list.setter
    def aircraft_list(self, val):
        self._aircraft_list = val
        self.aircraft_changed.emit(val)

    @property
    def alarms(self): return self._alarms

    @alarms.setter
    def alarms(self, val):
        self._alarms = val
        self.alarms_changed.emit(val)

    @property
    def selected_aircraft(self): return self._selected_aircraft

    @selected_aircraft.setter
    def selected_aircraft(self, val):
        self._selected_aircraft = val
        self.selection_changed.emit(val)
        self.filter_changed.emit()

    @property
    def active_tab(self): return self._active_tab

    @active_tab.setter
    def active_tab(self, val):
        self._active_tab = val
        self.filter_changed.emit()

    @property
    def filter_aircraft(self): return self._filter_aircraft

    @filter_aircraft.setter
    def filter_aircraft(self, val):
        self._filter_aircraft = val
        self.filter_changed.emit()

    @property
    def search_keyword(self): return self._search_keyword

    @search_keyword.setter
    def search_keyword(self, val):
        self._search_keyword = val
        self.filter_changed.emit()

    @property
    def sort_key(self): return self._sort_key

    @sort_key.setter
    def sort_key(self, val):
        self._sort_key = val
        self.filter_changed.emit()

    @property
    def sort_dir(self): return self._sort_dir

    @sort_dir.setter
    def sort_dir(self, val):
        self._sort_dir = val
        self.filter_changed.emit()

    # ── 필터링된 부품 목록 ────────────────────────────────────────
    def get_filtered_parts(self) -> list:
        result = list(self._parts)

        # 1. 탭 필터
        if self._active_tab == '기타':
            # 기타 = TRP, MSB, 프로펠러 등 (기체/엔진 외 모든 카테고리)
            result = [p for p in result
                      if p.get('category', '') not in ('기체', '엔진')]
        elif self._active_tab != '전체':
            result = [p for p in result if p.get('category') == self._active_tab]

        # 2. 기체 콤보박스 필터 (Supabase 구조인 aircraft_type에 대응)
        if self._filter_aircraft != '전체':
            result = [p for p in result
                      if self._filter_aircraft == p.get('aircraft_type', '') or p.get('aircraft_type') == '공통']

        # 3. 선택된 항공기 필터 - 대시보드에서는 필터 안 함 (BOM은 별도 표시)
        # selected_aircraft 변경 시 filter_changed 시그널만 발생, 필터링은 하지 않음

        # 4. 검색어 필터 (실제 DB 컬럼명인 part_number로 변경)
        if self._search_keyword:
            kw = self._search_keyword.lower()
            result = [p for p in result
                      if kw in p.get('part_number', '').lower()
                      or kw in p.get('name', '').lower()
                      or kw in p.get('location', '').lower()]

        # 5. 정렬 정밀화
        if self._sort_key:
            reverse = (self._sort_dir == 'desc')
            result.sort(
                key=lambda p: (p.get(self._sort_key) if p.get(self._sort_key) is not None else ''),
                reverse=reverse
            )

        return result

    # ── 기체 타입 목록 ────────────────────────────────────────────
    def get_aircraft_types(self) -> list:
        # ✅ Supabase 실제 컬럼명인 'category' (DA-40 NG 등)를 추출하도록 수정
        types = list(dict.fromkeys(a['category'] for a in self._aircraft_list if a.get('category')))
        return ['전체'] + types

    # ── 정렬 토글 ─────────────────────────────────────────────────
    def toggle_sort(self, key: str):
        if self._sort_key == key:
            self._sort_dir = 'desc' if self._sort_dir == 'asc' else 'asc'
        else:
            self._sort_key = key
            self._sort_dir = 'asc'
        self.filter_changed.emit()


# 싱글턴 인스턴스
inventory = InventoryState()