# api.py
from database import (
    db_fetch_parts,
    db_insert_part,
    db_update_part,
    db_delete_parts,
    db_fetch_aircraft_status,
    db_fetch_aircraft_detail,
    db_fetch_inbound,
    db_fetch_outbound,
    db_insert_inbound,
    db_insert_outbound,
    db_fetch_maint_history,
    db_insert_maint_history,
    db_delete_maint_history,
    db_fetch_alarms,
    db_update_safety_stock,
    db_fetch_users,
    db_update_aircraft,        # 추가 
    db_fetch_maint_schedule,   # 추가
    db_insert_maint_schedule,  # 추가 
    db_update_maint_schedule,  # 추가
    db_delete_maint_schedule,  # 추가
    db_update_maint_history,   # 추가 (수정 필요 시)
)

def fetch_parts() -> list:
    return db_fetch_parts()

def insert_part(part: dict) -> dict:
    return db_insert_part(part)

def update_part(part_id: int, data: dict) -> dict:
    return db_update_part(part_id, data)

def delete_parts(part_ids: list) -> None:
    db_delete_parts(part_ids)

def fetch_aircraft_status() -> list:
    return db_fetch_aircraft_status()

def fetch_aircraft_detail(aircraft_id: str) -> dict:
    return db_fetch_aircraft_detail(aircraft_id)

def fetch_alarms() -> list:
    return db_fetch_alarms()

def fetch_inbound() -> list:
    return db_fetch_inbound()

def insert_inbound(record: dict) -> dict:
    return db_insert_inbound(record)

def fetch_outbound() -> list:
    return db_fetch_outbound()

def insert_outbound(record: dict) -> dict:
    return db_insert_outbound(record)

def fetch_maint_history() -> list:
    return db_fetch_maint_history()

def insert_maint_history(record: dict) -> dict:
    return db_insert_maint_history(record)

def delete_maint_history(ids: list) -> None:
    db_delete_maint_history(ids)

def update_maint_history(history_id: int, data: dict) -> dict:
    return db_update_maint_history(history_id, data)

def update_safety_stock(part_id: int, data: dict) -> dict:
    return db_update_safety_stock(part_id, data)

def fetch_users() -> list:
    return db_fetch_users()

def fetch_bom_parts(aircraft_model: str) -> list:
    from database import db_fetch_bom_parts
    return db_fetch_bom_parts(aircraft_model)

def update_aircraft(aircraft_id: int, data: dict) -> dict:
    return db_update_aircraft(aircraft_id, data)

def fetch_maint_schedule() -> list:
    return db_fetch_maint_schedule()

def insert_maint_schedule(schedule: dict) -> dict:  
    return db_insert_maint_schedule(schedule)

def update_maint_schedule(schedule_id: int, data: dict) -> dict:
    return db_update_maint_schedule(schedule_id, data)

def delete_maint_schedule(ids: list) -> None:
    db_delete_maint_schedule(ids)

# 수정 팝업 있을 경우에만 필요
def update_maint_history(history_id: int, data: dict) -> dict:
    return db_update_maint_history(history_id, data)