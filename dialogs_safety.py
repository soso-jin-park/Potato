"""
dialogs_safety.py - 와이어프레임(img_14) 기준
부품 수정 팝업: 부품번호(읽기전용)/부품명칭/재고수량/안전재고수량
✓ 저장: 저장+유지 / X 저장 후 닫기: 저장+닫기
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from styles import COLOR


def _btn(label, primary=True):
    bg = COLOR['primary'] if primary else '#f0f4f8'
    fg = 'white'          if primary else COLOR['text']
    b  = QPushButton(label)
    b.setStyleSheet(
        f'background:{bg}; color:{fg}; border:1px solid {COLOR["border"]};'
        f'padding:8px 20px; border-radius:4px; font-size:21px;'
    )
    return b


def _lbl(text):
    l = QLabel(text)
    l.setStyleSheet(f'font-size:20px; color:{COLOR["text"]};')
    return l


class SafetyStockDialog(QDialog):
    def __init__(self, part: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle('부품 수정')
        self.setMinimumWidth(640)
        self.setModal(True)
        self._part_id = part.get('part_id')

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # 타이틀
        t = QLabel('부품 수정')
        t.setFont(QFont('', 18, QFont.Bold))
        t.setStyleSheet(f'color:{COLOR["primary"]};')
        layout.addWidget(t)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f'color:{COLOR["border"]};')
        layout.addWidget(sep)

        ro = (
            f'border:1px solid {COLOR["border"]}; border-radius:4px;'
            f'padding:6px 10px; font-size:20px;'
            f'background:#f0f4f8; color:{COLOR["muted"]};'
        )
        fw = (
            f'border:1px solid {COLOR["border"]}; border-radius:4px;'
            f'padding:6px 10px; font-size:20px; background:white;'
        )

        # 부품번호(P/N) 읽기전용
        layout.addWidget(_lbl('부품번호(P/N)'))
        self._pn = QLineEdit(part.get('part_no', ''))
        self._pn.setReadOnly(True)
        self._pn.setStyleSheet(ro)
        layout.addWidget(self._pn)

        # 부품명칭 읽기전용
        layout.addWidget(_lbl('부품명칭'))
        self._name = QLineEdit(part.get('name', ''))
        self._name.setReadOnly(True)
        self._name.setStyleSheet(ro)
        layout.addWidget(self._name)

        # 재고 수량 | 안전재고 수량 (한 행)
        qty_grid = QGridLayout()
        qty_grid.setSpacing(10)
        qty_grid.addWidget(_lbl('재고 수량'), 0, 0)
        qty_grid.addWidget(_lbl('안전재고 수량'), 0, 1)

        self._qty = QSpinBox()
        self._qty.setRange(0, 9999)
        self._qty.setValue(part.get('qty', 0))
        self._qty.setStyleSheet(fw)
        qty_grid.addWidget(self._qty, 1, 0)

        self._safe_qty = QSpinBox()
        self._safe_qty.setRange(0, 9999)
        self._safe_qty.setValue(part.get('safe_qty', 0))
        self._safe_qty.setStyleSheet(fw)
        qty_grid.addWidget(self._safe_qty, 1, 1)

        qty_grid.setColumnStretch(0, 1)
        qty_grid.setColumnStretch(1, 1)
        layout.addLayout(qty_grid)

        # 버튼: ✓ 저장(유지) / X 저장 후 닫기(닫기)
        btns = QHBoxLayout()
        btns.addStretch()
        btn_save      = _btn('✓ 저장', True)
        btn_save_close = _btn('X 저장 후 닫기', False)
        btn_save.clicked.connect(self._on_save_keep)
        btn_save_close.clicked.connect(self._on_ok)
        btns.addWidget(btn_save)
        btns.addWidget(btn_save_close)
        layout.addLayout(btns)

    def _on_save_keep(self):
        """저장하고 창 유지"""
        self.done(2)

    def _on_ok(self):
        """저장하고 닫기"""
        self.accept()

    def get_data(self) -> dict:
        return {
            'part_id':    self._part_id,
            'qty':        self._qty.value(),
            'safe_qty':   self._safe_qty.value(),
            'order_unit': 1,
            'lead_time':  98,
        }