#!/usr/bin/env python3
"""Query Logfire logs for the last 12 hours."""
import httpx

READ_TOKEN = 'pylf_v1_us_S9j1Cb7vX0bCgZ0XSjZGBZqjc8dTgsDcvPYDGZfmhmZP'
BASE_URL = 'https://logfire-api.pydantic.dev/v1/query'


def query(sql: str) -> list:
    """Execute SQL query against Logfire."""
    r = httpx.get(
        BASE_URL,
        headers={'Authorization': f'Bearer {READ_TOKEN}'},
        params={'sql': sql},
        timeout=30
    )
    if r.status_code == 200:
        data = r.json()
        cols = data.get('columns', [])
        if not cols:
            return []
        # Transpose column-oriented to row-oriented
        num_rows = len(cols[0]['values']) if cols else 0
        return [[col['values'][i] for col in cols] for i in range(num_rows)]
    print(f"Query error: {r.status_code} - {r.text[:200]}")
    return []


def main():
    print("=" * 70)
    print("📊 LOGFIRE LOGS - ALL AVAILABLE DATA")
    print("=" * 70)

    # Total count - remove time filter
    rows = query("SELECT count(*), min(start_timestamp), max(start_timestamp) FROM records")
    if rows:
        print(f"\n📈 Total records: {rows[0][0]}")
        print(f"   Time range: {rows[0][1][:19]} to {rows[0][2][:19]}")

    # By service - remove time filter
    print("\n📦 By service:")
    for r in query("""
        SELECT service_name, count(*) 
        FROM records 
        GROUP BY service_name 
        ORDER BY 2 DESC
    """):
        print(f"  • {r[0]}: {r[1]} records")

    # Errors and warnings (level >= 13 is WARN, >= 17 is ERROR) - remove time filter
    print("\n⚠️ Errors & Warnings:")
    rows = query("""
        SELECT start_timestamp, message, level 
        FROM records 
        WHERE level >= 13
        ORDER BY start_timestamp DESC
        LIMIT 10
    """)
    if rows:
        for r in rows:
            ts = r[0][11:19]
            lvl = "ERROR" if r[2] >= 17 else "WARN"
            print(f"  [{ts}] {lvl}: {r[1][:65]}")
    else:
        print("  ✅ No errors or warnings")

    # Model usage - remove time filter
    print("\n🤖 Model calls:")
    for r in query("""
        SELECT message, count(*) 
        FROM records 
        WHERE message LIKE '%Chat Completion%'
        GROUP BY message 
        ORDER BY 2 DESC
        LIMIT 5
    """):
        print(f"  • {r[0]}: {r[1]} calls")

    # Tool usage - remove time filter
    print("\n🔧 Tool usage:")
    for r in query("""
        SELECT message, count(*) 
        FROM records 
        WHERE message LIKE 'running tool:%'
        GROUP BY message 
        ORDER BY 2 DESC
        LIMIT 10
    """):
        tool = r[0].replace('running tool: ', '')
        print(f"  • {tool}: {r[1]} calls")

    # Slowest operations - remove time filter
    print("\n🐢 Slowest operations:")
    for r in query("""
        SELECT message 
        FROM records 
        WHERE message LIKE '%took%s'
        ORDER BY start_timestamp DESC
        LIMIT 10
    """):
        print(f"  • {r[0][:75]}")

    # Recent activity
    print("\n📋 Recent activity (last 15):")
    for r in query("""
        SELECT start_timestamp, message 
        FROM records 
        WHERE start_timestamp > now() - interval '12 hours' 
        ORDER BY start_timestamp DESC
        LIMIT 15
    """):
        ts = r[0][11:19]
        print(f"  [{ts}] {r[1][:60]}")

    print("\n" + "=" * 70)
    print("🔗 Full dashboard: https://logfire-us.pydantic.dev/t-granlund/code-puppy-logs/live")
    print("=" * 70)


if __name__ == '__main__':
    main()
