"""
page_maint_schedule_io.py
MaintSchedulePage 로직 믹스인 — load / select / fill / filter
"""
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QDialog, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from api import fetch_aircraft_status, fetch_bom_parts
from styles import COLOR


class MaintScheduleIOMixin:
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