"""
dialogs_aircraft_edit.py
AircraftEditDialog — 기체 수정 팝업
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QComboBox
)
from PyQt5.QtGui import QFont
from styles import COLOR

AC_TYPES  = ['DA-40 NG', 'DA-42 NG']
LOCATIONS = ['청주', '무안']


def _btn(label, primary=True):
    bg = COLOR['primary'] if primary else '#f0f4f8'
    fg = 'white' if primary else COLOR['text']
    b = QPushButton(label)
    b.setStyleSheet(
        f'background:{bg}; color:{fg}; border:1px solid {COLOR["border"]};'
        f'padding:8px 20px; border-radius:4px; font-size:21px;')
    return b


def _lbl(text):
    l = QLabel(text)
    l.setStyleSheet(f'font-size:20px; color:{COLOR["text"]};')
    return l

class AircraftEditDialog(QDialog):
    def __init__(self, aircraft, parent=None):
        super().__init__(parent)
        self._ac = aircraft
        self.setWindowTitle('기체 수정')
        self.setFixedWidth(560); self.setModal(True)
        ro = (f'border:1px solid {COLOR["border"]};border-radius:4px;'
              f'padding:6px 10px;font-size:20px;'
              f'background:#f0f4f8;color:{COLOR["muted"]};')
        fw = (f'border:1px solid {COLOR["border"]};border-radius:4px;'
              f'padding:6px 10px;font-size:20px;background:white;')

        layout = QVBoxLayout(self)
        layout.setSpacing(14); layout.setContentsMargins(20, 20, 20, 20)
        t = QLabel('기체 수정'); t.setFont(QFont('', 18, QFont.Bold))
        t.setStyleSheet(f'color:{COLOR["primary"]};')
        layout.addWidget(t)
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f'color:{COLOR["border"]};')
        layout.addWidget(sep)

        grid = QGridLayout(); grid.setSpacing(10)
        grid.addWidget(_lbl('기체 등록번호'), 0, 0)
        reg = QLineEdit(aircraft.get('id', ''))
        reg.setReadOnly(True); reg.setStyleSheet(ro)
        grid.addWidget(reg, 1, 0)
        grid.addWidget(_lbl('시리얼번호'), 0, 1)
        serial = QLineEdit(aircraft.get('model', '') or '-')
        serial.setReadOnly(True); serial.setStyleSheet(ro)
        grid.addWidget(serial, 1, 1)
        grid.addWidget(_lbl('기종'), 2, 0)
        self._type = QComboBox(); self._type.addItems(AC_TYPES)
        idx = self._type.findText(aircraft.get('type', ''))
        if idx >= 0: self._type.setCurrentIndex(idx)
        self._type.setStyleSheet(fw); grid.addWidget(self._type, 3, 0)
        grid.addWidget(_lbl('제조년도'), 2, 1)
        self._year = QLineEdit(str(aircraft.get('manufacture_year', '') or ''))
        self._year.setStyleSheet(fw); grid.addWidget(self._year, 3, 1)
        grid.addWidget(_lbl('장소'), 4, 0)
        self._loc = QComboBox(); self._loc.addItems(LOCATIONS)
        cl = (aircraft.get('location', '') or '').split('/')[0]
        li = self._loc.findText(cl)
        if li >= 0: self._loc.setCurrentIndex(li)
        self._loc.setStyleSheet(fw); grid.addWidget(self._loc, 5, 0)
        grid.addWidget(_lbl('누적 비행시간'), 4, 1)
        self._hours = QLineEdit(f"{aircraft.get('total_hours', 0):,.1f}")
        self._hours.setStyleSheet(fw); grid.addWidget(self._hours, 5, 1)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        btns = QHBoxLayout(); btns.addStretch()
        ok = _btn('✓ 저장'); cancel = _btn('X 닫기', False)
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        layout.addLayout(btns)

    def get_data(self):
        return {
            'category': self._type.currentText(),
            'manufacture_year': (int(self._year.text())
                if self._year.text().isdigit() else None),
            'location': self._loc.currentText(),
            'total_hours': (float(self._hours.text().replace(',', ''))
                if self._hours.text() else 0)}