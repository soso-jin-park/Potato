"""
styles.py
QSS 스타일시트 — 글자 크게 키운 버전
기본: 20px / 테이블: 18px / 헤더: 20px / 카드헤더: 22px
"""

COLOR = {
    'primary':   '#10298E',
    'secondary': '#2e6da4',
    'accent':    '#4a90d9',
    'green':     '#28a745',
    'orange':    '#fd7e14',
    'red':       '#dc3545',
    'border':    '#d0d7e2',
    'text':      '#000000',
    'muted':     '#A6A6A6',
    'card_bg':   '#ffffff',
    'bg':        '#f0f4f8',
}

MAIN_QSS = f"""
QWidget {{
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
    font-size: 22px;
    color: {COLOR['text']};
    background: {COLOR['bg']};
}}

/* 헤더 바 */
#headerBar {{
    background: white;
    border-bottom: 1px solid {COLOR['border']};
    min-height: 110px;
    max-height: 110px;
}}

#headerBar QLabel {{
    color: {COLOR['text']};
    background: transparent;
    font-size: 20px;
}}

#headerToggle {{
    background: transparent;
    color: {COLOR['primary']};
    border: none;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 32px;
}}
#headerToggle:hover {{ background: {COLOR['bg']}; }}

#headerIconBtn {{
    background: transparent;
    color: {COLOR['primary']};
    border: none;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 30px;
}}
#headerIconBtn:hover {{ background: {COLOR['bg']}; }}

/* 사이드바 */
#sidebar {{
    background: white;
    border-right: 1px solid {COLOR['border']};
    min-width: 300px;
    max-width: 300px;
}}

/* 카드 */
#card {{
    background: white;
    border: 1px solid {COLOR['border']};
    border-radius: 8px;
}}

/* 카드 헤더 (네이비) */
#cardHeader {{
    background: {COLOR['primary']};
    color: white;
    padding: 12px 18px;
    min-height: 64px;
    font-weight: bold;
    font-size: 24px;
    border-radius: 8px 8px 0 0;
}}

#cardHeader QLabel {{
    color: white;
    background: transparent;
    font-weight: bold;
    font-size: 24px;
}}

#cardHeader QPushButton {{
    background: transparent;
    color: white;
    border: none;
    font-size: 26px;
    padding: 2px 8px;
    border-radius: 4px;
}}
#cardHeader QPushButton:hover {{ background: rgba(255,255,255,0.2); }}

/* 툴바 */
#toolbar {{
    background: #fafbfc;
    border-bottom: 1px solid {COLOR['border']};
    padding: 10px 12px;
}}

/* 탭 버튼 */
QPushButton.tab-btn {{
    padding: 8px 18px;
    border: 1px solid {COLOR['border']};
    background: {COLOR['bg']};
    border-radius: 4px;
    font-size: 18px;
}}
QPushButton.tab-btn:hover,
QPushButton.tab-btn[active="true"] {{
    background: {COLOR['primary']};
    color: white;
    border-color: {COLOR['primary']};
}}

/* 검색 입력 */
QLineEdit#searchInput {{
    padding: 8px 14px;
    border: 1px solid {COLOR['border']};
    border-radius: 4px;
    font-size: 20px;
    background: white;
    min-width: 200px;
}}
QLineEdit#searchInput:focus {{ border-color: {COLOR['accent']}; }}

/* 콤보박스 */
QComboBox {{
    padding: 8px 14px;
    border: 1px solid {COLOR['border']};
    border-radius: 4px;
    font-size: 20px;
    background: white;
}}
QComboBox QAbstractItemView {{
    font-size: 20px;
}}

/* + 버튼 */
QPushButton#btnAdd {{
    background: {COLOR['primary']};
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 24px;
    min-width: 40px;
    max-width: 40px;
    min-height: 40px;
    max-height: 40px;
}}
QPushButton#btnAdd:hover {{ background: {COLOR['secondary']}; }}

/* 테이블 */
QTableWidget {{
    border: none;
    background: white;
    gridline-color: #eeeeee;
    font-size: 20px;
    selection-background-color: transparent;
}}

QTableWidget::item {{
    padding: 12px 14px;
    border-bottom: 1px solid #eeeeee;
    color: {COLOR['text']};
    /* background는 지정 안 함 → setBackground()가 직접 제어 */
}}

QTableWidget::item:hover {{
    background: #f0f5ff;
    color: {COLOR['text']};
}}

QTableWidget::item:selected {{
    background: #c8d8f8;
    color: {COLOR['text']};
}}

/* 점선 포커스 박스 제거 */
QTableWidget::item:focus {{
    outline: none;
    border: none;
}}
QTableWidget:focus {{
    outline: none;
}}

/* 안전재고 발주필요 테이블 */
#orderTbl::item {{
    padding: 10px 14px;
    border-bottom: 1px solid #eeeeee;
}}
#orderTbl::item:selected {{
    background: #c8d8f8;
    color: {COLOR['text']};
}}

/* 테이블 컬럼 헤더 */
QHeaderView::section {{
    background: #e8eef5;
    color: {COLOR['primary']};
    font-weight: bold;
    font-size: 22px;
    padding: 14px 14px;
    border: none;
    border-right: 1px solid {COLOR['border']};
    border-bottom: 2px solid {COLOR['border']};
}}

/* 스크롤바 */
QScrollBar:vertical {{
    width: 10px;
    background: #f1f1f1;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: #c1c1c1;
    border-radius: 5px;
    min-height: 28px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* 뒤로가기 버튼 */
QPushButton#btnBack {{
    background: {COLOR['bg']};
    border: 1px solid {COLOR['border']};
    border-radius: 18px;
    font-size: 22px;
    color: {COLOR['primary']};
    min-width: 38px;
    max-width: 38px;
    min-height: 38px;
    max-height: 38px;
}}
QPushButton#btnBack:hover {{
    background: {COLOR['primary']};
    color: white;
}}

/* 다이얼로그 */
QDialog {{
    font-size: 20px;
}}
QDialog QLabel {{
    font-size: 20px;
}}
QDialog QLineEdit, QDialog QSpinBox, QDialog QDoubleSpinBox,
QDialog QComboBox, QDialog QDateEdit, QDialog QTextEdit {{
    font-size: 18px;
    padding: 6px 10px;
}}
QMessageBox {{
    font-size: 18px;
}}

/* 포커스 점선 제거 */
QAbstractItemView::item:focus {{
    outline: none;
    border: none;
}}
QTableView::item:focus {{
    outline: none;
    border: none;
}}

/* 일반 버튼 (페이지 내 등록/삭제 등) */
QPushButton {{
    font-size: 20px;
}}
"""