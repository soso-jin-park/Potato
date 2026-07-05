"""
page_aircraft_io.py
AircraftPage 로직 믹스인 — _load / _refresh / 클릭 / 추가 / 삭제
"""
from PyQt5.QtWidgets import QTableWidgetItem, QDialog, QMessageBox
from PyQt5.QtCore import Qt

from api import fetch_aircraft_status
from dialogs_aircraft import AircraftDialog, AircraftEditDialog

ROW_H = 52


class AircraftPageIOMixin:

    def _load(self):
        try:
            self._aircraft = fetch_aircraft_status()
        except Exception as e:
            print(f'❌ [AircraftPage] 로드 실패: {e}')
            self._aircraft = []
        self._refresh()

    def reset(self):
        self._ac_combo.setCurrentIndex(0)
        self._search.clear()
        self._sort_col = -1
        self._sort_asc = True
        self._selected = None
        self._parts_tbl.setRowCount(0)
        self._load()

    def _get_sort_key(self, ac):
        keys = [None, 'id', None, 'type', None, None, 'total_hours', None]
        col = self._sort_col
        if col < 0 or col >= len(keys) or not keys[col]:
            return ''
        val = ac.get(keys[col], '')
        if col == 6:
            try:
                return float(str(val).replace(',', '').replace('H', '').strip())
            except Exception:
                return 0
        return str(val).lower()

    def _on_header_click(self, col):
        if col == 0:
            return
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._refresh()

    def _refresh(self):
        ac_f = self._ac_combo.currentText()
        kw   = self._search.text().strip().lower()
        filtered = [
            ac for ac in self._aircraft
            if (ac_f == '-- 전체 --'
                or ac.get('type', '').replace(' ', '') == ac_f.replace(' ', ''))
            and (not kw or kw in ac.get('id', '').lower())
        ]
        if self._sort_col > 0:
            filtered.sort(key=self._get_sort_key, reverse=not self._sort_asc)

        for col, (label, _) in enumerate(self._COLS_DATA):
            h = self._table.horizontalHeaderItem(col)
            if h:
                h.setText(label + (' ▲' if self._sort_asc else ' ▼')
                          if col == self._sort_col else label)

        self._table.setRowCount(len(filtered))
        for row, ac in enumerate(filtered):
            self._table.setRowHeight(row, ROW_H)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
                         | Qt.ItemIsSelectable)
            chk.setData(Qt.UserRole, ac)
            self._table.setItem(row, 0, chk)
            total = ac.get('total_hours', 0)
            cells = [
                ac.get('id', ''),
                ac.get('model', '') or ac.get('registration', ''),
                ac.get('type', ''),
                str(ac.get('manufacture_year', '') or '-'),
                ac.get('location', '-') or '-',
                f'{total:,.1f} H', '-',
            ]
            aligns = [
                Qt.AlignCenter, Qt.AlignLeft | Qt.AlignVCenter,
                Qt.AlignCenter, Qt.AlignCenter,
                Qt.AlignCenter, Qt.AlignCenter, Qt.AlignCenter,
            ]
            for col, (text, align) in enumerate(zip(cells, aligns)):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setData(Qt.UserRole, ac)
                self._table.setItem(row, col + 1, item)

    def _on_row_click(self, row, col):
        item = self._table.item(row, 1)
        if not item:
            return
        ac = item.data(Qt.UserRole)
        self._selected = ac
        from api import fetch_bom_parts
        try:
            parts = fetch_bom_parts(ac.get('type', '').replace(' ', ''))
            seen, unique = set(), []
            for p in parts:
                pno = p.get('part_no', '')
                if pno not in seen:
                    seen.add(pno)
                    unique.append(p)
            self._parts_tbl.setRowCount(len(unique))
            for r, p in enumerate(unique):
                for c, val in enumerate([p.get('part_no', ''), p.get('name', '')]):
                    it = QTableWidgetItem(val)
                    it.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self._parts_tbl.setItem(r, c, it)
        except Exception as e:
            print(f'❌ [AircraftPage] 부품 로드 실패: {e}')

    def _on_double_click(self, index):
        if index.column() == 0:
            return
        item = self._table.item(index.row(), 1)
        ac = item.data(Qt.UserRole) if item else None
        if not ac:
            return
        dlg = AircraftEditDialog(aircraft=ac, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            try:
                from api import update_aircraft
                update_aircraft(ac.get('db_id') or ac.get('id'), d)
            except Exception as e:
                print(f'❌ [AircraftPage] 기체 수정 실패: {e}')
            self._load()

    def _checked_aircraft(self):
        return [
            self._table.item(row, 0).data(Qt.UserRole)
            for row in range(self._table.rowCount())
            if self._table.item(row, 0)
            and self._table.item(row, 0).checkState() == Qt.Checked
        ]

    def _on_add(self):
        dlg = AircraftDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            if isinstance(d, list):
                print(f'✅ [AircraftPage] {len(d)}건 일괄 등록 요청')
            self._load()

    def _on_delete(self):
        selected = self._checked_aircraft()
        if not selected:
            QMessageBox.information(self, '알림', '삭제할 기체를 체크하세요.')
            return
        reply = QMessageBox.question(
            self, '삭제 확인', f'{len(selected)}개 기체를 삭제하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        QMessageBox.information(self, '알림', '기체 삭제 기능은 준비 중입니다.')
