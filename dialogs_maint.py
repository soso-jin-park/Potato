"""
dialogs_maint.py
정비 이력 등록 팝업 (CSV 양식 다운로드 + 파일 업로드 지원)
주기정비 내용 수정 팝업
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QFileDialog,
    QSpinBox, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QFont, QIcon
import pandas as pd
from styles import COLOR

CSV_COLUMNS = ['기체등록번호', '누적비행시간', '정비종류', '주기',
               '담당자', '날짜', '비고']


def _btn(label, primary=True):
    bg = COLOR['primary'] if primary else '#f0f4f8'
    fg = 'white' if primary else COLOR['text']
    b = QPushButton(label)
    b.setStyleSheet(
        f'background:{bg}; color:{fg}; border:1px solid {COLOR["border"]};'
        f'padding:8px 20px; border-radius:4px; font-size:20px;')
    return b


def _lbl(text):
    l = QLabel(text)
    l.setStyleSheet(f'font-size:19px; color:{COLOR["text"]};')
    return l


def _field():
    return (f'border:1px solid {COLOR["border"]}; border-radius:4px;'
            f'padding:8px 12px; font-size:19px; background:white;')


class MaintHistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('정비 이력 등록')
        self.setMinimumWidth(720)
        self.setMinimumHeight(700)
        self.setModal(True)
        self._uploaded_data = None  # 업로드된 데이터

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        # ── 제목 + CSV 다운로드 아이콘 ──
        title_row = QHBoxLayout()
        t = QLabel('정비 이력 등록')
        t.setFont(QFont('', 20, QFont.Bold))
        t.setStyleSheet(f'color:{COLOR["primary"]};')
        title_row.addWidget(t)

        btn_csv = QPushButton()
        btn_csv.setIcon(QIcon('excel.png'))
        btn_csv.setIconSize(QSize(22, 22))
        btn_csv.setFixedSize(36, 36)
        btn_csv.setToolTip('CSV 양식 다운로드')
        btn_csv.setStyleSheet(
            'QPushButton{border:1px solid #ccc;border-radius:6px;'
            'background:white}'
            'QPushButton:hover{background:#f0f0f0}')
        btn_csv.clicked.connect(self._download_csv)
        title_row.addWidget(btn_csv)
        title_row.addStretch()
        layout.addLayout(title_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f'color:{COLOR["border"]};')
        layout.addWidget(sep)

        # ── 파일 업로드 영역 ──
        upload_frame = QFrame()
        upload_frame.setStyleSheet(
            f'background:#f8f9fa; border:2px dashed {COLOR["border"]};'
            f'border-radius:8px;')
        uf_h = QHBoxLayout(upload_frame)
        uf_h.setContentsMargins(16, 12, 16, 12)
        self._file_lbl = QLabel('파일을 선택하면 일괄 등록됩니다')
        self._file_lbl.setStyleSheet('font-size:17px; color:#888; border:none;')
        btn_upload = QPushButton('📂 파일 업로드')
        btn_upload.setStyleSheet(
            'background:#217346; color:white; border:none;'
            'padding:8px 16px; border-radius:4px; font-size:17px;')
        btn_upload.clicked.connect(self._upload_file)
        uf_h.addWidget(self._file_lbl, 1)
        uf_h.addWidget(btn_upload)
        layout.addWidget(upload_frame)

        # ── 구분선 ──
        or_lbl = QLabel('── 또는 직접 입력 ──')
        or_lbl.setAlignment(Qt.AlignCenter)
        or_lbl.setStyleSheet('font-size:16px; color:#aaa;')
        layout.addWidget(or_lbl)

        # ── 수동 입력 (2열 그리드) ──
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)

        grid.addWidget(_lbl('기종'), 0, 0)
        grid.addWidget(_lbl('정비 종류'), 0, 1)
        self._ac_type = QLineEdit()
        self._ac_type.setPlaceholderText('예: DA-40 NG')
        self._ac_type.setStyleSheet(_field())
        grid.addWidget(self._ac_type, 1, 0)
        self._maint_type = QLineEdit()
        self._maint_type.setPlaceholderText('예: 항공기 100 HRS')
        self._maint_type.setStyleSheet(_field())
        grid.addWidget(self._maint_type, 1, 1)

        grid.addWidget(_lbl('기체 등록번호'), 2, 0)
        grid.addWidget(_lbl('주기'), 2, 1)
        self._ac_reg = QLineEdit()
        self._ac_reg.setPlaceholderText('예: HL1176')
        self._ac_reg.setStyleSheet(_field())
        grid.addWidget(self._ac_reg, 3, 0)
        self._interval = QLineEdit()
        self._interval.setPlaceholderText('예: 100H')
        self._interval.setStyleSheet(_field())
        grid.addWidget(self._interval, 3, 1)

        grid.addWidget(_lbl('담당 정비사'), 4, 0)
        grid.addWidget(_lbl('날짜'), 4, 1)
        self._tech = QLineEdit()
        self._tech.setStyleSheet(_field())
        grid.addWidget(self._tech, 5, 0)
        self._date = QDateEdit(QDate.currentDate())
        self._date.setCalendarPopup(True)
        self._date.setDisplayFormat('yyyy-MM-dd')
        self._date.setStyleSheet(_field())
        grid.addWidget(self._date, 5, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        # ── 교체 부품 ──
        parts_frame = QFrame()
        parts_frame.setStyleSheet(
            f'QFrame{{background:white;border:1px solid {COLOR["border"]};'
            f'border-radius:6px;}}')
        pf_v = QVBoxLayout(parts_frame)
        pf_v.setContentsMargins(0, 0, 0, 0)
        pf_v.setSpacing(0)

        # 섹션 헤더
        ph_bar = QFrame()
        ph_bar.setStyleSheet(
            f'background:{COLOR["primary"]};border-radius:6px 6px 0 0;')
        ph_bar.setFixedHeight(42)
        ph_h = QHBoxLayout(ph_bar)
        ph_h.setContentsMargins(12, 0, 8, 0)
        ph_lbl = QLabel('교체 부품')
        ph_lbl.setStyleSheet('color:white;font-size:18px;font-weight:bold;border:none;')
        ph_h.addWidget(ph_lbl)
        ph_h.addStretch()
        btn_add_row = QPushButton('+ 행 추가')
        btn_add_row.setStyleSheet(
            'background:rgba(255,255,255,0.2);color:white;border:1px solid rgba(255,255,255,0.4);'
            'border-radius:4px;padding:4px 14px;font-size:16px;')
        btn_add_row.clicked.connect(self._add_part_row)
        ph_h.addWidget(btn_add_row)
        pf_v.addWidget(ph_bar)

        self._parts_tbl = QTableWidget()
        self._parts_tbl.setColumnCount(4)
        self._parts_tbl.setHorizontalHeaderLabels(
            ['부품번호', '부품명칭', '수량', ''])
        self._parts_tbl.verticalHeader().setVisible(False)
        self._parts_tbl.verticalHeader().setDefaultSectionSize(52)
        self._parts_tbl.setMinimumHeight(160)
        hdr = self._parts_tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.Fixed)
        self._parts_tbl.setColumnWidth(0, 200)
        self._parts_tbl.setColumnWidth(2, 100)
        self._parts_tbl.setColumnWidth(3, 60)
        self._parts_tbl.setEditTriggers(QTableWidget.AllEditTriggers)
        self._parts_tbl.setStyleSheet(
            'QTableWidget{font-size:19px;border:none;}'
            'QHeaderView::section{font-size:18px;padding:10px 8px;'
            f'background:#e8eef5;color:{COLOR["primary"]};font-weight:bold;'
            f'border:none;border-right:1px solid {COLOR["border"]};'
            f'border-bottom:2px solid {COLOR["border"]};}}')
        pf_v.addWidget(self._parts_tbl, 1)
        layout.addWidget(parts_frame, 1)
        self._add_part_row()

        # ── 버튼 ──
        btns = QHBoxLayout()
        btns.addStretch()
        btn_ok = _btn('✓ 등록', True)
        btn_cancel = _btn('X 닫기', False)
        btn_ok.clicked.connect(self._on_ok)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def _download_csv(self):
        file, _ = QFileDialog.getSaveFileName(
            self, 'CSV 양식 다운로드', '정비이력_양식.csv',
            'CSV Files (*.csv);;All Files (*)')
        if not file:
            return
        try:
            df = pd.DataFrame(columns=CSV_COLUMNS)
            df.to_csv(file, index=False, encoding='utf-8-sig')
            QMessageBox.information(
                self, 'CSV 양식 다운로드',
                f'양식이 저장되었습니다.\n\n'
                f'열: {", ".join(CSV_COLUMNS)}\n\n'
                f'데이터를 채운 뒤 "📂 파일 업로드"로 등록하세요.')
        except Exception as e:
            QMessageBox.critical(self, '실패', str(e))

    def _upload_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, '정비 이력 파일 업로드', '',
            'Excel/CSV (*.xlsx *.xls *.csv);;All Files (*)')
        if not file:
            return
        try:
            if file.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8-sig')
            else:
                df = pd.read_excel(file)
        except Exception as e:
            QMessageBox.critical(self, '파일 읽기 실패', str(e))
            return

        col_map = {'기체등록번호': 'aircraft_id', '누적비행시간': 'flight_hrs',
                   '정비종류': 'maint_type', '주기': 'inspection_interval',
                   '담당자': 'technician', '날짜': 'date', '비고': 'note'}
        df.rename(columns=col_map, inplace=True)

        records = []
        for _, row in df.iterrows():
            rec = {
                'aircraft_id': str(row.get('aircraft_id', '')).strip(),
                'flight_hrs': float(row.get('flight_hrs', 0) or 0),
                'maint_type': str(row.get('maint_type', '')).strip(),
                'inspection_interval': str(
                    row.get('inspection_interval', '')).strip(),
                'technician': str(row.get('technician', '')).strip(),
                'date': str(row.get('date', '')).strip(),
                'note': str(row.get('note', '')).strip()}
            if rec['aircraft_id'] and rec['maint_type']:
                records.append(rec)

        if not records:
            QMessageBox.warning(self, '업로드 실패',
                                '유효한 데이터가 없습니다.\n'
                                '기체등록번호와 정비종류는 필수입니다.')
            return

        self._uploaded_data = records
        self._file_lbl.setText(
            f'✅ {len(records)}건 로드 완료 — "✓ 등록" 클릭 시 저장됩니다')
        self._file_lbl.setStyleSheet(
            'font-size:17px; color:#155724; font-weight:bold; border:none;')

    def _add_part_row(self):
        row = self._parts_tbl.rowCount()
        self._parts_tbl.insertRow(row)
        self._parts_tbl.setRowHeight(row, 52)
        self._parts_tbl.setItem(row, 0, QTableWidgetItem(''))
        self._parts_tbl.setItem(row, 1, QTableWidgetItem(''))
        qty = QSpinBox()
        qty.setRange(1, 99); qty.setMinimumHeight(44)
        qty.setStyleSheet('font-size:18px; padding:4px;')
        self._parts_tbl.setCellWidget(row, 2, qty)
        btn_del = QPushButton('−')
        btn_del.setMinimumHeight(44)
        btn_del.setStyleSheet(
            f'background:{COLOR["red"]}; color:white; border:none;'
            f'border-radius:3px; font-size:18px;')
        btn_del.clicked.connect(lambda _, r=row: self._del_row(r))
        self._parts_tbl.setCellWidget(row, 3, btn_del)

    def _del_row(self, row):
        if self._parts_tbl.rowCount() > 1:
            self._parts_tbl.removeRow(row)

    def _on_ok(self):
        # 파일 업로드된 경우 바로 accept
        if self._uploaded_data:
            self.accept()
            return
        # 수동 입력 검증
        if not self._ac_reg.text().strip():
            QMessageBox.warning(self, '입력 오류', '기체 등록번호를 입력하세요.')
            return
        if not self._tech.text().strip():
            QMessageBox.warning(self, '입력 오류', '담당 정비사를 입력하세요.')
            return
        self.accept()

    def get_data(self):
        """파일 업로드 시 list 반환, 수동 입력 시 dict 반환"""
        if self._uploaded_data:
            return self._uploaded_data
        parts = []
        for row in range(self._parts_tbl.rowCount()):
            pn = self._parts_tbl.item(row, 0)
            name = self._parts_tbl.item(row, 1)
            qty_w = self._parts_tbl.cellWidget(row, 2)
            if pn and pn.text().strip():
                parts.append({'name': name.text() if name else '',
                              'part_id': None,
                              'qty': qty_w.value() if qty_w else 1})
        return {
            'aircraft_id': self._ac_reg.text().strip(),
            'aircraft_db_id': None,
            'maint_type': self._maint_type.text().strip(),
            'inspection_interval': self._interval.text().strip(),
            'date': self._date.date().toString('yyyy-MM-dd'),
            'flight_hrs': 0, 'next_plan': 0,
            'technician': self._tech.text().strip(),
            'parts': parts, 'note': ''}


class MaintScheduleDialog(QDialog):
    """주기정비 현황 더블클릭 수정 팝업"""

    def __init__(self, item_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('주기정비 내용 수정')
        self.setMinimumWidth(640)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        t = QLabel('주기정비 내용 수정')
        t.setFont(QFont('', 20, QFont.Bold))
        t.setStyleSheet(f'color:{COLOR["primary"]};')
        layout.addWidget(t)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f'color:{COLOR["border"]};')
        layout.addWidget(sep)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)

        grid.addWidget(_lbl('부품번호'), 0, 0)
        grid.addWidget(_lbl('부품명칭'), 0, 1)
        self._part_no = QLineEdit(); self._part_no.setStyleSheet(_field())
        self._part_name = QLineEdit(); self._part_name.setStyleSheet(_field())
        grid.addWidget(self._part_no, 1, 0)
        grid.addWidget(self._part_name, 1, 1)

        grid.addWidget(_lbl('재고 수량'), 2, 0)
        grid.addWidget(_lbl('안전재고 수량'), 2, 1)
        self._qty = QSpinBox()
        self._qty.setRange(0, 9999); self._qty.setMinimumHeight(44)
        self._qty.setStyleSheet('font-size:19px; padding:6px;')
        self._safe_qty = QSpinBox()
        self._safe_qty.setRange(0, 9999); self._safe_qty.setMinimumHeight(44)
        self._safe_qty.setStyleSheet('font-size:19px; padding:6px;')
        grid.addWidget(self._qty, 3, 0)
        grid.addWidget(self._safe_qty, 3, 1)

        grid.addWidget(_lbl('정비종류'), 4, 0)
        grid.addWidget(_lbl('주기'), 4, 1)
        self._maint_type = QLineEdit()
        self._maint_type.setPlaceholderText('예: 항공기 100 HRS')
        self._maint_type.setStyleSheet(_field())
        self._interval = QLineEdit()
        self._interval.setPlaceholderText('예: 100H')
        self._interval.setStyleSheet(_field())
        grid.addWidget(self._maint_type, 5, 0)
        grid.addWidget(self._interval, 5, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        if item_data:
            self._part_no.setText(item_data.get('part_no', ''))
            self._part_name.setText(item_data.get('name', ''))
            self._qty.setValue(int(item_data.get('qty', 0) or 0))
            self._safe_qty.setValue(int(item_data.get('safe_qty', 0) or 0))
            self._maint_type.setText(
                item_data.get('maintenance_type', '')
                or item_data.get('inspection_interval', ''))
            self._interval.setText(
                item_data.get('inspection_interval', ''))

        btns = QHBoxLayout()
        btns.addStretch()
        btn_ok = _btn('✓ 저장', True)
        btn_cancel = _btn('✗ 닫기', False)
        btn_ok.clicked.connect(self._on_ok)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def _on_ok(self):
        if not self._part_no.text().strip():
            QMessageBox.warning(self, '입력 오류', '부품번호를 입력하세요.')
            return
        self.accept()

    def get_data(self):
        return {
            'part_no': self._part_no.text().strip(),
            'name': self._part_name.text().strip(),
            'qty': self._qty.value(),
            'safe_qty': self._safe_qty.value(),
            'maintenance_type': self._maint_type.text().strip(),
            'inspection_interval': self._interval.text().strip()}