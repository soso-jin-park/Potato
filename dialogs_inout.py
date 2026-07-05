"""
dialogs_inout.py - 입고/출고 등록 팝업
CSV 양식 다운로드 + Excel/CSV 파일 업로드 지원
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QComboBox,
    QSpinBox, QDateEdit, QFileDialog, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QFont, QIcon
import pandas as pd
from styles import COLOR
from api import fetch_parts

REGIONS = ['청주', '무안']
IN_CSV  = ['부품번호', '수량', '날짜']
OUT_CSV = ['부품번호', '출고수량', '지역', '담당정비사', '날짜']

def _btn(label, primary=True):
    bg = COLOR['primary'] if primary else '#f0f4f8'
    fg = 'white' if primary else COLOR['text']
    b = QPushButton(label)
    b.setStyleSheet(
        f'background:{bg}; color:{fg}; border:1px solid {COLOR["border"]};'
        f'padding:8px 20px; border-radius:4px; font-size:21px;')
    return b

def _field():
    return (f'border:1px solid {COLOR["border"]}; border-radius:4px;'
            f'padding:6px 10px; font-size:20px; background:white;')

def _ro():
    return (f'border:1px solid {COLOR["border"]}; border-radius:4px;'
            f'padding:6px 10px; font-size:20px;'
            f'background:#f0f4f8; color:{COLOR["muted"]};')

def _lbl(text):
    l = QLabel(text)
    l.setStyleSheet(f'font-size:20px; color:{COLOR["text"]};')
    return l


class InboundDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('입고 등록')
        self.setMinimumWidth(660); self.setModal(True)
        self._uploaded_data = None
        try: self._parts = fetch_parts()
        except: self._parts = []

        layout = QVBoxLayout(self)
        layout.setSpacing(14); layout.setContentsMargins(20, 20, 20, 20)

        # 타이틀 + CSV
        tr = QHBoxLayout()
        t = QLabel('입고 등록'); t.setFont(QFont('', 18, QFont.Bold))
        t.setStyleSheet(f'color:{COLOR["primary"]};')
        tr.addWidget(t)
        bc = QPushButton(); bc.setIcon(QIcon('excel.png'))
        bc.setIconSize(QSize(22, 22)); bc.setFixedSize(36, 36)
        bc.setToolTip('CSV 양식 다운로드')
        bc.setStyleSheet('QPushButton{border:1px solid #ccc;border-radius:6px;background:white}'
                         'QPushButton:hover{background:#f0f0f0}')
        bc.clicked.connect(lambda: self._dl_csv(IN_CSV, '입고_양식.csv'))
        tr.addWidget(bc); tr.addStretch()
        layout.addLayout(tr)
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f'color:{COLOR["border"]};'); layout.addWidget(sep)

        # 업로드
        uf = QFrame()
        uf.setStyleSheet(f'background:#f8f9fa;border:2px dashed {COLOR["border"]};border-radius:8px;')
        uf_h = QHBoxLayout(uf); uf_h.setContentsMargins(16, 12, 16, 12)
        self._file_lbl = QLabel('파일 선택 시 일괄 등록')
        self._file_lbl.setStyleSheet('font-size:17px;color:#888;border:none;')
        bu = QPushButton('📂 파일 업로드')
        bu.setStyleSheet('background:#217346;color:white;border:none;padding:8px 16px;border-radius:4px;font-size:17px;')
        bu.clicked.connect(self._upload_inbound)
        uf_h.addWidget(self._file_lbl, 1); uf_h.addWidget(bu)
        layout.addWidget(uf)
        ol = QLabel('── 또는 직접 입력 ──'); ol.setAlignment(Qt.AlignCenter)
        ol.setStyleSheet('font-size:16px;color:#aaa;'); layout.addWidget(ol)

        # 수동 입력
        grid = QGridLayout(); grid.setSpacing(10)
        grid.addWidget(_lbl('부품번호'), 0, 0); grid.addWidget(_lbl('부품명칭'), 0, 1)
        self._part_combo = QComboBox(); self._part_combo.setEditable(True)
        self._part_combo.setStyleSheet(_field())
        for p in self._parts:
            self._part_combo.addItem(p.get('part_no', ''), userData=p)
        self._part_combo.currentIndexChanged.connect(self._on_part)
        grid.addWidget(self._part_combo, 1, 0)
        self._name = QLineEdit(); self._name.setReadOnly(True); self._name.setStyleSheet(_ro())
        grid.addWidget(self._name, 1, 1)
        grid.addWidget(_lbl('수량'), 2, 0); grid.addWidget(_lbl('날짜'), 2, 1)
        self._qty = QSpinBox(); self._qty.setRange(1, 9999); self._qty.setStyleSheet(_field())
        grid.addWidget(self._qty, 3, 0)
        self._date = QDateEdit(QDate.currentDate()); self._date.setCalendarPopup(True)
        self._date.setDisplayFormat('yyyy-MM-dd'); self._date.setStyleSheet(_field())
        grid.addWidget(self._date, 3, 1)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        btns = QHBoxLayout(); btns.addStretch()
        ok = _btn('✓ 등록'); cancel = _btn('X 닫기', False)
        ok.clicked.connect(self._on_ok); cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        layout.addLayout(btns)
        self._on_part(0)

    def _on_part(self, idx):
        p = self._part_combo.itemData(idx)
        if p: self._name.setText(p.get('name', ''))

    def _dl_csv(self, cols, fname):
        f, _ = QFileDialog.getSaveFileName(self, 'CSV 양식 다운로드', fname, 'CSV (*.csv)')
        if not f: return
        try:
            pd.DataFrame(columns=cols).to_csv(f, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, 'CSV 양식', f'양식 저장 완료.\n열: {", ".join(cols)}')
        except Exception as e: QMessageBox.critical(self, '실패', str(e))

    def _upload_inbound(self):
        f, _ = QFileDialog.getOpenFileName(self, '입고 파일 업로드', '',
            'Excel/CSV (*.xlsx *.xls *.csv);;All (*)')
        if not f: return
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.endswith('.csv') else pd.read_excel(f)
        except Exception as e: QMessageBox.critical(self, '실패', str(e)); return
        df.rename(columns={'부품번호': 'part_no', '수량': 'qty', '날짜': 'date'}, inplace=True)
        pmap = {p.get('part_no', ''): p for p in self._parts}
        recs = []
        for _, r in df.iterrows():
            pno = str(r.get('part_no', '')).strip()
            p = pmap.get(pno, {})
            if pno:
                recs.append({'part_id': p.get('part_id'), 'part_no': pno,
                    'name': p.get('name', ''), 'qty': int(r.get('qty', 0) or 0),
                    'date': str(r.get('date', '')).strip(), 'location': '청주'})
        if not recs: QMessageBox.warning(self, '실패', '유효한 데이터 없음'); return
        self._uploaded_data = recs
        self._file_lbl.setText(f'✅ {len(recs)}건 로드 완료')
        self._file_lbl.setStyleSheet('font-size:17px;color:#155724;font-weight:bold;border:none;')

    def _on_ok(self):
        if self._uploaded_data: self.accept(); return
        if not self._part_combo.currentText().strip():
            QMessageBox.warning(self, '오류', '부품번호를 선택하세요.'); return
        self.accept()

    def get_data(self):
        if self._uploaded_data: return self._uploaded_data
        p = self._part_combo.currentData()
        return {'part_id': p.get('part_id') if p else None,
                'part_no': self._part_combo.currentText(),
                'name': self._name.text(), 'qty': self._qty.value(),
                'date': self._date.date().toString('yyyy-MM-dd'), 'location': '청주'}


class OutboundDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('출고 등록')
        self.setFixedWidth(520); self.setModal(True)
        self._uploaded_data = None
        try: self._parts = fetch_parts()
        except: self._parts = []

        layout = QVBoxLayout(self)
        layout.setSpacing(14); layout.setContentsMargins(20, 20, 20, 20)

        tr = QHBoxLayout()
        t = QLabel('출고 등록'); t.setFont(QFont('', 18, QFont.Bold))
        t.setStyleSheet(f'color:{COLOR["primary"]};')
        tr.addWidget(t)
        bc = QPushButton(); bc.setIcon(QIcon('excel.png'))
        bc.setIconSize(QSize(22, 22)); bc.setFixedSize(36, 36)
        bc.setToolTip('CSV 양식 다운로드')
        bc.setStyleSheet('QPushButton{border:1px solid #ccc;border-radius:6px;background:white}'
                         'QPushButton:hover{background:#f0f0f0}')
        bc.clicked.connect(lambda: self._dl_csv(OUT_CSV, '출고_양식.csv'))
        tr.addWidget(bc); tr.addStretch()
        layout.addLayout(tr)
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f'color:{COLOR["border"]};'); layout.addWidget(sep)

        uf = QFrame()
        uf.setStyleSheet(f'background:#f8f9fa;border:2px dashed {COLOR["border"]};border-radius:8px;')
        uf_h = QHBoxLayout(uf); uf_h.setContentsMargins(16, 12, 16, 12)
        self._file_lbl = QLabel('파일 선택 시 일괄 등록')
        self._file_lbl.setStyleSheet('font-size:17px;color:#888;border:none;')
        bu = QPushButton('📂 파일 업로드')
        bu.setStyleSheet('background:#217346;color:white;border:none;padding:8px 16px;border-radius:4px;font-size:17px;')
        bu.clicked.connect(self._upload_outbound)
        uf_h.addWidget(self._file_lbl, 1); uf_h.addWidget(bu)
        layout.addWidget(uf)
        ol = QLabel('── 또는 직접 입력 ──'); ol.setAlignment(Qt.AlignCenter)
        ol.setStyleSheet('font-size:16px;color:#aaa;'); layout.addWidget(ol)

        grid = QGridLayout(); grid.setSpacing(10)
        grid.addWidget(_lbl('부품번호'), 0, 0); grid.addWidget(_lbl('부품명칭'), 0, 1)
        self._part_combo = QComboBox(); self._part_combo.setEditable(True)
        self._part_combo.setStyleSheet(_field())
        for p in self._parts:
            self._part_combo.addItem(p.get('part_no', ''), userData=p)
        self._part_combo.currentIndexChanged.connect(self._on_part)
        grid.addWidget(self._part_combo, 1, 0)
        self._name = QLineEdit(); self._name.setReadOnly(True); self._name.setStyleSheet(_ro())
        grid.addWidget(self._name, 1, 1)
        grid.addWidget(_lbl('지역'), 2, 0); grid.addWidget(_lbl('날짜'), 2, 1)
        self._region = QComboBox(); self._region.addItems(REGIONS)
        self._region.setStyleSheet(_field()); grid.addWidget(self._region, 3, 0)
        self._date = QDateEdit(QDate.currentDate()); self._date.setCalendarPopup(True)
        self._date.setDisplayFormat('yyyy-MM-dd'); self._date.setStyleSheet(_field())
        grid.addWidget(self._date, 3, 1)
        grid.addWidget(_lbl('재고 수량'), 4, 0); grid.addWidget(_lbl('출고 수량'), 4, 1)
        self._stock = QLineEdit('0'); self._stock.setReadOnly(True)
        self._stock.setStyleSheet(_ro()); grid.addWidget(self._stock, 5, 0)
        self._qty = QSpinBox(); self._qty.setRange(1, 9999)
        self._qty.setStyleSheet(_field()); grid.addWidget(self._qty, 5, 1)
        grid.addWidget(_lbl('담당 정비사'), 6, 0, 1, 2)
        self._tech = QLineEdit(); self._tech.setStyleSheet(_field())
        grid.addWidget(self._tech, 7, 0, 1, 2)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        btns = QHBoxLayout(); btns.addStretch()
        ok = _btn('✓ 등록'); cancel = _btn('X 닫기', False)
        ok.clicked.connect(self._on_ok); cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        layout.addLayout(btns)
        self._on_part(0)

    def _on_part(self, idx):
        p = self._part_combo.itemData(idx)
        if p:
            self._name.setText(p.get('name', ''))
            self._stock.setText(str(p.get('qty', 0)))

    def _dl_csv(self, cols, fname):
        f, _ = QFileDialog.getSaveFileName(self, 'CSV 양식 다운로드', fname, 'CSV (*.csv)')
        if not f: return
        try:
            pd.DataFrame(columns=cols).to_csv(f, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, 'CSV 양식', f'양식 저장 완료.\n열: {", ".join(cols)}')
        except Exception as e: QMessageBox.critical(self, '실패', str(e))

    def _upload_outbound(self):
        f, _ = QFileDialog.getOpenFileName(self, '출고 파일 업로드', '',
            'Excel/CSV (*.xlsx *.xls *.csv);;All (*)')
        if not f: return
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.endswith('.csv') else pd.read_excel(f)
        except Exception as e: QMessageBox.critical(self, '실패', str(e)); return
        df.rename(columns={'부품번호': 'part_no', '출고수량': 'qty',
            '지역': 'region', '담당정비사': 'technician', '날짜': 'date'}, inplace=True)
        pmap = {p.get('part_no', ''): p for p in self._parts}
        recs = []
        for _, r in df.iterrows():
            pno = str(r.get('part_no', '')).strip()
            p = pmap.get(pno, {})
            if pno:
                recs.append({'part_id': p.get('part_id'), 'part_no': pno,
                    'name': p.get('name', ''), 'qty': int(r.get('qty', 0) or 0),
                    'region': str(r.get('region', '청주')).strip(),
                    'technician': str(r.get('technician', '')).strip(),
                    'date': str(r.get('date', '')).strip(),
                    'remain': p.get('qty', 0), 'aircraft_db_id': None, 'maint_type': ''})
        if not recs: QMessageBox.warning(self, '실패', '유효한 데이터 없음'); return
        self._uploaded_data = recs
        self._file_lbl.setText(f'✅ {len(recs)}건 로드 완료')
        self._file_lbl.setStyleSheet('font-size:17px;color:#155724;font-weight:bold;border:none;')

    def _on_ok(self):
        if self._uploaded_data: self.accept(); return
        if not self._part_combo.currentText().strip():
            QMessageBox.warning(self, '오류', '부품번호를 선택하세요.'); return
        if not self._tech.text().strip():
            QMessageBox.warning(self, '오류', '담당 정비사를 입력하세요.'); return
        self.accept()

    def get_data(self):
        if self._uploaded_data: return self._uploaded_data
        p = self._part_combo.currentData()
        return {'part_id': p.get('part_id') if p else None,
                'part_no': self._part_combo.currentText(), 'name': self._name.text(),
                'region': self._region.currentText(),
                'date': self._date.date().toString('yyyy-MM-dd'),
                'qty': self._qty.value(), 'remain': int(self._stock.text() or 0),
                'technician': self._tech.text().strip(),
                'aircraft_db_id': None, 'maint_type': ''}