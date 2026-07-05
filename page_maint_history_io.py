"""
page_maint_history_io.py
정비 이력 페이지 - 테이블 채우기 / 행 선택 믹스인
"""
import re
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import Qt

ROW_H = 52


def _extract_cycle(maint_type, interval=''):
    """정비종류에서 주기 추출: '항공기 100 HRS' → '100H'"""
    # interval에 값이 있으면 우선 사용
    if interval and interval != '-':
        m = re.search(r'(\d+)', interval)
        if m:
            return f"{m.group(1)}H"
        return interval
    # 정비종류에서 숫자 추출
    if maint_type:
        m = re.search(r'(\d+)\s*(?:HRS?|H|시간)', maint_type, re.IGNORECASE)
        if m:
            return f"{m.group(1)}H"
    return '-'


class MaintHistoryIOMixin:
    """page_maint_history.MaintHistoryPage 에서 상속받아 사용"""

    # ── 정기 정비 테이블 채우기 ─────────────────────────────
    def _fill_reg(self, data):
        KEYS = ['', 'aircraft_id', 'flight_hrs', 'maint_type',
                'inspection_interval', 'technician', 'date']
        rc, ra = self._sort_reg
        if 0 < rc < len(KEYS) and KEYS[rc]:
            data.sort(key=lambda r: str(r.get(KEYS[rc], '')),
                      reverse=not ra)
        LABELS = ['', '기체 등록번호', '누적 비행시간', '정비 종류',
                  '주기', '담당자', '날짜']
        for col, lbl in enumerate(LABELS):
            h = self._tbl_reg.horizontalHeaderItem(col)
            if h:
                h.setText(lbl + ((' ▲' if ra else ' ▼')
                                 if col == rc else ''))
        self._tbl_reg.setRowCount(len(data))
        for row, r in enumerate(data):
            self._tbl_reg.setRowHeight(row, ROW_H)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
                         | Qt.ItemIsSelectable)
            chk.setData(Qt.UserRole, r)
            self._tbl_reg.setItem(row, 0, chk)
            cells = [
                (r.get('aircraft_id', ''), Qt.AlignCenter),
                (f"{r.get('flight_hrs',0):,.0f} H", Qt.AlignCenter),
                (r.get('maint_type', ''),
                 Qt.AlignLeft | Qt.AlignVCenter),
                (_extract_cycle(r.get('maint_type', ''),
                                r.get('inspection_interval', '')),
                 Qt.AlignCenter),
                (r.get('technician', ''), Qt.AlignCenter),
                (r.get('date', ''), Qt.AlignCenter)]
            for col, (txt, align) in enumerate(cells):
                it = QTableWidgetItem(txt)
                it.setTextAlignment(align)
                it.setData(Qt.UserRole, r)
                self._tbl_reg.setItem(row, col + 1, it)

    # ── 비정기 정비 테이블 채우기 ───────────────────────────
    def _fill_irr(self, data):
        KEYS = ['', 'aircraft_id', 'flight_hrs', 'maint_type',
                'technician', 'date']
        ic, ia = self._sort_irr
        if 0 < ic < len(KEYS) and KEYS[ic]:
            data.sort(key=lambda r: str(r.get(KEYS[ic], '')),
                      reverse=not ia)
        LABELS = ['', '기체 등록번호', '누적 비행시간', '정비 종류',
                  '담당자', '날짜']
        for col, lbl in enumerate(LABELS):
            h = self._tbl_irr.horizontalHeaderItem(col)
            if h:
                h.setText(lbl + ((' ▲' if ia else ' ▼')
                                 if col == ic else ''))
        self._tbl_irr.setRowCount(len(data))
        for row, r in enumerate(data):
            self._tbl_irr.setRowHeight(row, ROW_H)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
                         | Qt.ItemIsSelectable)
            chk.setData(Qt.UserRole, r)
            self._tbl_irr.setItem(row, 0, chk)
            cells = [
                (r.get('aircraft_id', ''), Qt.AlignCenter),
                (f"{r.get('flight_hrs',0):,.0f} H", Qt.AlignCenter),
                (r.get('maint_type', ''),
                 Qt.AlignLeft | Qt.AlignVCenter),
                (r.get('technician', ''), Qt.AlignCenter),
                (r.get('date', ''), Qt.AlignCenter)]
            for col, (txt, align) in enumerate(cells):
                it = QTableWidgetItem(txt)
                it.setTextAlignment(align)
                it.setData(Qt.UserRole, r)
                self._tbl_irr.setItem(row, col + 1, it)

    # ── 행 선택 → 교체 부품 목록 ───────────────────────────
    def _on_reg_select(self):
        rows = set(i.row() for i in self._tbl_reg.selectedItems())
        if not rows:
            return
        it = self._tbl_reg.item(list(rows)[0], 0)
        self._show_parts(it.data(Qt.UserRole) if it else None)

    def _on_irr_select(self):
        rows = set(i.row() for i in self._tbl_irr.selectedItems())
        if not rows:
            return
        it = self._tbl_irr.item(list(rows)[0], 0)
        self._show_parts(it.data(Qt.UserRole) if it else None)

    def _show_parts(self, rec):
        if not rec:
            return
        parts = rec.get('parts', [])
        self._tbl_parts.setRowCount(len(parts))
        for row, p in enumerate(parts):
            self._tbl_parts.setRowHeight(row, ROW_H)
            texts = [p.get('part_no', '') or str(p.get('part_id', '')),
                     p.get('name', ''), str(p.get('qty', 1))]
            for col, txt in enumerate(texts):
                it = QTableWidgetItem(txt)
                it.setTextAlignment(Qt.AlignCenter)
                self._tbl_parts.setItem(row, col, it)