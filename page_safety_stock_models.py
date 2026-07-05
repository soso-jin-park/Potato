"""
page_safety_stock_models.py
_OrderModel, _ColorDelegate — 안전재고 테이블 모델 및 delegate
"""
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

