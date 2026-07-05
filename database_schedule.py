"""
database_schedule.py
DB 함수 — 정비스케줄 / BOM / 알람 / 사용자
"""
from database import supabase, _safe
import json


def db_fetch_maint_schedule() -> list:
    if not supabase:
        return []
    rows = _safe(lambda: supabase.table("maintenance_schedule")
                 .select("*, aircraft(registration)").execute().data)
    return [{
        "id":            r["id"], 
        "aircraft":      (r.get("aircraft") or {}).get("registration", ""),
        "aircraft_id":   r.get("aircraft_id", ""),
        "maint_type":    r.get("maintenance_type", ""), 
        "interval_hour": r.get("interval_hours"),
        "interval_mcal": r.get("interval_months"),
        "last_maint":    str(r.get("last_maintenance_date")),
        "next_due":      str(r.get("next_due_date")),
        "last_hours":    r.get("last_maint_hours"), 
        "due_hours":     r.get("next_due_hours"),
        "description":   r.get("description", ""),
    } for r in rows]


def db_insert_maint_schedule(schedule: dict) -> dict:
    if not supabase:
        return schedule
    def _insert():
        row = supabase.table("maintenance_schedule").insert({
            "aircraft_id":           schedule["aircraft_db_id"], 
            "maintenance_type":      schedule.get("maint_type", ""),
            "interval_hours":        schedule.get("interval_hour"),
            "interval_months":       schedule.get("interval_mcal"),
            "last_maintenance_date": schedule.get("last_maint"),
            "next_due_date":         schedule.get("next_due"), 
            "last_maint_hours":      schedule.get("last_hours"),
            "next_due_hours":        schedule.get("due_hours"),
            "description":           schedule.get("description", ""),
        }).execute().data[0]
        return {**schedule, "id": row["id"]}
    return _safe(_insert, schedule)


def db_update_maint_schedule(schedule_id: int, data: dict) -> dict:
    if not supabase:
        return data
    def _update():
        supabase.table("maintenance_schedule").update({
            "maintenance_type": data.get("maint_type", ""),
            "interval_hours":   data.get("interval_hour"),
            "interval_months":  data.get("interval_mcal"), 
            "last_maint_hours": data.get("last_hours"),
            "next_due_hours":   data.get("due_hours"),
            "description":      data.get("description", ""),
        }).eq("id", schedule_id).execute()
        return data
    return _safe(_update, data)


def db_delete_maint_schedule(ids: list) -> None:
    if not supabase or not ids:
        return
    _safe(lambda: supabase.table("maintenance_schedule")
          .delete().in_("id", ids).execute())


# database.py

...

def db_update_maint_history(history_id: int, data: dict) -> dict:
    if not supabase:
        return data
    def _update():
        supabase.table("maintenance_history").update({
            "aircraft_id":          data.get("aircraft_db_id"),
            "maintenance_date":     data.get("date"),
            "maintenance_type":     data.get("maint_type", ""),
            "hours_at_maintenance": data.get("flight_hrs", 0),
            "work_description":     data.get("note", ""),
            "next_due_hours":       data.get("next_plan", 0),
            "handled_by":           data.get("technician", ""),
        }).eq("id", history_id).execute()
        return data
    return _safe(_update, data)

# ── 8. BOM 조회 ───────────────────────────────────────────────────
def db_fetch_bom_parts(aircraft_model: str) -> list:
    """
    기체 클릭 시 좌측 표에 표시할 부품 목록
    = components(해당 기종 aircraft_id) + BOM(해당 기종) 통합
    aircraft_model: 'DA-40NG' 또는 'DA-42NG'
    """
    if not supabase:
        return []

    # ── 1. aircraft_id 매핑 (DA-40NG→2, DA-42NG→3) ──
    ac_rows = _safe(lambda: supabase.table("aircraft")
                    .select("id, category").execute().data)
    ac_id_map = {}
    for a in ac_rows:
        cat = a.get("category", "").replace(" ", "")  # 'DA-40 NG' → 'DA-40NG'
        ac_id_map[cat] = a["id"]

    ac_db_id = ac_id_map.get(aircraft_model)

    # ── 2. components: 해당 기종 aircraft_id 기준 조회 ──
    if ac_db_id:
        comps = _safe(lambda: supabase.table("components")
                      .select("*").eq("aircraft_id", ac_db_id).execute().data)
    else:
        comps = []

    # ── 3. BOM: 해당 기종 부품 조회 ──
    bom_rows = _safe(lambda: supabase.table("bom")
                     .select("*").eq("aircraft_model", aircraft_model)
                     .execute().data)

    # BOM part_id → maintenance_type 매핑 (중복 시 첫 번째)
    bom_map = {}
    for b in bom_rows:
        pid = b["part_id"]
        if pid not in bom_map:
            bom_map[pid] = b.get("maintenance_type", "")

    # ── 4. 전체 part_id 수집 (components + BOM) ──
    comp_ids = {c["id"] for c in comps}
    bom_ids  = set(bom_map.keys())
    all_ids  = list(comp_ids | bom_ids)

    if not all_ids:
        return []

    # ── 5. 재고/안전재고 조회 ──
    invs = _safe(lambda: supabase.table("parts_inventory")
                 .select("*").in_("part_id", all_ids).execute().data)
    rops = _safe(lambda: supabase.table("reorder_points")
                 .select("*").in_("part_id", all_ids).execute().data)

    # BOM에만 있는 부품은 components에서 추가 조회
    extra_ids = list(bom_ids - comp_ids)
    if extra_ids:
        extra_comps = _safe(lambda: supabase.table("components")
                            .select("*").in_("id", extra_ids).execute().data)
        comps = comps + extra_comps

    comp_map = {c["id"]: c for c in comps}

    inv_map = {}
    for row in invs:
        pid = row["part_id"]
        if pid not in inv_map:
            inv_map[pid] = {"qty": 0, "locations": []}
        inv_map[pid]["qty"] += row.get("quantity_on_hand", 0)
        if row.get("location"):
            inv_map[pid]["locations"].append(row["location"])

    rop_map = {r["part_id"]: r for r in rops}

    # ── 6. 결과 조합 ──
    result = []
    for pid in sorted(all_ids):
        c   = comp_map.get(pid, {})
        inv = inv_map.get(pid, {"qty": 0, "locations": []})
        rop = rop_map.get(pid, {})
        locs = list(dict.fromkeys(inv["locations"]))

        # inspection_interval: components 우선, 없으면 BOM maintenance_type
        interval = c.get("inspection_interval") or bom_map.get(pid, "")

        result.append({
            "part_id":             pid,
            "part_no":             c.get("part_number", ""),
            "part_number":         c.get("part_number", ""),
            "name":                c.get("nomenclature", ""),
            "category":            c.get("category", ""),
            "inspection_interval": interval,
            "qty":                 inv["qty"],
            "safe_qty":            rop.get("safety_stock", 0),
            "location":            "/".join(locs) if locs else "-",
            "maintenance_type":    bom_map.get(pid, interval),
            "required_qty":        1,
            "unit":                "EA",
            "lead_time":           rop.get("lead_time_days", 98),
            "order_unit":          rop.get("reorder_qty", 1),
            "reason":              rop.get("update_reason") or "",
        })
    return result