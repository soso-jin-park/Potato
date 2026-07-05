"""
page_safety_stock.py
메뉴 > 재고관리 > 안전재고 관리 - 와이어프레임(img_14) 기준
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QLineEdit, QComboBox, QSplitter,
    QTableView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import QStyledItemDelegate

from styles import COLOR
from api import fetch_parts, update_safety_stock
from dialogs_safety import SafetyStockDialog

ROW_H    = 52
AC_TYPES = ['-- 전체 --', 'DA-40NG', 'DA-42NG']


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



class _OrderModel(QAbstractTableModel):
    """발주필요부품 테이블 - BackgroundRole 직접 반환해 QSS 우회"""
    HEADERS = ['부품번호', '부품명칭', '재고', '안전재고']

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []   # list of (part_no, name, qty, safe_qty, bg, fg)

    def load(self, parts):
        self.beginResetModel()
        self._data = []
        for p in parts:
            qty      = p.get('qty', 0)
            safe_qty = p.get('safe_qty', 0)
            if qty == 0 or qty < safe_qty:
                bg, fg = QColor('#f8d7da'), QColor('#721c24')
            elif qty <= safe_qty * 1.5:
                bg, fg = QColor('#fff3cd'), QColor('#856404')
            else:
                bg, fg = QColor('#d4edda'), QColor('#155724')
            self._data.append((
                p.get('part_no', ''), p.get('name', ''),
                str(qty), str(safe_qty), bg, fg
            ))
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()): return len(self._data)
    def columnCount(self, parent=QModelIndex()): return 4

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._data):
            return QVariant()
        row = self._data[index.row()]
        if role == Qt.DisplayRole:
            return row[index.column()]
        if role == Qt.BackgroundRole:
            return row[4]
        if role == Qt.ForegroundRole:
            return row[5]
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter if index.column() in (2, 3) else (Qt.AlignLeft | Qt.AlignVCenter)
        return QVariant()


class _ColorDelegate(QStyledItemDelegate):
    """QSS를 완전히 우회하여 배경색을 직접 그리는 delegate"""
    def paint(self, painter, option, index):
        from PyQt5.QtWidgets import QStyle, QStyleOptionViewItem
        from PyQt5.QtGui import QBrush, QPalette

        bg = index.data(Qt.BackgroundRole)
        fg = index.data(Qt.ForegroundRole)
        is_sel = bool(int(option.state) & QStyle.State_Selected)

        # option 복사 후 배경 관련 상태 제거
        opt = QStyleOptionViewItem(option)
        opt.state &= ~QStyle.State_Selected
        opt.state &= ~QStyle.State_HasFocus
        opt.backgroundBrush = QBrush()  # 브러시 초기화로 QSS 배경 차단

        # 팔레트에서 base 색상 재지정
        pal = opt.palette
        if is_sel:
            fill = QColor('#c8d8f8')
        elif bg and isinstance(bg, QColor) and bg.isValid():
            fill = bg
        else:
            fill = QColor('white')
        pal.setColor(QPalette.Base, fill)
        pal.setColor(QPalette.Window, fill)
        opt.palette = pal

        # 전경색
        if fg and isinstance(fg, QColor):
            p2 = opt.palette
            p2.setColor(QPalette.Text, fg if not is_sel else QColor('#000000'))
            opt.palette = p2

        # 배경 직접 채우기
        painter.fillRect(option.rect, fill)

        # 텍스트 그리기 (배경 없이)
        super().paint(painter, opt, index)

class SafetyStockPage(QWidget):
    COLS = ['부품번호', '부품명칭', '재고 수량', '안전재고 수량',
            '재고 비율(%)', '재고 상태', '전 분기 단가 (EUR)']

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parts = []
        self._sort_col = -1
        self._sort_asc = True
        self._status_filter = None  # None=부족+경고, '부족', '경고', '정상'
        self._build_ui()
        self._load()

    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # 툴바
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

        th.addWidget(self._ac_combo)
        th.addWidget(self._search, 1)
        v.addWidget(tb)

        # 좌우 분할
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle { background:#d0d7e2; }
            QSplitter::handle:hover { background:#4a90d9; }
        """)
        splitter.addWidget(self._build_table_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([600, 700])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        v.addWidget(splitter, 1)

    def _build_table_panel(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self._table = QTableWidget()
        self._table.setColumnCount(len(self.COLS))
        self._table.setHorizontalHeaderLabels(self.COLS)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(ROW_H)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        for col in [0, 2, 3, 4, 5, 6]:
            hdr.setSectionResizeMode(col, QHeaderView.Interactive)
        self._table.setColumnWidth(0, 280)
        self._table.setColumnWidth(2, 170)
        self._table.setColumnWidth(3, 200)
        self._table.setColumnWidth(4, 180)
        self._table.setColumnWidth(5, 170)
        self._table.setColumnWidth(6, 260)
        hdr.setMinimumSectionSize(100)

        self._table.doubleClicked.connect(self._on_detail)
        self._table.horizontalHeader().sectionClicked.connect(self._on_header_click)
        v.addWidget(self._table)
        return w

    def _build_right_panel(self):
        panel = QFrame()
        panel.setStyleSheet(
            f'background:white; border-left:1px solid {COLOR["border"]};'
        )
        panel.setMinimumWidth(500)
        panel.setMaximumWidth(750)

        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(14)

        # ── 재고 수량 현황 요약 ──
        summary_lbl = QLabel('재고 수량 현황 요약')
        summary_lbl.setFont(QFont('', 22, QFont.Bold))
        summary_lbl.setStyleSheet(f'color:{COLOR["text"]};')
        v.addWidget(summary_lbl)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(16)
        self._badge_danger = self._make_badge('0\n부족', COLOR['red'])
        self._badge_warn   = self._make_badge('0\n경고', COLOR['orange'])
        self._badge_ok     = self._make_badge('0\n정상', COLOR['green'])

        # 배지 클릭 이벤트 연결
        self._badge_danger.setCursor(Qt.PointingHandCursor)
        self._badge_warn.setCursor(Qt.PointingHandCursor)
        self._badge_ok.setCursor(Qt.PointingHandCursor)
        self._badge_danger.mousePressEvent = lambda e: self._on_badge_click('부족')
        self._badge_warn.mousePressEvent = lambda e: self._on_badge_click('경고')
        self._badge_ok.mousePressEvent = lambda e: self._on_badge_click('정상')

        badge_row.addWidget(self._badge_danger, 1)
        badge_row.addWidget(self._badge_warn, 1)
        badge_row.addWidget(self._badge_ok, 1)
        v.addLayout(badge_row)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet(f'color:{COLOR["border"]};')
        v.addWidget(sep1)

        # ── 다음 발주 필요 부품 ──
        order_lbl = QLabel('다음 발주 필요 부품')
        order_lbl.setFont(QFont('', 21, QFont.Bold))
        order_lbl.setStyleSheet(f'color:{COLOR["text"]};')
        v.addWidget(order_lbl)

        self._order_model = _OrderModel()
        self._order_tbl = QTableView()
        self._order_tbl.setObjectName('orderTbl')
        self._order_tbl.setModel(self._order_model)
        self._order_tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._order_tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._order_tbl.verticalHeader().setVisible(False)
        self._order_tbl.verticalHeader().setDefaultSectionSize(52)
        self._order_tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._order_tbl.setColumnWidth(0, 160)
        self._order_tbl.setColumnWidth(2, 60)
        self._order_tbl.setColumnWidth(3, 120)
        self._order_tbl.setFont(__import__('PyQt5.QtGui', fromlist=['QFont']).QFont('', 20))
        self._order_tbl.setAlternatingRowColors(False)
        self._order_tbl.setItemDelegate(_ColorDelegate(self._order_tbl))
        self._order_tbl.setShowGrid(True)
        v.addWidget(self._order_tbl, 1)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f'color:{COLOR["border"]};')
        v.addWidget(sep2)

        # ── 다음 발주일 ──
        order_date_row = QHBoxLayout()
        order_date_lbl = QLabel('다음 발주일:')
        order_date_lbl.setFont(QFont('', 21, QFont.Bold))
        order_date_lbl.setStyleSheet(f'color:{COLOR["text"]};')
        self._order_date = QLabel('2026년 7월')
        self._order_date.setStyleSheet(
            f'background:#f0f4f8; border:1px solid {COLOR["border"]};'
            f'border-radius:4px; padding:8px 16px; font-size:21px; font-weight:bold;'
            f'color:{COLOR["primary"]};'
        )
        order_date_row.addWidget(order_date_lbl)
        order_date_row.addWidget(self._order_date)
        order_date_row.addStretch()
        v.addLayout(order_date_row)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet(f'border:1px dashed {COLOR["border"]};')
        v.addWidget(sep3)

        # ── 범례 ──
        for color, text in [
            (COLOR['red'],    '부족 - 안전재고 수량 이하'),
            (COLOR['orange'], '경고 - 안전재고 수량 × 1.5 이하'),
            (COLOR['green'],  '정상'),
        ]:
            row = QHBoxLayout()
            dot = QLabel('●')
            dot.setStyleSheet(f'color:{color}; font-size:22px;')
            dot.setFixedWidth(22)
            lbl = QLabel(text)
            lbl.setStyleSheet(f'font-size:20px; color:{COLOR["text"]};')
            row.addWidget(dot)
            row.addWidget(lbl)
            row.addStretch()
            v.addLayout(row)

        return panel

    def _make_badge(self, text, color):
        f = QFrame()
        f.setMinimumSize(140, 120)
        f.setStyleSheet(
            f'background:white; border:3px solid {color}; border-radius:12px;'
        )
        v = QVBoxLayout(f)
        v.setContentsMargins(0, 0, 0, 0)
        v.setAlignment(Qt.AlignCenter)
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFont(QFont('', 28, QFont.Bold))
        lbl.setStyleSheet(f'color:{color}; border:none;')
        v.addWidget(lbl)
        f._color = color  # 원래 색상 저장
        return f

    def _on_badge_click(self, status):
        """배지 클릭 시 발주 필요 부품 테이블 필터링"""
        if self._status_filter == status:
            self._status_filter = None  # 같은 배지 다시 클릭 → 해제
        else:
            self._status_filter = status
        self._refresh()

    def _update_badge_styles(self):
        """선택된 배지 강조 표시"""
        for badge, st in [(self._badge_danger, '부족'),
                          (self._badge_warn, '경고'),
                          (self._badge_ok, '정상')]:
            c = badge._color
            if self._status_filter == st:
                badge.setStyleSheet(
                    f'background:{c}; border:3px solid {c}; border-radius:12px;')
                lbl = badge.findChild(QLabel)
                if lbl:
                    lbl.setStyleSheet(
                        f'color:white; border:none; font-size:28px; font-weight:bold;')
            else:
                badge.setStyleSheet(
                    f'background:white; border:3px solid {c}; border-radius:12px;')
                lbl = badge.findChild(QLabel)
                if lbl:
                    lbl.setStyleSheet(
                        f'color:{c}; border:none; font-size:28px; font-weight:bold;')


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