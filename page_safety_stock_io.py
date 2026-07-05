"""
page_safety_stock_io.py
SafetyStockPage 로직 믹스인 — reset / load / refresh / badge / detail
"""
from PyQt5.QtWidgets import QTableWidgetItem, QDialog, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from api import fetch_parts, update_safety_stock
from dialogs_safety import SafetyStockDialog
from styles import COLOR

ROW_H = 52

def _status(qty, safe_qty):
    if qty == 0 or qty < safe_qty:
        return '부족', QColor('#f8d7da'), QColor('#721c24')
    if qty <= safe_qty * 1.5:
        return '경고', QColor('#fff3cd'), QColor('#856404')
    return '정상', QColor('#d4edda'), QColor('#155724')


def _pct(qty, safe_qty):
    if safe_qty == 0:
        return 100
    return min(int(qty / safe_qty * 100), 999)


class SafetyStockIOMixin:
    def reset(self):
        """필터/검색/정렬 초기화 후 데이터 재로드"""
        self._ac_combo.setCurrentIndex(0)
        self._search.clear()
        self._sort_col = -1
        self._sort_asc = True
        self._status_filter = None
        self._load()

    def _on_header_click(self, col):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._refresh()

    def _load(self):
        try:
            self._parts = fetch_parts()
        except Exception as e:
            print(f'❌ [SafetyStockPage] 로드 실패: {e}')
            self._parts = []
        self._refresh()

    def _refresh(self):
        ac = self._ac_combo.currentText()
        kw = self._search.text().strip().lower()

        filtered = []
        for p in self._parts:
            ac_id    = p.get('aircraft_id')
            ac_label = 'DA-40NG' if ac_id == 2 else 'DA-42NG' if ac_id == 3 else ''
            if ac != '-- 전체 --' and ac_label != ac:
                continue
            if kw and kw not in p.get('part_no', '').lower() \
                    and kw not in p.get('name', '').lower():
                continue
            filtered.append(p)

        SORT_KEYS = ['part_no', 'name', 'qty', 'safe_qty', '_pct', '_status', 'unit_price']

        def _sort_val(p, key):
            if key == '_pct':
                return _pct(p.get('qty', 0), p.get('safe_qty', 0))
            if key == '_status':
                st = _status(p.get('qty', 0), p.get('safe_qty', 0))[0]
                return {'부족': 0, '경고': 1, '정상': 2}.get(st, 9)
            val = p.get(key, 0)
            if isinstance(val, (int, float)):
                return val
            return str(val or '').lower()

        if 0 <= self._sort_col < len(SORT_KEYS) and SORT_KEYS[self._sort_col]:
            sk = SORT_KEYS[self._sort_col]
            filtered.sort(key=lambda p: _sort_val(p, sk),
                          reverse=not self._sort_asc)
        LABELS = ['부품번호', '부품명칭', '재고 수량', '안전재고 수량', '재고 비율(%)', '재고 상태', '전 분기 단가 (EUR)']
        for col, label in enumerate(LABELS):
            h = self._table.horizontalHeaderItem(col)
            if h:
                h.setText(label + (' ▲' if self._sort_asc else ' ▼') if col == self._sort_col else label)
        self._table.setRowCount(len(filtered))
        danger_cnt = warn_cnt = 0
        order_parts = []

        for row, p in enumerate(filtered):
            qty      = p.get('qty', 0)
            safe_qty = p.get('safe_qty', 0)
            pct      = _pct(qty, safe_qty)
            st, bg, fg = _status(qty, safe_qty)
            unit_price = p.get('unit_price', 0.0)

            if st == '부족':
                danger_cnt += 1
                order_parts.append(p)
            elif st == '경고':
                warn_cnt += 1
                order_parts.append(p)

            self._table.setRowHeight(row, ROW_H)
            cells = [
                p.get('part_no', ''), p.get('name', ''),
                str(qty), str(safe_qty),
                f'{pct}%', st,
                f'{unit_price:.1f}' if unit_price else '-',
            ]
            aligns = [
                Qt.AlignLeft | Qt.AlignVCenter,
                Qt.AlignLeft | Qt.AlignVCenter,
                Qt.AlignCenter, Qt.AlignCenter,
                Qt.AlignCenter, Qt.AlignCenter,
                Qt.AlignCenter,
            ]
            for col, (text, align) in enumerate(zip(cells, aligns)):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setData(Qt.UserRole, p)
                if col == 5:
                    item.setBackground(bg)
                    item.setForeground(fg)
                    f2 = item.font()
                    f2.setBold(True)
                    item.setFont(f2)
                elif col == 4 and pct < 100:
                    item.setForeground(QColor(COLOR['red']))
                self._table.setItem(row, col, item)

        ok_cnt = len(filtered) - danger_cnt - warn_cnt
        self._update_badge(self._badge_danger, f'{danger_cnt}\n부족', COLOR['red'])
        self._update_badge(self._badge_warn,   f'{warn_cnt}\n경고',  COLOR['orange'])
        self._update_badge(self._badge_ok,     f'{ok_cnt}\n정상',    COLOR['green'])

        # 배지 필터 적용
        if self._status_filter == '부족':
            display_parts = [p for p in order_parts
                             if _status(p.get('qty', 0), p.get('safe_qty', 0))[0] == '부족']
        elif self._status_filter == '경고':
            display_parts = [p for p in order_parts
                             if _status(p.get('qty', 0), p.get('safe_qty', 0))[0] == '경고']
        elif self._status_filter == '정상':
            display_parts = []  # 정상은 빈 표
        else:
            display_parts = order_parts  # 전체 (부족+경고)

        self._update_order_table(display_parts)
        self._update_badge_styles()

    def _update_badge(self, badge, text, color):
        lbl = badge.findChild(QLabel)
        if lbl:
            lbl.setText(text)
            lbl.setStyleSheet(
                f'color:{color}; border:none; font-size:28px; font-weight:bold;'
            )

    def _update_order_table(self, parts):
        self._order_model.load(parts)

    def _on_detail(self, index):
        item = self._table.item(index.row(), 0)
        part = item.data(Qt.UserRole) if item else None
        if not part:
            return
        dlg = SafetyStockDialog(part=part, parent=self)
        result = dlg.exec_()
        if result in (QDialog.Accepted, 2):
            d = dlg.get_data()
            try:
                update_safety_stock(part.get('part_id'), d)
                # qty(재고수량)가 변경된 경우 parts_inventory도 업데이트
                if d.get('qty') is not None and d['qty'] != part.get('qty'):
                    from api import update_part
                    update_part(part.get('part_id'), {'qty': d['qty']})
            except Exception as e:
                print(f'❌ [SafetyStockPage] 수정 실패: {e}')
            # 화면에 즉시 반영
            part['qty']        = d.get('qty', part.get('qty', 0))
            part['safe_qty']   = d['safe_qty']
            part['order_unit'] = d.get('order_unit', 1)
            part['lead_time']  = d.get('lead_time', 98)
            self._refresh()
            if result == 2:
                self._on_detail(index)