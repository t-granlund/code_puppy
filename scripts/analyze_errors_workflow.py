#!/usr/bin/env python3
"""Analyze error patterns and workflow efficiency."""
import httpx

READ_TOKEN = 'pylf_v1_us_S9j1Cb7vX0bCgZ0XSjZGBZqjc8dTgsDcvPYDGZfmhmZP'
BASE_URL = 'https://logfire-api.pydantic.dev/v1/query'


def query(sql: str) -> list:
    r = httpx.get(BASE_URL, headers={'Authorization': f'Bearer {READ_TOKEN}'}, params={'sql': sql}, timeout=30)
    if r.status_code == 200:
        cols = r.json().get('columns', [])
        if not cols: return []
        n = len(cols[0]['values']) if cols else 0
        return [[col['values'][i] for col in cols] for i in range(n)]
    return []


def main():
    print("=" * 75)
    print("🔬 ERROR PATTERN & WORKFLOW ANALYSIS")
    print("=" * 75)

    # 1. What are the actual error messages?
    print("\n1️⃣ ERROR MESSAGES (full text from exceptions):")
    rows = query("""
        SELECT start_timestamp, span_name, message, attributes
        FROM records 
        WHERE level >= 17 
        ORDER BY start_timestamp DESC 
        LIMIT 20
    """)
    if rows:
        for r in rows:
            ts = r[0][11:19] if r[0] else "?"
            span = r[1] or "?"
            msg = r[2] or "?"
            attrs = str(r[3])[:100] if r[3] else ""
            print(f"\n   [{ts}] {span}")
            print(f"      Message: {msg[:80]}")
            if "exception" in attrs.lower() or "error" in attrs.lower():
                print(f"      Attrs: {attrs[:100]}...")

    # 2. What happened right before errors?
    print("\n\n2️⃣ CONTEXT AROUND ERRORS (messages around error timestamps):")
    # Get first error timestamp
    errors = query("SELECT start_timestamp FROM records WHERE level >= 17 ORDER BY start_timestamp LIMIT 3")
    if errors:
        ts = errors[0][0]
        print(f"   Looking around first error at {ts[:19]}...")
        context = query(f"""
            SELECT start_timestamp, span_name, message 
            FROM records 
            WHERE start_timestamp BETWEEN '{ts}'::timestamp - interval '30 seconds' AND '{ts}'::timestamp + interval '10 seconds'
            ORDER BY start_timestamp
            LIMIT 20
        """)
        for r in context:
            print(f"   [{r[0][11:19]}] {r[1]}: {r[2][:60]}")

    # 3. Workload routing - is Kimi being used for CODING when GLM should be?
    print("\n\n3️⃣ WORKLOAD ROUTING ANALYSIS:")
    print("   Expected: GLM-4.7 for CODING, Kimi-K2.5 for ORCHESTRATOR/REASONING")
    print()
    
    # Check if Kimi is being used for tool-heavy work (should be GLM)
    print("   Tool calls per model:")
    rows = query("""
        SELECT 
            CASE 
                WHEN span_name LIKE '%Kimi%' THEN 'Kimi-K2.5'
                WHEN span_name LIKE '%GLM%' THEN 'GLM-4.7'
                ELSE 'Other'
            END as model,
            count(*)
        FROM records 
        WHERE message LIKE 'running tool:%'
        GROUP BY 1
        ORDER BY 2 DESC
    """)
    for r in rows:
        print(f"      {r[0]}: {r[1]} tool calls")

    # 4. Agent run duration analysis
    print("\n\n4️⃣ AGENT RUN PATTERNS:")
    rows = query("""
        SELECT span_name, count(*), avg(extract(epoch from (end_timestamp - start_timestamp))) as avg_duration
        FROM records 
        WHERE span_name LIKE 'agent%' OR span_name LIKE 'chat%'
        GROUP BY span_name
        ORDER BY 3 DESC NULLS LAST
        LIMIT 15
    """)
    if rows:
        for r in rows:
            dur = f"{r[2]:.1f}s" if r[2] else "?"
            print(f"   {r[0]}: {r[1]} runs, avg {dur}")

    # 5. Retry patterns (same operation repeated quickly)
    print("\n\n5️⃣ RETRY PATTERNS (potential wasted work):")
    rows = query("""
        SELECT message, count(*) as cnt
        FROM records 
        WHERE message LIKE 'running tool: edit_file%' 
           OR message LIKE 'running tool: grep%'
        GROUP BY message
        HAVING count(*) > 3
        ORDER BY cnt DESC
        LIMIT 10
    """)
    if rows:
        for r in rows:
            print(f"   {r[0][:50]}... = {r[1]}x")
    else:
        print("   ✅ No significant retry patterns")

    # 6. Check for "redo" patterns
    print("\n\n6️⃣ POTENTIAL REDO PATTERNS:")
    rows = query("""
        SELECT message, count(*) 
        FROM records 
        WHERE message LIKE '%redo%' OR message LIKE '%retry%' OR message LIKE '%again%'
        GROUP BY message
        ORDER BY 2 DESC
        LIMIT 10
    """)
    if rows:
        for r in rows:
            print(f"   {r[0][:60]}: {r[1]}")
    else:
        print("   ✅ No explicit redo messages")

    # 7. Consecutive model calls without tools (thinking loops?)
    print("\n\n7️⃣ MODEL EFFICIENCY (calls without tool output):")
    total_model_calls = query("SELECT count(*) FROM records WHERE message LIKE 'Chat Completion%'")[0][0]
    tool_runs = query("SELECT count(*) FROM records WHERE message LIKE 'running%tool%'")[0][0]
    
    print(f"   Total model calls: {total_model_calls}")
    print(f"   Total tool runs: {tool_runs}")
    
    if total_model_calls > 0:
        efficiency = tool_runs / total_model_calls
        print(f"   Tool/Model ratio: {efficiency:.2f}")
        if efficiency < 0.5:
            print("   ⚠️ LOW - Model may be doing excessive thinking without action")
        elif efficiency < 1.0:
            print("   ✅ NORMAL - Reasonable balance of thinking and action")
        else:
            print("   ✅ HIGH - Many tools per model call (efficient)")

    print("\n" + "=" * 75)


if __name__ == "__main__":
    main()
