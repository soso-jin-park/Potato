"""
database.py
Supabase 연결 + 실제 DB 스키마 기반 데이터 조회/수정 함수 모음
"""
import os
from supabase import create_client, Client
from pathlib import Path
from dotenv import load_dotenv

# [Linux] .env / _env 둘 다 탐색 (실행 위치 무관)
_BASE_DIR = Path(__file__).resolve().parent
for _env_name in ('.env', '_env'):
    _env_path = _BASE_DIR / _env_name
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
        break

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

print(f"\n[Supabase] URL: {'✅' if SUPABASE_URL else '❌ 누락'}")
print(f"[Supabase] KEY: {'✅' if SUPABASE_KEY else '❌ 누락'}")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[Supabase] 클라이언트 생성 성공")
    except Exception as e:
        print(f"[Supabase] 클라이언트 생성 실패: {e}")


def _safe(fn, fallback=None):
    try:
        return fn()
    except Exception as e:
        print(f"❌ DB 오류: {e}")
        return fallback if fallback is not None else []


def db_fetch_parts() -> list:
    if not supabase:
        return []
    comps = _safe(lambda: supabase.table("components").select("*").execute().data)
    invs  = _safe(lambda: supabase.table("parts_inventory").select("*").execute().data)
    rops  = _safe(lambda: supabase.table("reorder_points").select("*").execute().data)

    inv_map = {}
    for row in invs:
        pid = row["part_id"]
        if pid not in inv_map:
            inv_map[pid] = {"qty": 0, "locations": []}
        inv_map[pid]["qty"] += row.get("quantity_on_hand", 0)
        if row.get("location"):
            inv_map[pid]["locations"].append(row["location"])

    rop_map = {r["part_id"]: r for r in rops}
    result = []
    for c in comps:
        pid = c["id"]
        inv = inv_map.get(pid, {"qty": 0, "locations": []})
        rop = rop_map.get(pid, {})
        locs = list(dict.fromkeys(inv["locations"]))
        result.append({
            "part_id":             pid,
            "part_number":         c.get("part_number", ""),
            "part_no":             c.get("part_number", ""),
            "name":                c.get("nomenclature", ""),
            "category":            c.get("category", ""),
            "aircraft_id":         c.get("aircraft_id"),
            "inspection_interval": c.get("inspection_interval", ""),
            "qty":                 inv["qty"],
            "safe_qty":            rop.get("safety_stock", 0),
            "location":            "/".join(locs) if locs else "-",
            "safety_stock":        rop.get("safety_stock", 0),
            "lead_time_days":      rop.get("lead_time_days", 98),
            "lead_time":           rop.get("lead_time_days", 98),
            "order_unit":          rop.get("reorder_qty", 1),
            "reorder_qty":         rop.get("reorder_qty", 0),
            "minimum_qty":         rop.get("minimum_qty", 0),
            "maximum_qty":         rop.get("maximum_qty", 0),
            "unit_price":          0.0,
            "reason":              rop.get("update_reason") or "",
        })
    return result


def db_insert_part(part: dict) -> dict:
    if not supabase:
        return part
    def _insert():
        comp = supabase.table("components").insert({
            "category":            part.get("category", "기체"),
            "nomenclature":        part.get("name", ""),
            "part_number":         part.get("part_number", part.get("part_no", "")),
            "inspection_interval": part.get("inspection_interval", ""),
            "aircraft_id":         part.get("aircraft_id"),
        }).execute().data[0]
        pid = comp["id"]
        supabase.table("parts_inventory").insert({
            "part_id":          pid,
            "quantity_on_hand": part.get("qty", 0),
            "location":         part.get("location", "청주"),
        }).execute()
        if part.get("safe_qty", 0) > 0:
            supabase.table("reorder_points").insert({
                "part_id":        pid,
                "safety_stock":   part.get("safe_qty", 0),
                "minimum_qty":    part.get("minimum_qty", 1),
                "maximum_qty":    part.get("maximum_qty", 10),
                "reorder_qty":    part.get("order_unit", 1),
                "lead_time_days": part.get("lead_time", 98),
            }).execute()
        return {**part, "part_id": pid}
    return _safe(_insert, part)


