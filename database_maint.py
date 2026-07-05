"""
database_maint.py
DB 함수 — 입출고 / 정비이력 / 정비스케줄 / BOM / 알람 / 사용자
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

_BASE_DIR = Path(__file__).resolve().parent
for _env_name in ('.env', '_env'):
    _env_path = _BASE_DIR / _env_name
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
        break

_URL = os.getenv("SUPABASE_URL", "").strip()
_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

# database.py에서 공유 클라이언트를 가져옴
try:
    from database import supabase, _safe
except ImportError:
    supabase = create_client(_URL, _KEY) if _URL and _KEY else None
    def _safe(fn, fallback=None):
        try:
            return fn()
        except Exception as e:
            print(f"❌ DB 오류: {e}")
            return fallback if fallback is not None else []

def db_fetch_inbound() -> list:
    if not supabase:
        return []
    rows = _safe(lambda: supabase.table("parts_transactions")
                 .select("*, components(part_number, nomenclature)")
                 .eq("transaction_type", "입고")
                 .order("transaction_date", desc=True).execute().data)
    return [{
        "id":         r["id"],
        "date":       str(r.get("transaction_date", ""))[:10],
        "order_no":   r.get("reference_number") or "-",
        "part_id":    r.get("part_id"),
        "part_no":    (r.get("components") or {}).get("part_number", ""),
        "name":       (r.get("components") or {}).get("nomenclature", ""),
        "qty":        r.get("quantity", 0),
        "unit_price": float(r.get("unit_price_eur") or 0),
        "rate":       float(r.get("exchange_rate_applied") or 0),
        "location":   r.get("location", ""),
        "note":       r.get("notes") or "",
    } for r in rows]


def db_fetch_outbound() -> list:
    if not supabase:
        return []
    rows = _safe(lambda: supabase.table("parts_transactions")
                 .select("*, components(part_number, nomenclature)")
                 .eq("transaction_type", "출고")
                 .order("transaction_date", desc=True).execute().data)
    return [{
        "id":          r["id"],
        "date":        str(r.get("transaction_date", ""))[:10],
        "part_id":     r.get("part_id"),
        "part_no":     (r.get("components") or {}).get("part_number", ""),
        "name":        (r.get("components") or {}).get("nomenclature", ""),
        "qty":         r.get("quantity", 0),
        "remain":      0,
        "region":      r.get("location", ""),
        "aircraft_id": str(r.get("aircraft_id") or ""),
        "maint_type":  r.get("maintenance_type") or "",
        "technician":  r.get("handled_by") or "",
        "note":        r.get("notes") or "",
    } for r in rows]


def db_insert_inbound(record: dict) -> dict:
    if not supabase:
        return record
    def _insert():
        row = supabase.table("parts_transactions").insert({
            "part_id":               record.get("part_id"),
            "transaction_type":      "입고",
            "quantity":              record.get("qty", 0),
            "transaction_date":      record.get("date"),
            "reference_number":      record.get("order_no"),
            "unit_price_eur":        record.get("unit_price"),
            "exchange_rate_applied": record.get("rate"),
            "location":              record.get("location", "청주"),
            "notes":                 record.get("note", ""),
        }).execute().data[0]
        invs = supabase.table("parts_inventory").select("*")\
            .eq("part_id", record.get("part_id"))\
            .eq("location", record.get("location", "청주")).execute().data
        if invs:
            supabase.table("parts_inventory").update({
                "quantity_on_hand": invs[0]["quantity_on_hand"] + record.get("qty", 0)
            }).eq("id", invs[0]["id"]).execute()
        return {**record, "id": row["id"]}
    return _safe(_insert, record)


def db_insert_outbound(record: dict) -> dict:
    if not supabase:
        return record
    def _insert():
        row = supabase.table("parts_transactions").insert({
            "part_id":          record.get("part_id"),
            "transaction_type": "출고",
            "quantity":         record.get("qty", 0),
            "transaction_date": record.get("date"),
            "location":         record.get("region", "청주"),
            "aircraft_id":      record.get("aircraft_db_id"),
            "maintenance_type": record.get("maint_type", ""),
            "handled_by":       record.get("technician", ""),
            "notes":            record.get("note", ""),
        }).execute().data[0]
        invs = supabase.table("parts_inventory").select("*")\
            .eq("part_id", record.get("part_id"))\
            .eq("location", record.get("region", "청주")).execute().data
        if invs:
            supabase.table("parts_inventory").update({
                "quantity_on_hand": max(0, invs[0]["quantity_on_hand"] - record.get("qty", 0))
            }).eq("id", invs[0]["id"]).execute()
        return {**record, "id": row["id"]}
    return _safe(_insert, record)


def db_fetch_maint_history() -> list:
    if not supabase:
        return []
    rows = _safe(lambda: supabase.table("maintenance_history").select("""
        *,
        aircraft(registration),
        parts_transactions(
            maintenance_history_id,
            part_id,
            components(part_number, nomenclature),
            quantity
        )  
    """).order("maintenance_date", desc=True).execute().data)

    result = []
    for r in rows:
        parts = [
            {
                "part_id":  p["part_id"],
                "part_no":  p["components"]["part_number"],
                "name":     p["components"]["nomenclature"], 
                "qty":      p["quantity"],
            }
            for p in r["parts_transactions"]
        ]
        result.append({
            "id":          r["id"],
            "date":        str(r.get("maintenance_date", "")),
            "aircraft_id": (r.get("aircraft") or {}).get("registration", str(r.get("aircraft_id", ""))),
            "maint_type":  r.get("maintenance_type", ""),
            "flight_hrs":  float(r.get("hours_at_maintenance") or 0),
            "next_plan":   float(r.get("next_due_hours") or 0),
            "technician":  r.get("handled_by", ""),
            "parts":       parts,
            "note":        r.get("work_description", ""),
        })
    return result


def db_insert_maint_history(record: dict) -> dict:
    if not supabase:
        return record
    def _insert():
        ac_rows = supabase.table("aircraft").select("id")\
            .eq("registration", record.get("aircraft_id", "")).execute().data
        ac_db_id = ac_rows[0]["id"] if ac_rows else record.get("aircraft_db_id")
        row = supabase.table("maintenance_history").insert({
            "aircraft_id":          ac_db_id,
            "maintenance_date":     record.get("date"),
            "maintenance_type":     record.get("maint_type", ""),
            "hours_at_maintenance": record.get("flight_hrs", 0),
            "work_description":     record.get("note", ""),
            "next_due_hours":       record.get("next_plan", 0),
            "handled_by":           record.get("technician", ""),
        }).execute().data[0]
        return {**record, "id": row["id"]}
    return _safe(_insert, record)


def db_delete_maint_history(ids: list) -> None:
    if not supabase or not ids:
        return
    _safe(lambda: supabase.table("maintenance_history")
          .delete().in_("id", ids).execute())


def db_fetch_alarms() -> list:
    if not supabase:
        return []
    return _safe(lambda: supabase.table("maintenance_alarms")
                 .select("*").execute().data)


def db_update_safety_stock(part_id: int, data: dict) -> dict:
    if not supabase:
        return data
    def _update():
        existing = supabase.table("reorder_points").select("id")\
            .eq("part_id", part_id).execute().data
        payload = {
            "safety_stock":   data.get("safe_qty", 0),
            "reorder_qty":    data.get("order_unit", 1),
            "lead_time_days": data.get("lead_time", 98),
            "update_reason":  data.get("reason", ""),
        }
        if existing:
            supabase.table("reorder_points").update(payload)\
                .eq("part_id", part_id).execute()
        else:
            supabase.table("reorder_points").insert(
                {**payload, "part_id": part_id}
            ).execute()
        return data
    return _safe(_update, data)


def db_fetch_users() -> list:
    if not supabase:
        return []
    return _safe(lambda: supabase.table("user_roles").select("*").execute().data)

# database.py

...

def db_update_aircraft(aircraft_id: int, data: dict) -> dict:
    if not supabase:
        return data
    def _update():
        supabase.table("aircraft").update({
            "total_flight_hours": data.get("total_hours", 0),
            "registration":       data.get("registration", ""),
            "aircraft_serial_no": data.get("serial", ""),
            "location":           data.get("location", ""),
        }).eq("id", aircraft_id).execute()
        return data
    return _safe(_update, data)

