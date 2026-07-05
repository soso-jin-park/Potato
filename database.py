"""
database.py
Supabase 연결 + 실제 DB 스키마 기반 데이터 조회/수정 함수 모음
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

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