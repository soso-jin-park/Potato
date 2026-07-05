"""
dummy_data.py
개발/테스트용 더미 데이터 모음
실제 DB 연동 시 이 파일은 사용하지 않음 (api.py의 USE_DUMMY = False)

포함 내용:
  - 공통 상수 (MAINT_TYPES, REGIONS)
  - PARTS        : 부품 목록
  - AIRCRAFT     : 항공기 현황
  - ALARMS       : 알람 목록
  - INBOUND      : 입고 이력
  - OUTBOUND     : 출고 이력
  - MAINT_HISTORY: 정비 이력
"""

# ── 공통 상수 ─────────────────────────────────────────────────────
MAINT_TYPES = [
    '기체 100 HRS', '기체 200 HRS', '기체 1000 HRS',
    "ENG' 100 HRS", "ENG' 300 HRS", "ENG' 1000 HRS",
    'MSB',
]

REGIONS = ['청주', '무안', '제주', '서울', '부산']

AIRCRAFT_TYPES = ['DA-40 NG', 'DA-42 NG']

# ── 부품 목록 ─────────────────────────────────────────────────────
PARTS = [
    {'id': 1,  'category': '기체', 'aircraft': ['DA-40 NG'],
     'cycle': '항공기 100 HRS', 'part_no': 'WK724-3',
     'name': 'Fuel Filter',              'qty': 3,  'safe_qty': 2,  'location': 'A-1',
     'order_unit': 2, 'lead_time': 21, 'unit_price': 82.5,  'reason': ''},
    {'id': 2,  'category': '기체', 'aircraft': ['DA-40 NG'],
     'cycle': '항공기 100 HRS', 'part_no': 'ORO 375',
     'name': 'Gascolator O-Ring',        'qty': 1,  'safe_qty': 2,  'location': 'A-2',
     'order_unit': 5, 'lead_time': 14, 'unit_price': 12.0,  'reason': ''},
    {'id': 3,  'category': '기체', 'aircraft': ['DA-40 NG'],
     'cycle': '항공기 100 HRS', 'part_no': 'TORRO_50-70_12_W1',
     'name': 'Worm Clamp',               'qty': 6,  'safe_qty': 4,  'location': 'B-3',
     'order_unit': 4, 'lead_time': 10, 'unit_price': 3.5,   'reason': ''},
    {'id': 4,  'category': '기체', 'aircraft': ['DA-40 NG'],
     'cycle': '항공기 100 HRS', 'part_no': 'DIN985-M12-A2',
     'name': 'Nut, Hexagon Self locking', 'qty': 0, 'safe_qty': 2,  'location': 'C-1',
     'order_unit': 10,'lead_time': 7,  'unit_price': 1.2,   'reason': ''},
    {'id': 5,  'category': '기체', 'aircraft': ['DA-40 NG'],
     'cycle': '항공기 200 HRS', 'part_no': 'LN94-20020',
     'name': 'Split Pin',                 'qty': 0, 'safe_qty': 2,  'location': 'C-3',
     'order_unit': 10,'lead_time': 14, 'unit_price': 0.8,   'reason': ''},
    {'id': 6,  'category': '기체', 'aircraft': ['DA-40 NG'],
     'cycle': '항공기 200 HRS', 'part_no': 'RU-1620',
     'name': 'Air Filter',                'qty': 4, 'safe_qty': 2,  'location': 'D-1',
     'order_unit': 2, 'lead_time': 21, 'unit_price': 55.0,  'reason': ''},
    {'id': 7,  'category': '엔진', 'aircraft': ['DA-40 NG'],
     'cycle': "ENG' 100 HRS", 'part_no': 'Shell HELIX Ultra',
     'name': "Eng' OIL",                  'qty': 24,'safe_qty': 14, 'location': 'F-1',
     'order_unit': 12,'lead_time': 3,  'unit_price': 18.0,  'reason': ''},
    {'id': 8,  'category': '엔진', 'aircraft': ['DA-40 NG'],
     'cycle': "ENG' 100 HRS", 'part_no': 'E4A-52-300-KIT',
     'name': "Eng' Oil Filter",            'qty': 1, 'safe_qty': 2,  'location': 'D-3',
     'order_unit': 2, 'lead_time': 30, 'unit_price': 145.0, 'reason': ''},
    {'id': 9,  'category': '엔진', 'aircraft': ['DA-40 NG'],
     'cycle': "ENG' 300 HRS", 'part_no': 'E4A-70-000-806',
     'name': 'Gearbox Oil Filter',         'qty': 3, 'safe_qty': 2,  'location': 'D-5',
     'order_unit': 2, 'lead_time': 30, 'unit_price': 98.0,  'reason': ''},
    {'id': 10, 'category': '기체', 'aircraft': ['DA-42 NG'],
     'cycle': '항공기 100 HRS', 'part_no': 'DA42-WK724-3',
     'name': 'Fuel Filter (42)',           'qty': 2, 'safe_qty': 2,  'location': 'G-1',
     'order_unit': 2, 'lead_time': 21, 'unit_price': 90.0,  'reason': ''},
    {'id': 11, 'category': '엔진', 'aircraft': ['DA-42 NG'],
     'cycle': "ENG' 100 HRS", 'part_no': 'DA42-E4A-52',
     'name': "Eng' Oil Filter (42)",       'qty': 0, 'safe_qty': 2,  'location': 'G-2',
     'order_unit': 2, 'lead_time': 30, 'unit_price': 155.0, 'reason': ''},
]