def db_update_part(part_id: int, data: dict) -> dict:
    if not supabase:
        return data
    def _update():
        supabase.table("components").update({
            "nomenclature": data.get("name", ""),
            "part_number":  data.get("part_number", data.get("part_no", "")),
        }).eq("id", part_id).execute()
        if "safe_qty" in data:
            existing = supabase.table("reorder_points").select("id")\
                .eq("part_id", part_id).execute().data
            payload = {
                "safety_stock":   data["safe_qty"],
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


def db_delete_parts(ids: list) -> None:
    if not supabase or not ids:
        return
    # 자식 테이블 먼저 삭제 (FK 제약 순서 주의)
    _safe(lambda: supabase.table("bom")
          .delete().in_("part_id", ids).execute())
    _safe(lambda: supabase.table("inventory_history")
          .delete().in_("part_id", ids).execute())
    _safe(lambda: supabase.table("parts_transactions")
          .delete().in_("part_id", ids).execute())
    _safe(lambda: supabase.table("parts_inventory")
          .delete().in_("part_id", ids).execute())
    _safe(lambda: supabase.table("reorder_points")
          .delete().in_("part_id", ids).execute())
    # 마지막으로 components 삭제
    _safe(lambda: supabase.table("components")
          .delete().in_("id", ids).execute())


def db_fetch_aircraft_status() -> list:
    if not supabase:
        return []
    acs    = _safe(lambda: supabase.table("aircraft").select("*").execute().data)
    scheds = _safe(lambda: supabase.table("maintenance_schedule").select("*").execute().data)
    ctrs   = _safe(lambda: supabase.table("d_time_counter").select("*").execute().data)
    invs   = _safe(lambda: supabase.table("parts_inventory").select("*").execute().data)
    rops   = _safe(lambda: supabase.table("reorder_points").select("*").execute().data)

    sched_map = {}
    for s in scheds:
        sched_map.setdefault(s["aircraft_id"], []).append(s)
    ctr_map = {}
    for c in ctrs:
        ctr_map.setdefault(c["aircraft_id"], []).append(c)
    rop_map = {r["part_id"]: r for r in rops}
    inv_map = {}
    for row in invs:
        pid = row["part_id"]
        inv_map[pid] = inv_map.get(pid, 0) + row.get("quantity_on_hand", 0)

    result = []
    for ac in acs:
        aid       = ac["id"]
        total_hrs = float(ac.get("total_flight_hours") or 0)
        ac_ctrs   = ctr_map.get(aid, [])
        ac_scheds = sched_map.get(aid, [])

        hr_ctrs = [c for c in ac_ctrs if c.get("hours_remaining") is not None]
        if hr_ctrs:
            min_ctr   = min(hr_ctrs, key=lambda c: float(c["hours_remaining"]))
            next_insp = float(min_ctr["hours_remaining"])
            cs        = next((s for s in ac_scheds
                              if s["id"] == min_ctr["maintenance_schedule_id"]), {})
            cycle_hrs = float(cs.get("interval_hours") or 100)
        else:
            next_insp, cycle_hrs = 100.0, 100.0

        pct = min(int(next_insp / cycle_hrs * 100), 100) if cycle_hrs else 0

        msb_ctr = next(
            (c for c in ac_ctrs
             if c.get("days_remaining") is not None
             and not c.get("hours_remaining")), None
        )

        shortage = [
            {"part_id": pid, "qty": qty, "safe_qty": rop_map[pid]["safety_stock"]}
            for pid, qty in inv_map.items()
            if pid in rop_map and qty < rop_map[pid].get("safety_stock", 0)
        ]

        # maintenance_schedule에서 상위 3개, interval_hours 없어도 포함
        schedules = []
        for s in ac_scheds[:3]:
            hrs = s.get("interval_hours") or s.get("due_hours")
            schedules.append({
                "label": s.get("maintenance_type", ""),
                "hours": float(hrs) if hrs else 0,
                "cycle": float(s.get("interval_hours") or 100),
            })

        result.append({
            "id":              ac.get("registration", ""),
            "type":            ac.get("category", ""),
            "total_hours":     total_hrs,
            "pct":             pct,
            "next_inspection": next_insp,
            "cycle_hours":     cycle_hrs,
            "location":        "",
            "msb_remaining":   msb_ctr["days_remaining"] if msb_ctr else None,
            "stock_shortage":  shortage,
            "schedules":       schedules,
            "db_id":           aid,
            "registration":    ac.get("registration", ""),
            "category":        ac.get("category", ""),
            "model":           ac.get("model", ""),
            "status":          ac.get("status", ""),
        })
    # registration 번호 기준 오름차순 정렬 (HL1176, HL1177, ... HL2046)
    result.sort(key=lambda x: x.get("registration", ""))
    return result


def db_fetch_aircraft_detail(aircraft_id: str) -> dict:
    for ac in db_fetch_aircraft_status():
        if ac["id"] == aircraft_id or ac["registration"] == aircraft_id:
            return ac
    return {}


