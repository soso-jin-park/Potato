"""
page_inout_io.py
InOutPage 로직 믹스인 — load / refresh / 입고 / 출고 / sync
"""
from PyQt5.QtWidgets import QTableWidgetItem, QDialog, QMessageBox
from PyQt5.QtCore import Qt

from api import (fetch_inbound, fetch_outbound,
                 insert_inbound, insert_outbound, delete_inout)
from dialogs_inout import InboundDialog, OutboundDialog

IN_KEYS  = ['', 'part_no', 'name', 'qty', '', 'date']
OUT_KEYS = ['', 'part_no', 'name', 'qty', 'qty', 'region', 'technician', 'date']
IN_LABELS  = ['', '부품번호', '부품명칭', '재고 수량', '안전재고 수량', '입고 날짜']
OUT_LABELS = ['', '부품번호', '부품명칭', '재고 수량', '출고 수량', '지역', '담당자', '출고 날짜']
ROW_H = 52


class InOutPageIOMixin:

    def _load(self):
        try:
            self._inbound = fetch_inbound()
        except Exception as e:
            print(f'❌ [InOutPage] 입고 로드 실패: {e}')
        try:
            self._outbound = fetch_outbound()
        except Exception as e:
            print(f'❌ [InOutPage] 출고 로드 실패: {e}')
        self._refresh()

    def reset(self):
        self._ac_combo.setCurrentIndex(0)
        self._search.clear()
        self._sort_in  = (-1, True)
        self._sort_out = (-1, True)
        self._load()

    def _refresh(self):
        kw = self._search.text().strip().lower()

        # ── 입고 ──
        in_data = [r for r in self._inbound
                   if not kw or kw in r.get('part_no', '').lower()
                   or kw in r.get('name', '').lower()]
        in_col, in_asc = self._sort_in
        if 0 < in_col < len(IN_KEYS) and IN_KEYS[in_col]:
            in_data.sort(
                key=lambda r: str(r.get(IN_KEYS[in_col], '')),
                reverse=not in_asc)
        for col, lbl in enumerate(IN_LABELS):
            h = self._tbl_in.horizontalHeaderItem(col)
            if h:
                h.setText(lbl + (' ▲' if in_asc else ' ▼')
                          if col == in_col else lbl)
        self._tbl_in.setRowCount(len(in_data))
        for row, r in enumerate(in_data):
            self._tbl_in.setRowHeight(row, ROW_H)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
                         | Qt.ItemIsSelectable)
            chk.setData(Qt.UserRole, r)
            self._tbl_in.setItem(row, 0, chk)
            cells = [r.get('part_no', ''), r.get('name', ''),
                     str(r.get('qty', 0)), '', r.get('date', '')]
            aligns = [Qt.AlignLeft | Qt.AlignVCenter,
                      Qt.AlignLeft | Qt.AlignVCenter,
                      Qt.AlignCenter, Qt.AlignCenter, Qt.AlignCenter]
            for i, (text, align) in enumerate(zip(cells, aligns)):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setData(Qt.UserRole, r)
                self._tbl_in.setItem(row, i + 1, item)

        # ── 출고 ──
        out_data = [r for r in self._outbound
                    if not kw or kw in r.get('part_no', '').lower()
                    or kw in r.get('name', '').lower()]
        out_col, out_asc = self._sort_out
        if 0 < out_col < len(OUT_KEYS) and OUT_KEYS[out_col]:
            out_data.sort(
                key=lambda r: str(r.get(OUT_KEYS[out_col], '')),
                reverse=not out_asc)
        for col, lbl in enumerate(OUT_LABELS):
            h = self._tbl_out.horizontalHeaderItem(col)
            if h:
                h.setText(lbl + (' ▲' if out_asc else ' ▼')
                          if col == out_col else lbl)
        self._tbl_out.setRowCount(len(out_data))
        for row, r in enumerate(out_data):
            self._tbl_out.setRowHeight(row, ROW_H)
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
                         | Qt.ItemIsSelectable)
            chk.setData(Qt.UserRole, r)
            self._tbl_out.setItem(row, 0, chk)
            cells = [r.get('part_no', ''), r.get('name', ''),
                     str(r.get('qty', 0)), str(r.get('qty', 0)),
                     r.get('region', ''), r.get('technician', ''),
                     r.get('date', '')]
            aligns = [Qt.AlignLeft | Qt.AlignVCenter,
                      Qt.AlignLeft | Qt.AlignVCenter,
                      Qt.AlignCenter, Qt.AlignCenter,
                      Qt.AlignCenter, Qt.AlignCenter, Qt.AlignCenter]
            for i, (text, align) in enumerate(zip(cells, aligns)):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setData(Qt.UserRole, r)
                self._tbl_out.setItem(row, i + 1, item)

    def _on_inbound(self):
        dlg = InboundDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            recs = d if isinstance(d, list) else [d]
            for rec in recs:
                try:
                    self._inbound.insert(0, insert_inbound(rec))
                except Exception as e:
                    print(f'❌ [InOutPage] 입고 등록 실패: {e}')
                    if not isinstance(d, list):
                        self._inbound.insert(0, rec)
            self._refresh()
            self._sync_parts()

    def _on_outbound(self):
        dlg = OutboundDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            recs = d if isinstance(d, list) else [d]
            for rec in recs:
                try:
                    self._outbound.insert(0, insert_outbound(rec))
                except Exception as e:
                    print(f'❌ [InOutPage] 출고 등록 실패: {e}')
                    if not isinstance(d, list):
                        self._outbound.insert(0, rec)
            self._refresh()
            self._sync_parts()

    def _on_delete(self):
        # 입고·출고 테이블에서 체크된 항목의 id 수집
        in_ids, out_ids = [], []
        for row in range(self._tbl_in.rowCount()):
            it = self._tbl_in.item(row, 0)
            if it and it.checkState() == Qt.Checked:
                rec = it.data(Qt.UserRole)
                if rec and rec.get('id') is not None:
                    in_ids.append(rec['id'])
        for row in range(self._tbl_out.rowCount()):
            it = self._tbl_out.item(row, 0)
            if it and it.checkState() == Qt.Checked:
                rec = it.data(Qt.UserRole)
                if rec and rec.get('id') is not None:
                    out_ids.append(rec['id'])

        all_ids = in_ids + out_ids
        if not all_ids:
            QMessageBox.information(self, '알림', '삭제할 항목을 체크하세요.')
            return

        msg = f'입고 {len(in_ids)}건, 출고 {len(out_ids)}건을 삭제하시겠습니까?'
        if QMessageBox.question(
                self, '삭제 확인', msg,
                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        try:
            delete_inout(all_ids)
        except Exception as e:
            print(f'❌ [InOutPage] 삭제 실패: {e}')

        # 로컬 목록에서도 제거
        self._inbound  = [r for r in self._inbound
                          if r.get('id') not in in_ids]
        self._outbound = [r for r in self._outbound
                          if r.get('id') not in out_ids]
        self._refresh()
        self._sync_parts()

    def _sync_parts(self):
        try:
            from api import fetch_parts
            from inventory import inventory
            fresh = fetch_parts()
            inventory.parts = fresh
            # 부품관리 등 다른 페이지에 실제 재고 변동 알림
            inventory.stock_updated.emit()
            print(f"✅ [InOutPage] 부품 재고 동기화 완료: {len(fresh)}개")
        except Exception as e:
            print(f"❌ [InOutPage] 부품 재고 동기화 실패: {e}")