# ── 항공기 현황 ───────────────────────────────────────────────────
AIRCRAFT = [
    {'id': 'HL1176', 'type': 'DA-40 NG', 'pct': 79,
     'total_hours': 5978, 'next_inspection': 79, 'cycle_hours': 100,
     'location': '청주', 'msb_remaining': 450,
     'stock_shortage': [{'name': 'Gascolator O-Ring', 'qty': 1, 'safe_qty': 2}],
     'schedules': [{'label': '기체 주기 정비', 'hours': 79,  'cycle': '항공기 100 HRS'},
                   {'label': '엔진 주기 정비', 'hours': 653, 'cycle': "ENG' 1000 HRS"}]},
    {'id': 'HL1177', 'type': 'DA-40 NG', 'pct': 5,
     'total_hours': 12034, 'next_inspection': 44, 'cycle_hours': 2000,
     'location': '청주', 'msb_remaining': 120,
     'stock_shortage': [{'name': 'Nut, Hexagon', 'qty': 0, 'safe_qty': 2},
                        {'name': 'Split Pin',     'qty': 0, 'safe_qty': 2}],
     'schedules': [{'label': '기체 주기 정비', 'hours': 44,  'cycle': '항공기 2000 HRS'},
                   {'label': '엔진 주기 정비', 'hours': 244, 'cycle': "ENG' 300 HRS"}]},
    {'id': 'HL1178', 'type': 'DA-40 NG', 'pct': 43,
     'total_hours': 3210, 'next_inspection': 43, 'cycle_hours': 100,
     'location': '청주', 'msb_remaining': 300,
     'stock_shortage': [],
     'schedules': [{'label': '기체 주기 정비', 'hours': 43,  'cycle': '항공기 100 HRS'},
                   {'label': '엔진 주기 정비', 'hours': 243, 'cycle': "ENG' 300 HRS"}]},
    {'id': 'HL1179', 'type': 'DA-40 NG', 'pct': 99,
     'total_hours': 1820, 'next_inspection': 198, 'cycle_hours': 200,
     'location': '청주', 'msb_remaining': 600,
     'stock_shortage': [],
     'schedules': [{'label': '기체 주기 정비', 'hours': 198, 'cycle': '항공기 200 HRS'},
                   {'label': '엔진 주기 정비', 'hours': 398, 'cycle': "ENG' 600 HRS"}]},
    {'id': 'HL1252', 'type': 'DA-40 NG', 'pct': 10,
     'total_hours': 4430, 'next_inspection': 10, 'cycle_hours': 100,
     'location': '청주', 'msb_remaining': 80,
     'stock_shortage': [{'name': "Eng' Oil Filter", 'qty': 1, 'safe_qty': 2}],
     'schedules': [{'label': '기체 주기 정비', 'hours': 10,  'cycle': '항공기 100 HRS'},
                   {'label': '엔진 주기 정비', 'hours': 110, 'cycle': "ENG' 100 HRS"}]},
    {'id': 'HL1253', 'type': 'DA-40 NG', 'pct': 79,
     'total_hours': 2100, 'next_inspection': 79, 'cycle_hours': 100,
     'location': '청주', 'msb_remaining': 550,
     'stock_shortage': [],
     'schedules': [{'label': '기체 주기 정비', 'hours': 79,  'cycle': '항공기 100 HRS'},
                   {'label': '엔진 주기 정비', 'hours': 279, 'cycle': "ENG' 300 HRS"}]},
    {'id': 'HL1254', 'type': 'DA-40 NG', 'pct': 91,
     'total_hours': 980,  'next_inspection': 182, 'cycle_hours': 200,
     'location': '청주', 'msb_remaining': 700,
     'stock_shortage': [],
     'schedules': [{'label': '기체 주기 정비', 'hours': 182, 'cycle': '항공기 200 HRS'},
                   {'label': '엔진 주기 정비', 'hours': 382, 'cycle': "ENG' 600 HRS"}]},
    {'id': 'HL1295', 'type': 'DA-40 NG', 'pct': 5,
     'total_hours': 7450, 'next_inspection': 50, 'cycle_hours': 1000,
     'location': '청주', 'msb_remaining': 200,
     'stock_shortage': [{'name': 'Gascolator O-Ring', 'qty': 1, 'safe_qty': 2}],
     'schedules': [{'label': '기체 주기 정비', 'hours': 50,  'cycle': '항공기 1000 HRS'},
                   {'label': 'MSB 정비',        'hours': 200, 'cycle': 'MSB'}]},
    {'id': 'HL2046', 'type': 'DA-42 NG', 'pct': 76,
     'total_hours': 3293, 'next_inspection': 153, 'cycle_hours': 200,
     'location': '무안', 'msb_remaining': 450,
     'stock_shortage': [{'name': "Eng' Oil Filter (42)", 'qty': 0, 'safe_qty': 2}],
     'schedules': [{'label': '기체 주기 정비', 'hours': 153, 'cycle': '항공기 200 HRS'},
                   {'label': '엔진 주기 정비', 'hours': 353, 'cycle': "ENG' 300 HRS"}]},
]

