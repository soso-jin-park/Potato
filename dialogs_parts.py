"""
dialogs_parts.py - 신규 부품 등록 / 부품 수정
CSV 양식 다운로드 + Excel/CSV 파일 업로드 지원
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QDialog, QGridLayout, QLineEdit, QComboBox, QSpinBox,
    QMessageBox, QFileDialog, QWidget
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
import pandas as pd
from styles import COLOR

AC_TYPES  = ['DA-40NG', 'DA-42NG']
LOCATIONS = ['청주', '무안']
CSV_COLS  = ['부품번호', '부품명칭', '적용기종', '보관위치', '초기재고수량', '안전재고수량']

def _btn(label, primary=True):
    bg = COLOR['primary'] if primary else '#f0f4f8'
    fg = 'white' if primary else COLOR['text']
    b = QPushButton(label)
    b.setStyleSheet(
        f'background:{bg}; color:{fg}; border:1px solid {COLOR["border"]};'
        f'padding:8px 20px; border-radius:4px; font-size:21px;')
    return b

def _field_style():
    return (f'border:1px solid {COLOR["border"]}; border-radius:4px;'
            f'padding:6px 10px; font-size:20px; background:white;')

def _ro_style():
    return (f'border:1px solid {COLOR["border"]}; border-radius:4px;'
            f'padding:6px 10px; font-size:20px;'
            f'background:#f0f4f8; color:{COLOR["muted"]};')

def _lbl(text):
    l = QLabel(text)
    l.setStyleSheet(f'font-size:20px; color:{COLOR["text"]};')
    return l


class PartDialog(QDialog):
    def __init__(self, part=None, parent=None):
        super().__init__(parent)
        self._edit = part is not None
        self._part = part or {}
        self._uploaded_data = None
        self.setWindowTitle('부품 수정' if self._edit else '신규 부품 등록')
        self.setMinimumWidth(680); self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # 타이틀 + CSV 아이콘
        title_row = QHBoxLayout()
        t = QLabel('부품 수정' if self._edit else '신규 부품 등록')
        t.setFont(QFont('', 18, QFont.Bold))
        t.setStyleSheet(f'color:{COLOR["primary"]};')
        title_row.addWidget(t)
        if not self._edit:
            btn_csv = QPushButton()
            btn_csv.setIcon(QIcon('excel.png'))
            btn_csv.setIconSize(QSize(22, 22))
            btn_csv.setFixedSize(36, 36)
            btn_csv.setToolTip('CSV 양식 다운로드')
            btn_csv.setStyleSheet(
                'QPushButton{border:1px solid #ccc;border-radius:6px;background:white}'
                'QPushButton:hover{background:#f0f0f0}')
            btn_csv.clicked.connect(self._download_csv)
            title_row.addWidget(btn_csv)
        title_row.addStretch()
        layout.addLayout(title_row)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f'color:{COLOR["border"]};')
        layout.addWidget(sep)

        # 파일 업로드 (신규만)
        if not self._edit:
            uf = QFrame()
            uf.setStyleSheet(
                f'background:#f8f9fa;border:2px dashed {COLOR["border"]};border-radius:8px;')
            uf_h = QHBoxLayout(uf)
            uf_h.setContentsMargins(16, 12, 16, 12)
            self._file_lbl = QLabel('파일 선택 시 일괄 등록')
            self._file_lbl.setStyleSheet('font-size:17px;color:#888;border:none;')
            btn_up = QPushButton('📂 파일 업로드')
            btn_up.setStyleSheet(
                'background:#217346;color:white;border:none;'
                'padding:8px 16px;border-radius:4px;font-size:17px;')
            btn_up.clicked.connect(self._upload_file)
            uf_h.addWidget(self._file_lbl, 1)
            uf_h.addWidget(btn_up)
            layout.addWidget(uf)
            or_lbl = QLabel('── 또는 직접 입력 ──')
            or_lbl.setAlignment(Qt.AlignCenter)
            or_lbl.setStyleSheet('font-size:16px;color:#aaa;')
            layout.addWidget(or_lbl)

        if self._edit:
            layout.addLayout(self._build_edit_form())
        else:
            layout.addLayout(self._build_new_form())

        btns = QHBoxLayout(); btns.addStretch()
        if self._edit:
            btn_ok = _btn('✓ 저장', True)
            btn_cancel = _btn('X 저장 후 닫기', False)
            btn_ok.clicked.connect(self._on_save_keep)
            btn_cancel.clicked.connect(self._on_ok)
        else:
            btn_ok = _btn('✓ 등록', True)
            btn_cancel = _btn('X 닫기', False)
            btn_ok.clicked.connect(self._on_ok)
            btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok); btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def _build_new_form(self):
        grid = QGridLayout(); grid.setSpacing(10)
        grid.addWidget(_lbl('부품번호(P/N)'), 0, 0)
        self._pn = QLineEdit(); self._pn.setStyleSheet(_field_style())
        grid.addWidget(self._pn, 1, 0)
        grid.addWidget(_lbl('부품명칭'), 0, 1)
        self._name = QLineEdit(); self._name.setStyleSheet(_field_style())
        grid.addWidget(self._name, 1, 1)
        grid.addWidget(_lbl('적용 기종'), 2, 0)
        self._ac_combo = QComboBox(); self._ac_combo.addItems(AC_TYPES)
        self._ac_combo.setStyleSheet(_field_style())
        grid.addWidget(self._ac_combo, 3, 0)
        grid.addWidget(_lbl('보관 위치'), 2, 1)
        self._loc = QLineEdit(); self._loc.setStyleSheet(_field_style())
        self._loc.setPlaceholderText('예: 청주')
        grid.addWidget(self._loc, 3, 1)
        grid.addWidget(_lbl('초기 재고 수량'), 4, 0)
        self._qty = QSpinBox(); self._qty.setRange(0, 9999)
        self._qty.setStyleSheet(_field_style())
        grid.addWidget(self._qty, 5, 0)
        grid.addWidget(_lbl('안전재고 수량'), 4, 1)
        self._safe_qty = QSpinBox(); self._safe_qty.setRange(0, 9999)
        self._safe_qty.setStyleSheet(_field_style())
        grid.addWidget(self._safe_qty, 5, 1)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)
        return grid

    def _build_edit_form(self):
        v = QVBoxLayout(); v.setSpacing(8)
        v.addWidget(_lbl('부품번호(P/N)'))
        self._pn = QLineEdit(self._part.get('part_no', ''))
        self._pn.setReadOnly(True); self._pn.setStyleSheet(_ro_style())
        v.addWidget(self._pn)
        v.addWidget(_lbl('부품명칭'))
        self._name = QLineEdit(self._part.get('name', ''))
        self._name.setStyleSheet(_field_style())
        v.addWidget(self._name)
        v.addWidget(_lbl('적용 기종'))
        self._ac_combo = QComboBox(); self._ac_combo.addItems(AC_TYPES)
        ac_id = self._part.get('aircraft_id')
        if ac_id == 2: self._ac_combo.setCurrentText('DA-40NG')
        elif ac_id == 3: self._ac_combo.setCurrentText('DA-42NG')
        self._ac_combo.setStyleSheet(_field_style())
        v.addWidget(self._ac_combo)
        v.addWidget(_lbl('보관 위치'))
        self._loc = QLineEdit(self._part.get('location', '').split('/')[0])
        self._loc.setStyleSheet(_field_style())
        v.addWidget(self._loc)
        return v

    def _download_csv(self):
        f, _ = QFileDialog.getSaveFileName(
            self, 'CSV 양식 다운로드', '부품등록_양식.csv',
            'CSV Files (*.csv);;All Files (*)')
        if not f: return
        try:
            pd.DataFrame(columns=CSV_COLS).to_csv(f, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, 'CSV 양식', f'양식이 저장되었습니다.\n열: {", ".join(CSV_COLS)}')
        except Exception as e:
            QMessageBox.critical(self, '실패', str(e))

    def _upload_file(self):
        f, _ = QFileDialog.getOpenFileName(
            self, '부품 파일 업로드', '',
            'Excel/CSV (*.xlsx *.xls *.csv);;All Files (*)')
        if not f: return
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.endswith('.csv') else pd.read_excel(f)
        except Exception as e:
            QMessageBox.critical(self, '파일 읽기 실패', str(e)); return
        cmap = {'부품번호': 'part_no', '부품명칭': 'name', '적용기종': 'ac_type',
                '보관위치': 'location', '초기재고수량': 'qty', '안전재고수량': 'safe_qty'}
        df.rename(columns=cmap, inplace=True)
        recs = []
        for _, r in df.iterrows():
            ac = str(r.get('ac_type', 'DA-40NG')).strip()
            ac_id = 3 if '42' in ac else 2
            rec = {'part_number': str(r.get('part_no', '')).strip(),
                   'part_no': str(r.get('part_no', '')).strip(),
                   'name': str(r.get('name', '')).strip(),
                   'aircraft_id': ac_id,
                   'location': str(r.get('location', '청주')).strip(),
                   'qty': int(r.get('qty', 0) or 0),
                   'safe_qty': int(r.get('safe_qty', 0) or 0)}
            if rec['part_no']: recs.append(rec)
        if not recs:
            QMessageBox.warning(self, '실패', '유효한 데이터가 없습니다.'); return
        self._uploaded_data = recs
        self._file_lbl.setText(f'✅ {len(recs)}건 로드 완료')
        self._file_lbl.setStyleSheet('font-size:17px;color:#155724;font-weight:bold;border:none;')

    def _on_save_keep(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, '입력 오류', '부품명칭을 입력하세요.'); return
        self.done(2)

    def _on_ok(self):
        if self._uploaded_data: self.accept(); return
        if not self._pn.text().strip():
            QMessageBox.warning(self, '입력 오류', '부품번호를 입력하세요.'); return
        if not self._name.text().strip():
            QMessageBox.warning(self, '입력 오류', '부품명칭을 입력하세요.'); return
        self.accept()

    def get_data(self):
        if self._uploaded_data: return self._uploaded_data
        ac_text = self._ac_combo.currentText()
        ac_db_id = 2 if ac_text == 'DA-40NG' else 3
        d = {'part_number': self._pn.text().strip(), 'part_no': self._pn.text().strip(),
             'name': self._name.text().strip(), 'aircraft_id': ac_db_id,
             'location': self._loc.text().strip()}
        if not self._edit:
            d['qty'] = self._qty.value(); d['safe_qty'] = self._safe_qty.value()
        return d