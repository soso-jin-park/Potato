"""
api.py
DB 함수 래퍼 — database / database_maint / database_schedule 세 파일에서 가져옴
"""
from database import (
    db_fetch_parts, db_insert_part, db_update_part, db_delete_parts,
    db_fetch_aircraft_status, db_fetch_aircraft_detail,
)
from database_maint import (
    db_fetch_inbound, db_insert_inbound,
    db_fetch_outbound, db_insert_outbound,
    db_fetch_maint_history, db_insert_maint_history,
    db_delete_maint_history,
    db_fetch_alarms, db_update_safety_stock, db_fetch_users,
    db_update_aircraft,
)
from database_schedule import (
    db_fetch_maint_schedule, db_insert_maint_schedule,
    db_update_maint_schedule, db_delete_maint_schedule,
    db_fetch_bom_parts, db_update_maint_history,
)


def fetch_parts() -> list:          return db_fetch_parts()
def insert_part(p): return db_insert_part(p)
def update_part(pid, d): return db_update_part(pid, d)
def delete_parts(ids): db_delete_parts(ids)

def fetch_aircraft_status() -> list: return db_fetch_aircraft_status()
def fetch_aircraft_detail(aid): return db_fetch_aircraft_detail(aid)
def update_aircraft(aid, d): return db_update_aircraft(aid, d)

def fetch_alarms() -> list: return db_fetch_alarms()
def fetch_users() -> list: return db_fetch_users()

def fetch_inbound() -> list: return db_fetch_inbound()
def insert_inbound(r): return db_insert_inbound(r)
def fetch_outbound() -> list: return db_fetch_outbound()
def insert_outbound(r): return db_insert_outbound(r)

def fetch_maint_history() -> list: return db_fetch_maint_history()
def insert_maint_history(r): return db_insert_maint_history(r)
def delete_maint_history(ids): db_delete_maint_history(ids)
def update_maint_history(hid, d): return db_update_maint_history(hid, d)

def update_safety_stock(pid, d): return db_update_safety_stock(pid, d)

def fetch_bom_parts(model): return db_fetch_bom_parts(model)

def fetch_maint_schedule() -> list: return db_fetch_maint_schedule()
def insert_maint_schedule(s): return db_insert_maint_schedule(s)
def update_maint_schedule(sid, d): return db_update_maint_schedule(sid, d)
def delete_maint_schedule(ids): db_delete_maint_schedule(ids)