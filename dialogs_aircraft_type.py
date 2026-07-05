"""
dialogs_aircraft_type.py
AircraftTypeDialog — 기종 등록 팝업
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

BASE_DIR = Path(__file__).resolve().parent


def _res(f): return str(BASE_DIR / f)


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

class AircraftTypeDialog(QDialog):
    TYPE_CSV = ['부품번호', '부품명칭', '정비종류', '수량']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('기종 등록')
        self.setMinimumWidth(780); self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setSpacing(14); layout.setContentsMargins(20, 20, 20, 20)

        # 타이틀 + CSV 아이콘
        tr = QHBoxLayout()
        t = QLabel('기종 등록')
        t.setFont(QFont('', 18, QFont.Bold))
        t.setStyleSheet(f'color:{COLOR["primary"]};')
        tr.addWidget(t)
        bc = QPushButton(); bc.setIcon(QIcon('excel.png'))
        bc.setIconSize(QSize(22, 22)); bc.setFixedSize(36, 36)
        bc.setToolTip('CSV 양식 다운로드')
        bc.setStyleSheet(
            'QPushButton{border:1px solid #ccc;border-radius:6px;background:white}'
            'QPushButton:hover{background:#f0f0f0}')
        bc.clicked.connect(self._download_csv)
        tr.addWidget(bc); tr.addStretch()
        layout.addLayout(tr)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f'color:{COLOR["border"]};')
        layout.addWidget(sep)

        # ── 파일 업로드 영역 ──
        uf = QFrame()
        uf.setStyleSheet(
            f'background:#f8f9fa;border:2px dashed {COLOR["border"]};'
            f'border-radius:8px;')
        uf_h = QHBoxLayout(uf); uf_h.setContentsMargins(16, 12, 16, 12)
        self._file_lbl = QLabel('파일 선택 시 테이블에 자동 채움')
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

        # ── 기종 ──
        layout.addWidget(_lbl('기종'))
        self._type = QLineEdit(); self._type.setStyleSheet(_field())
        layout.addWidget(self._type)

        # ── 정비 종류 ──
        layout.addWidget(_lbl('정비 종류'))
        mr = QHBoxLayout()
        self._maint_input = QLineEdit(); self._maint_input.setStyleSheet(_field())
        bam = QPushButton('+'); bam.setFixedSize(38, 38)
        bam.setStyleSheet(
            f'background:{COLOR["primary"]};color:white;border:none;'
            f'border-radius:4px;font-size:20px;')
        bam.clicked.connect(self._add_maint)
        mr.addWidget(self._maint_input); mr.addWidget(bam)
        layout.addLayout(mr)

        self._maint_tags = QWidget()
        self._maint_tags_layout = QHBoxLayout(self._maint_tags)
        self._maint_tags_layout.setContentsMargins(0, 0, 0, 0)
        self._maint_tags_layout.addStretch()
        layout.addWidget(self._maint_tags)
        self._maint_list = []

        # ── 정비 종류별 정비 부품 ──
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
        ph_lbl = QLabel('정비 종류별 정비 부품')
        ph_lbl.setStyleSheet('color:white;font-size:18px;font-weight:bold;border:none;')
        ph_h.addWidget(ph_lbl)
        ph_h.addStretch()
        bar = QPushButton('+ 행 추가')
        bar.setStyleSheet(
            'background:rgba(255,255,255,0.2);color:white;border:1px solid rgba(255,255,255,0.4);'
            'border-radius:4px;padding:4px 14px;font-size:16px;')
        bar.clicked.connect(self._add_parts_row)
        ph_h.addWidget(bar)
        pf_v.addWidget(ph_bar)

        self._parts_tbl = QTableWidget()
        self._parts_tbl.setColumnCount(5)
        self._parts_tbl.setHorizontalHeaderLabels(
            ['부품번호', '부품명칭', '정비종류', '수량', ''])
        self._parts_tbl.setMinimumHeight(200)
        self._parts_tbl.verticalHeader().setVisible(False)
        self._parts_tbl.verticalHeader().setDefaultSectionSize(52)
        self._parts_tbl.setEditTriggers(QTableWidget.AllEditTriggers)
        hdr = self._parts_tbl.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.Fixed)
        self._parts_tbl.setColumnWidth(0, 180)
        self._parts_tbl.setColumnWidth(2, 180)
        self._parts_tbl.setColumnWidth(3, 80)
        self._parts_tbl.setColumnWidth(4, 60)
        self._parts_tbl.setStyleSheet(
            'QTableWidget{font-size:19px;border:none;}'
            'QHeaderView::section{font-size:18px;padding:10px 8px;'
            f'background:#e8eef5;color:{COLOR["primary"]};font-weight:bold;'
            f'border:none;border-right:1px solid {COLOR["border"]};'
            f'border-bottom:2px solid {COLOR["border"]};}}')
        self._add_parts_row()
        pf_v.addWidget(self._parts_tbl, 1)
        layout.addWidget(parts_frame, 1)

        btns = QHBoxLayout(); btns.addStretch()
        ok = _btn('✓ 등록'); cancel = _btn('X 닫기', False)
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        layout.addLayout(btns)

    def _download_csv(self):
        f, _ = QFileDialog.getSaveFileName(
            self, 'CSV 양식 다운로드', '기종등록_부품양식.csv', 'CSV (*.csv)')
        if not f: return
        try:
            pd.DataFrame(columns=self.TYPE_CSV).to_csv(
                f, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, 'CSV 양식',
                f'양식 저장 완료.\n열: {", ".join(self.TYPE_CSV)}')
        except Exception as e: QMessageBox.critical(self, '실패', str(e))

    def _upload_file(self):
        f, _ = QFileDialog.getOpenFileName(self, '부품 파일 업로드', '',
            'Excel/CSV (*.xlsx *.xls *.csv);;All (*)')
        if not f: return
        try:
            df = (pd.read_csv(f, encoding='utf-8-sig')
                  if f.endswith('.csv') else pd.read_excel(f))
        except Exception as e:
            QMessageBox.critical(self, '실패', str(e)); return
        df.rename(columns={'부품번호': 'part_no', '부품명칭': 'name',
                           '정비종류': 'maint_type', '수량': 'qty'}, inplace=True)
        self._parts_tbl.setRowCount(0)
        cnt = 0
        for _, r in df.iterrows():
            pno = str(r.get('part_no', '')).strip()
            if not pno: continue
            row = self._parts_tbl.rowCount()
            self._parts_tbl.insertRow(row)
            self._parts_tbl.setRowHeight(row, 52)
            self._parts_tbl.setItem(row, 0, QTableWidgetItem(pno))
            self._parts_tbl.setItem(row, 1,
                QTableWidgetItem(str(r.get('name', '')).strip()))
            self._parts_tbl.setItem(row, 2,
                QTableWidgetItem(str(r.get('maint_type', '')).strip()))
            qty = QSpinBox(); qty.setRange(1, 99); qty.setMinimumHeight(44)
            qty.setStyleSheet('font-size:18px; padding:4px;')
            qty.setValue(int(r.get('qty', 1) or 1))
            self._parts_tbl.setCellWidget(row, 3, qty)
            bd = QPushButton('−'); bd.setMinimumHeight(44)
            bd.setStyleSheet(
                f'background:{COLOR["red"]};color:white;border:none;'
                f'border-radius:3px;font-size:18px;')
            bd.clicked.connect(lambda _, rr=row: self._parts_tbl.removeRow(rr))
            self._parts_tbl.setCellWidget(row, 4, bd)
            cnt += 1
        self._file_lbl.setText(f'✅ {cnt}건 로드 완료')
        self._file_lbl.setStyleSheet(
            'font-size:17px;color:#155724;font-weight:bold;border:none;')

    def _add_parts_row(self):
        row = self._parts_tbl.rowCount()
        self._parts_tbl.insertRow(row)
        self._parts_tbl.setRowHeight(row, 52)
        for col in range(3):
            self._parts_tbl.setItem(row, col, QTableWidgetItem(''))
        qty = QSpinBox(); qty.setRange(1, 99); qty.setMinimumHeight(44)
        qty.setStyleSheet('font-size:18px; padding:4px;')
        self._parts_tbl.setCellWidget(row, 3, qty)
        bd = QPushButton('−'); bd.setMinimumHeight(44)
        bd.setStyleSheet(
            f'background:{COLOR["red"]};color:white;border:none;'
            f'border-radius:3px;font-size:18px;')
        bd.clicked.connect(lambda _, r=row: self._parts_tbl.removeRow(r))
        self._parts_tbl.setCellWidget(row, 4, bd)

    def _add_maint(self):
        text = self._maint_input.text().strip()
        if not text or text in self._maint_list: return
        self._maint_list.append(text)
        tag = QLabel(text)
        tag.setStyleSheet(
            f'background:#e8f0fb;color:{COLOR["primary"]};border-radius:4px;'
            f'padding:4px 10px;font-size:15px;border:1px solid {COLOR["accent"]};')
        self._maint_tags_layout.insertWidget(
            self._maint_tags_layout.count() - 1, tag)
        self._maint_input.clear()


class AircraftEditDialog(QDialog):
    def __init__(self, aircraft, parent=None):
        super().__init__(parent)
        self._ac = aircraft
        self.setWindowTitle('기체 수정')
        self.setFixedWidth(560); self.setModal(True)
        ro = (f'border:1px solid {COLOR["border"]};border-radius:4px;'
              f'padding:6px 10px;font-size:20px;'
              f'background:#f0f4f8;color:{COLOR["muted"]};')