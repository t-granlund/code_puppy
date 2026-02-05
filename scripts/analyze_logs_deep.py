#!/usr/bin/env python3
"""Deep analysis of Logfire logs for failover, model routing, and efficiency."""
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
        cols = r.json().get('columns', [])
        if not cols:
            return []
        num_rows = len(cols[0]['values']) if cols else 0
        return [[col['values'][i] for col in cols] for i in range(num_rows)]
    return []


def main():
    print("=" * 75)
    print("🔍 DEEP ANALYSIS: Model Routing, Failover & Efficiency")
    print("=" * 75)

    # 1. Failover events
    print("\n1️⃣ FAILOVER EVENTS (model switches):")
    rows = query("SELECT message FROM records WHERE message LIKE '%failover%' OR message LIKE '%switching%' OR message LIKE '%fallback%' LIMIT 20")
    if rows:
        for r in rows:
            print(f"   {r[0][:80]}")
    else:
        print("   ✅ No explicit failover events logged")

    # 2. Rate limits
    print("\n2️⃣ RATE LIMIT / 429 ERRORS:")
    rows = query("SELECT start_timestamp, message FROM records WHERE message LIKE '%429%' OR message LIKE '%rate limit%' LIMIT 10")
    if rows:
        for r in rows:
            print(f"   [{r[0][11:19]}] {r[1][:60]}")
    else:
        print("   ✅ No rate limit errors")

    # 3. Model usage over time
    print("\n3️⃣ MODEL DISTRIBUTION BY TIME BUCKET:")
    rows = query("""
        SELECT 
            CASE 
                WHEN extract(hour from start_timestamp) < 5 THEN '03-05h'
                WHEN extract(hour from start_timestamp) < 7 THEN '05-07h' 
                WHEN extract(hour from start_timestamp) < 9 THEN '07-09h'
                WHEN extract(hour from start_timestamp) < 11 THEN '09-11h'
                ELSE '11-13h'
            END as time_bucket,
            message,
            count(*)
        FROM records 
        WHERE message LIKE 'Chat Completion%'
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """)
    if rows:
        current_bucket = None
        for r in rows:
            if r[0] != current_bucket:
                current_bucket = r[0]
                print(f"\n   📊 {current_bucket}:")
            model = r[1].replace("Chat Completion with '", "").replace("'", "")
            print(f"      {model}: {r[2]} calls")

    # 4. Agent invocation patterns
    print("\n4️⃣ AGENT INVOCATIONS:")
    rows = query("SELECT message, count(*) FROM records WHERE message LIKE 'agent%' GROUP BY message ORDER BY 2 DESC LIMIT 10")
    if rows:
        for r in rows:
            print(f"   {r[0]}: {r[1]}")
    else:
        print("   (no agent-level logs)")

    # 5. Errors by span/context
    print("\n5️⃣ ERRORS BY CONTEXT (span_name):")
    rows = query("SELECT span_name, count(*) FROM records WHERE level >= 17 GROUP BY span_name ORDER BY 2 DESC LIMIT 10")
    if rows:
        for r in rows:
            print(f"   {r[0]}: {r[1]} errors")
    else:
        print("   ✅ No errors")

    # 6. Tool efficiency (how many tool calls per model call)
    print("\n6️⃣ TOOL CALL EFFICIENCY:")
    model_calls = query("SELECT count(*) FROM records WHERE message LIKE 'Chat Completion%'")
    tool_calls = query("SELECT count(*) FROM records WHERE message LIKE 'running tool:%'")
    if model_calls and tool_calls:
        m = model_calls[0][0]
        t = tool_calls[0][0]
        ratio = t / m if m > 0 else 0
        print(f"   Model calls: {m}")
        print(f"   Tool calls: {t}")
        print(f"   Ratio: {ratio:.2f} tools per model call")

    # 7. Repeated/redundant operations
    print("\n7️⃣ POTENTIAL REDUNDANCY (same tool on same file):")
    rows = query("""
        SELECT message, count(*) as cnt 
        FROM records 
        WHERE message LIKE 'running tool: read_file%'
        GROUP BY message 
        HAVING count(*) > 5
        ORDER BY cnt DESC 
        LIMIT 10
    """)
    if rows:
        for r in rows:
            print(f"   {r[0][:50]}... ({r[1]}x)")
    else:
        print("   ✅ No highly repeated read_file operations")

    # 8. Slow streaming responses
    print("\n8️⃣ SLOWEST STREAMING RESPONSES:")
    rows = query("SELECT message FROM records WHERE message LIKE 'streaming response%took%s' ORDER BY start_timestamp DESC LIMIT 10")
    if rows:
        for r in rows:
            msg = r[0]
            # Extract model and time
            print(f"   {msg}")

    # 9. invoke_agent usage (delegation)
    print("\n9️⃣ AGENT DELEGATION (invoke_agent tool):")
    rows = query("SELECT start_timestamp, message FROM records WHERE message LIKE '%invoke_agent%' ORDER BY start_timestamp DESC LIMIT 10")
    if rows:
        for r in rows:
            print(f"   [{r[0][11:19]}] {r[1][:60]}")
    else:
        print("   No agent delegation logged")

    # 10. GLM-4.7 specific usage (should be CODING workload)
    print("\n🔟 GLM-4.7 USAGE (should be CODING workload):")
    rows = query("SELECT message, count(*) FROM records WHERE message LIKE '%GLM-4%' OR message LIKE '%zai-glm%' GROUP BY message ORDER BY 2 DESC LIMIT 5")
    if rows:
        for r in rows:
            print(f"   {r[0]}: {r[1]}")
    else:
        print("   No GLM-4.7 usage logged")

    print("\n" + "=" * 75)
    print("📊 Dashboard: https://logfire-us.pydantic.dev/t-granlund/code-puppy-logs")
    print("=" * 75)


if __name__ == "__main__":
    main()
