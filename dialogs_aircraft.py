"""
dialogs_aircraft.py - 기체 등록 / 기종 등록 / 기체 수정 팝업
CSV 양식 다운로드 + Excel/CSV 파일 업로드 지원
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QComboBox,
    QSpinBox, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QWidget, QFileDialog
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QFont, QIcon
import pandas as pd
from pathlib import Path
from styles import COLOR

# [Linux] __file__ 기준 절대경로
BASE_DIR = Path(__file__).resolve().parent


def _res(filename: str) -> str:
    return str(BASE_DIR / filename)


AC_TYPES  = ['DA-40 NG', 'DA-42 NG']
LOCATIONS = ['청주', '무안']
STATUSES  = ['operational', 'grounded', 'maintenance']
AC_CSV    = ['기체등록번호', '기종', '시리얼번호', '제조년도', '설치지역', '설치날짜']

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

def _field():
    return (f'border:1px solid {COLOR["border"]}; border-radius:4px;'
            f'padding:6px 10px; font-size:20px; background:white;')


class AircraftDialog(QDialog):
    def __init__(self, aircraft=None, parent=None):
        super().__init__(parent)
        self._edit = aircraft is not None
        self._ac = aircraft or {}
        self._uploaded_data = None
        self.setWindowTitle('기체 수정' if self._edit else '기체 등록')
        self.setFixedWidth(660); self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(14); layout.setContentsMargins(20, 20, 20, 20)

        # 타이틀 + CSV + 기종등록
        tr = QHBoxLayout()
        t = QLabel('기체 등록')
        t.setFont(QFont('', 18, QFont.Bold))
        t.setStyleSheet(f'color:{COLOR["primary"]};')
        tr.addWidget(t)
        bc = QPushButton(); bc.setIcon(QIcon(_res('excel.png')))
        bc.setIconSize(QSize(22, 22)); bc.setFixedSize(36, 36)
        bc.setToolTip('CSV 양식 다운로드')
        bc.setStyleSheet('QPushButton{border:1px solid #ccc;border-radius:6px;background:white}'
                         'QPushButton:hover{background:#f0f0f0}')
        bc.clicked.connect(self._download_csv)
        tr.addWidget(bc)
        tr.addStretch()
        btn_ac_type = QPushButton('+ 기종 등록')
        btn_ac_type.setStyleSheet(
            f'background:white; color:{COLOR["primary"]};'
            f'border:2px solid {COLOR["primary"]};'
            f'border-radius:14px; padding:4px 14px;'
            f'font-size:15px; font-weight:bold;')
        btn_ac_type.clicked.connect(self._on_ac_type)
        tr.addWidget(btn_ac_type)
        layout.addLayout(tr)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f'color:{COLOR["border"]};')
        layout.addWidget(sep)

        # 업로드
        uf = QFrame()
        uf.setStyleSheet(
            f'background:#f8f9fa;border:2px dashed {COLOR["border"]};'
            f'border-radius:8px;')
        uf_h = QHBoxLayout(uf); uf_h.setContentsMargins(16, 12, 16, 12)
        self._file_lbl = QLabel('파일 선택 시 일괄 등록')
        self._file_lbl.setStyleSheet('font-size:17px;color:#888;border:none;')
        bu = QPushButton('📂 파일 업로드')
        bu.setStyleSheet(
            'background:#217346;color:white;border:none;'
            'padding:8px 16px;border-radius:4px;font-size:17px;')
        bu.clicked.connect(self._upload_file)
        uf_h.addWidget(self._file_lbl, 1); uf_h.addWidget(bu)
        layout.addWidget(uf)
        ol = QLabel('── 또는 직접 입력 ──')
        ol.setAlignment(Qt.AlignCenter)
        ol.setStyleSheet('font-size:16px;color:#aaa;')
        layout.addWidget(ol)

        # 수동 입력
        grid = QGridLayout(); grid.setSpacing(10)
        grid.addWidget(_lbl('기체 등록번호'), 0, 0)
        grid.addWidget(_lbl('기종'), 0, 1)
        self._reg = QLineEdit(self._ac.get('registration', ''))
        self._reg.setStyleSheet(_field()); grid.addWidget(self._reg, 1, 0)
        self._type = QComboBox(); self._type.addItems(AC_TYPES)
        self._type.setStyleSheet(_field())
        if self._ac.get('category'):
            idx = self._type.findText(self._ac['category'])
            if idx >= 0: self._type.setCurrentIndex(idx)
        grid.addWidget(self._type, 1, 1)

        grid.addWidget(_lbl('시리얼번호'), 2, 0)
        grid.addWidget(_lbl('제조년도'), 2, 1)
        self._serial = QLineEdit(self._ac.get('serial_number', '') or '')
        self._serial.setStyleSheet(_field()); grid.addWidget(self._serial, 3, 0)
        self._year = QLineEdit(str(self._ac.get('manufacture_year', '') or ''))
        self._year.setStyleSheet(_field()); grid.addWidget(self._year, 3, 1)

        grid.addWidget(_lbl('설치 지역'), 4, 0)
        grid.addWidget(_lbl('설치 날짜'), 4, 1)
        self._loc = QComboBox(); self._loc.addItems(LOCATIONS)
        self._loc.setStyleSheet(_field()); grid.addWidget(self._loc, 5, 0)
        self._date = QDateEdit(QDate.currentDate())
        self._date.setCalendarPopup(True)
        self._date.setDisplayFormat('yyyy-MM-dd')
        self._date.setStyleSheet(_field()); grid.addWidget(self._date, 5, 1)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        btns = QHBoxLayout(); btns.addStretch()
        ok = _btn('✓ 등록'); cancel = _btn('X 닫기', False)
        ok.clicked.connect(self._on_ok); cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        layout.addLayout(btns)

    def _on_ac_type(self):
        dlg = AircraftTypeDialog(parent=self); dlg.exec_()

    def _download_csv(self):
        f, _ = QFileDialog.getSaveFileName(
            self, 'CSV 양식 다운로드', '기체등록_양식.csv', 'CSV (*.csv)')
        if not f: return
        try:
            pd.DataFrame(columns=AC_CSV).to_csv(
                f, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, 'CSV 양식',
                f'양식 저장 완료.\n열: {", ".join(AC_CSV)}')
        except Exception as e: QMessageBox.critical(self, '실패', str(e))

    def _upload_file(self):
        f, _ = QFileDialog.getOpenFileName(self, '기체 파일 업로드', '',
            'Excel/CSV (*.xlsx *.xls *.csv);;All (*)')
        if not f: return
        try:
            df = (pd.read_csv(f, encoding='utf-8-sig')
                  if f.endswith('.csv') else pd.read_excel(f))
        except Exception as e:
            QMessageBox.critical(self, '실패', str(e)); return
        df.rename(columns={
            '기체등록번호': 'registration', '기종': 'category',
            '시리얼번호': 'serial_number', '제조년도': 'manufacture_year',
            '설치지역': 'location', '설치날짜': 'install_date'}, inplace=True)
        recs = []
        for _, r in df.iterrows():
            reg = str(r.get('registration', '')).strip()
            if reg:
                recs.append({
                    'registration': reg,
                    'category': str(r.get('category', 'DA-40 NG')).strip(),
                    'serial_number': str(r.get('serial_number', '')).strip(),
                    'manufacture_year': (int(r['manufacture_year'])
                        if pd.notna(r.get('manufacture_year')) else None),
                    'location': str(r.get('location', '청주')).strip(),
                    'install_date': str(r.get('install_date', '')).strip()})
        if not recs:
            QMessageBox.warning(self, '실패', '유효한 데이터 없음'); return
        self._uploaded_data = recs
        self._file_lbl.setText(f'✅ {len(recs)}건 로드 완료')
        self._file_lbl.setStyleSheet(
            'font-size:17px;color:#155724;font-weight:bold;border:none;')

    def _on_ok(self):
        if self._uploaded_data: self.accept(); return
        if not self._reg.text().strip():
            QMessageBox.warning(self, '오류', '기체 등록번호를 입력하세요.')
            return
        self.accept()

    def get_data(self):
        if self._uploaded_data: return self._uploaded_data
        return {
            'registration': self._reg.text().strip(),
            'category': self._type.currentText(),
            'serial_number': self._serial.text().strip(),
            'manufacture_year': (int(self._year.text())
                if self._year.text().isdigit() else None),
            'location': self._loc.currentText(),
            'install_date': self._date.date().toString('yyyy-MM-dd')}


from dialogs_aircraft_type import AircraftTypeDialog  # noqa: F401
from dialogs_aircraft_edit import AircraftEditDialog  # noqa: F401
