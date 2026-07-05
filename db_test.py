# db_test.py
# 실행: python db_test.py
import os
from dotenv import load_dotenv
from supabase import create_client



load_dotenv()
URL = os.getenv("SUPABASE_URL", "").strip()
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

print(f"URL: {URL}")
print(f"KEY: {KEY[:30]}...")

sb = create_client(URL, KEY)

tables = [
    "components", "parts_inventory", "reorder_points",
    "aircraft", "maintenance_schedule", "d_time_counter",
    "parts_transactions", "maintenance_history", "user_roles",
]

print("\n── 테이블별 행 수 ──")
for t in tables:
    try:
        rows = sb.table(t).select("*", count="exact").execute()
        print(f"  {t:30s}: {rows.count}행")
    except Exception as e:
        print(f"  {t:30s}: ❌ {e}")

# components 샘플 1건
print("\n── components 샘플 ──")
try:
    r = sb.table("components").select("*").limit(1).execute()
    print(r.data)
except Exception as e:
    print(f"❌ {e}")

# aircraft 샘플 1건
print("\n── aircraft 샘플 ──")
try:
    r = sb.table("aircraft").select("*").limit(1).execute()
    print(r.data)
except Exception as e:
    print(f"❌ {e}")