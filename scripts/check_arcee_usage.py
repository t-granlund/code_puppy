#!/usr/bin/env python3
"""Check Logfire logs for Arcee AI usage."""
import httpx
import json

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
        
        column_names = [c['name'] for c in cols]
        
        # Transpose column-oriented to row-oriented dicts
        num_rows = len(cols[0]['values']) if cols else 0
        rows = []
        for i in range(num_rows):
            row = {}
            for j, col_name in enumerate(column_names):
                row[col_name] = cols[j]['values'][i]
            rows.append(row)
        return rows
    print(f"Query error: {r.status_code} - {r.text[:200]}")
    return []


def main():
    print("Finding Arcee-AI usage in recent logs...")
    
    # Try using the specific column if it exists, otherwise fall back to searching "attributes"
    sql = """
        SELECT start_timestamp, message, attributes
        FROM records 
        WHERE attributes LIKE '%arcee%' 
           OR message LIKE '%arcee%'
        ORDER BY start_timestamp DESC 
        LIMIT 10
    """
    
    rows = query(sql)
    
    if not rows:
        print("No logs found explicitly mentioning 'arcee' in the recent past.")
    else:
        print(f"Found {len(rows)} records with 'arcee':")
        for row in rows:
            print(f"[{row['start_timestamp']}] {row['message']}")
            print(f"Attributes: {str(row['attributes'])[:200]}...")
            print("-" * 50)

    # Check model usage distribution
    print("\nRecent Model Usage (last 1 hour):")
    # Note: Column names with dots/slashes usually need double quotes in SQL
    sql_models = """
        SELECT "_lf_attributes/gen_ai.request.model" as model, count(*) as count
        FROM records
        WHERE start_timestamp > now() - interval '1 hour'
          AND "_lf_attributes/gen_ai.request.model" IS NOT NULL
        GROUP BY 1
        ORDER BY 2 DESC
    """
    
    rows_models = query(sql_models)
    
    if rows_models:
        for r in rows_models:
            print(f"  • {r['model']}: {r['count']} calls")
    else:
        print("  No model usage found in the last hour via '_lf_attributes/gen_ai.request.model'.")

if __name__ == "__main__":
    main()