# ── 알람 목록 ─────────────────────────────────────────────────────
ALARMS = [
    {'id': 1, 'level': 'danger',
     'message': 'HL1177 — 44시간 후 항공기 2000 HRS 점검 필요',
     'stock_info': 'Nut 현재 0개'},
    {'id': 2, 'level': 'danger',
     'message': 'HL1252 — 10시간 후 항공기 100 HRS 점검 필요',
     'stock_info': "Eng' Oil Filter 현재 1개"},
    {'id': 3, 'level': 'warn',
     'message': 'HL1176 — 79시간 후 항공기 100 HRS 점검 필요',
     'stock_info': 'Gascolator O-Ring 현재 1개'},
    {'id': 4, 'level': 'warn',
     'message': 'Split Pin 안전재고 미만 — 구매 필요',
     'stock_info': '현재 0개 / 안전재고 2개'},
    {'id': 5, 'level': 'warn',
     'message': "Eng' Oil Filter (42) 재고 없음 — 구매 필요",
     'stock_info': '현재 0개 / 안전재고 2개'},
]

# ── 입고 이력 ─────────────────────────────────────────────────────
INBOUND = [
    {'id': 1, 'date': '2025-04-10', 'order_no': 'PO-001', 'part_no': 'WK724-3',
     'name': 'Fuel Filter',         'qty': 5, 'unit_price': 82.5,  'rate': 1350, 'note': ''},
    {'id': 2, 'date': '2025-05-02', 'order_no': 'PO-002', 'part_no': 'ORO 375',
     'name': 'Gascolator O-Ring',   'qty': 10,'unit_price': 12.0,  'rate': 1320, 'note': ''},
    {'id': 3, 'date': '2025-05-20', 'order_no': 'PO-003', 'part_no': 'E4A-52-300-KIT',
     'name': "Eng' Oil Filter",     'qty': 3, 'unit_price': 145.0, 'rate': 1340, 'note': '긴급 발주'},
]

# ── 출고 이력 ─────────────────────────────────────────────────────
OUTBOUND = [
    {'id': 1, 'date': '2025-04-15', 'region': '청주', 'aircraft_id': 'HL1176',
     'maint_type': '기체 100 HRS', 'part_no': 'WK724-3',
     'name': 'Fuel Filter',         'qty': 1, 'remain': 3, 'technician': '김철수', 'note': ''},
    {'id': 2, 'date': '2025-05-05', 'region': '청주', 'aircraft_id': 'HL1252',
     'maint_type': "ENG' 100 HRS", 'part_no': 'E4A-52-300-KIT',
     'name': "Eng' Oil Filter",     'qty': 1, 'remain': 0, 'technician': '이영희', 'note': '재고 소진'},
]

# ── 정비 이력 ─────────────────────────────────────────────────────
MAINT_HISTORY = [
    {'id': 1, 'date': '2025-02-10', 'aircraft_id': 'HL1176',
     'maint_type': '기체 100 HRS', 'flight_hrs': 5899,
     'parts': [{'name': 'Fuel Filter', 'qty': 1},
               {'name': 'Gascolator O-Ring', 'qty': 1}],
     'next_plan': 6000, 'technician': '김철수', 'note': ''},
    {'id': 2, 'date': '2025-03-05', 'aircraft_id': 'HL1252',
     'maint_type': "ENG' 100 HRS", 'flight_hrs': 4420,
     'parts': [{'name': "Eng' Oil Filter", 'qty': 1},
               {'name': "Eng' OIL",        'qty': 8}],
     'next_plan': 4520, 'technician': '이영희', 'note': ''},
    {'id': 3, 'date': '2025-04-18', 'aircraft_id': 'HL2046',
     'maint_type': '기체 200 HRS', 'flight_hrs': 3140,
     'parts': [{'name': 'Fuel Filter (42)', 'qty': 1}],
     'next_plan': 3340, 'technician': '박민준', 'note': ''},
]