"""
page_parts.py - 와이어프레임(img_03) 기준 + 컬럼 정렬
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QLineEdit, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from styles import COLOR
from api import fetch_parts, insert_part, delete_parts
from dialogs_parts import PartDialog

AC_TYPES = ['-- 전체 --', 'DA-40NG', 'DA-42NG']
ROW_H    = 52
COLS     = ['', '부품번호', '부품명칭', '재고 수량', '안전재고 수량', '위치', '적용 기종']
SORT_KEYS = ['', 'part_no', 'name', 'qty', 'safe_qty', 'location', '']


class PartsPage(QWidget):
    COLS = COLS

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parts    = []
        self._sort_col = -1
        self._sort_asc = True
        self._build_ui()
        self._load()

    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ── 툴바 ──
        tb = QFrame()
        tb.setStyleSheet(
            f'background:#fafbfc; border-bottom:1px solid {COLOR["border"]};'
        )
        th = QHBoxLayout(tb)
        th.setContentsMargins(12, 10, 12, 10)
        th.setSpacing(8)

        self._ac_combo = QComboBox()
        self._ac_combo.addItems(AC_TYPES)
        self._ac_combo.setFixedWidth(140)
        self._ac_combo.currentTextChanged.connect(self._refresh)

        self._search = QLineEdit()
        self._search.setObjectName('searchInput')
        self._search.setPlaceholderText('부품번호 / 명칭 검색')
        self._search.textChanged.connect(self._refresh)

        btn_add = QPushButton('+ 신규')
        btn_add.setStyleSheet(
            f'background:{COLOR["primary"]}; color:white; border:none;'
            f'padding:8px 18px; border-radius:4px; font-size:18px;'
        )
        btn_add.clicked.connect(self._on_add)

        btn_del = QPushButton('🗑 삭제')
        btn_del.setStyleSheet(
            f'background:{COLOR["red"]}; color:white; border:none;'
            f'padding:8px 18px; border-radius:4px; font-size:18px;'
        )
        btn_del.clicked.connect(self._on_delete)

        th.addWidget(self._ac_combo)
        th.addWidget(self._search, 1)
        th.addStretch()
        th.addWidget(btn_add)
        th.addWidget(btn_del)
        v.addWidget(tb)

        # ── 테이블 ──
        self._table = QTableWidget()
        self._table.setColumnCount(len(self.COLS))
        self._table.setHorizontalHeaderLabels(self.COLS)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(ROW_H)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        self._table.setColumnWidth(0, 44)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        for col in [1, 3, 4, 5, 6]:
            hdr.setSectionResizeMode(col, QHeaderView.Interactive)
        self._table.setColumnWidth(1, 300)
        self._table.setColumnWidth(3, 200)
        self._table.setColumnWidth(4, 200)
        self._table.setColumnWidth(5, 200)
        self._table.setColumnWidth(6, 160)
        hdr.setMinimumSectionSize(60)

        # 헤더 체크박스 (전체 선택)
        self._header_chk = QTableWidgetItem()
        self._header_chk.setCheckState(Qt.Unchecked)
        self._table.setHorizontalHeaderItem(0, self._header_chk)
        hdr.sectionClicked.connect(self._on_header_click)

        self._table.doubleClicked.connect(self._on_detail)
        v.addWidget(self._table, 1)

    def _on_header_click(self, col):
        if col == 0:
            # 전체 선택/해제
            cur = self._header_chk.checkState()
            new_state = Qt.Unchecked if cur == Qt.Checked else Qt.Checked
            self._header_chk.setCheckState(new_state)
            for row in range(self._table.rowCount()):
                item = self._table.item(row, 0)
                if item:
                    item.setCheckState(new_state)
            return
        # 정렬
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
            print(f'❌ [PartsPage] 부품 로드 실패: {e}')
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
            filtered.append((p, ac_label))

        # 정렬
        if 0 < self._sort_col < len(SORT_KEYS) and SORT_KEYS[self._sort_col]:
            key = SORT_KEYS[self._sort_col]
            filtered.sort(
                key=lambda x: (x[0].get(key, 0) if isinstance(x[0].get(key, 0), (int, float))
                               else str(x[0].get(key, '')).lower()),
                reverse=not self._sort_asc
            )

        # 헤더 정렬 표시
        for col, label in enumerate(self.COLS):
            h = self._table.horizontalHeaderItem(col)
            if h and col > 0:
                h.setText(label + (' ▲' if self._sort_asc else ' ▼')
                          if col == self._sort_col else label)

        self._table.setRowCount(len(filtered))
        for row, (p, ac_label) in enumerate(filtered):
            qty      = p.get('qty', 0)
            safe_qty = p.get('safe_qty', 0)
            bg = (QColor('#f8d7da') if qty == 0 else
                  QColor('#fff3cd') if qty <= safe_qty else
                  QColor('white'))

            # 체크박스
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            chk.setData(Qt.UserRole, p)
            chk.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 0, chk)
            self._table.setRowHeight(row, ROW_H)

            cells = [
                p.get('part_no', ''), p.get('name', ''),
                str(qty), str(safe_qty),
                p.get('location', '-'), ac_label,
            ]
            aligns = [
                Qt.AlignLeft | Qt.AlignVCenter,
                Qt.AlignLeft | Qt.AlignVCenter,
                Qt.AlignCenter, Qt.AlignCenter,
                Qt.AlignCenter, Qt.AlignCenter,
            ]
            for i, (text, align) in enumerate(zip(cells, aligns)):
                col  = i + 1
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setData(Qt.UserRole, p)
                if col == 3:
                    item.setBackground(bg)
                self._table.setItem(row, col, item)

    def _checked_parts(self):
        result = []
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                result.append(item.data(Qt.UserRole))
        return result

    def _on_add(self):
        dlg = PartDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            if isinstance(d, list):
                for rec in d:
                    try:
                        insert_part(rec)
                    except Exception:
                        pass
            else:
                insert_part(d)
            self._load()

    def _on_detail(self, index):
        if index.column() == 0:
            return
        item = self._table.item(index.row(), 1)
        part = item.data(Qt.UserRole) if item else None
        if not part:
            return
        dlg = PartDialog(part=part, parent=self)
        result = dlg.exec_()
        if result in (QDialog.Accepted, 2):
            d = dlg.get_data()
            part_id = part.get('part_id') or part.get('id')
            print(f"🔧 수정 시도 part_id={part_id}, data={d}")
            try:
                from api import update_part
                update_part(part_id, d)
                print(f"✅ DB 수정 완료")
            except Exception as e:
                print(f'❌ [PartsPage] 수정 실패: {e}')
            part.update(d)
            self._load()  # DB에서 새로 가져와서 반영
            if result == 2:
                self._on_detail(index)

    def reset(self):
        """필터/검색/정렬 초기화 후 데이터 재로드"""
        self._ac_combo.setCurrentIndex(0)
        self._search.clear()
        self._sort_col = -1
        self._sort_asc = True
        self._load()

    def _on_delete(self):
        parts = self._checked_parts()
        if not parts:
            QMessageBox.information(self, '알림', '삭제할 항목을 체크하세요.')
            return
        ids = {p.get('part_id') for p in parts}
        reply = QMessageBox.question(
            self, '삭제 확인', f'{len(ids)}개 부품을 삭제하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            delete_parts(list(ids))
        except Exception as e:
            print(f'❌ [PartsPage] 삭제 실패: {e}')
        self._parts = [p for p in self._parts if p.get('part_id') not in ids]
        self._refresh()