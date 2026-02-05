#!/usr/bin/env python3
"""Inspect Logfire columns."""
import httpx
import json

READ_TOKEN = 'pylf_v1_us_S9j1Cb7vX0bCgZ0XSjZGBZqjc8dTgsDcvPYDGZfmhmZP'
BASE_URL = 'https://logfire-api.pydantic.dev/v1/query'


def query(sql: str) -> dict:
    """Execute SQL query against Logfire."""
    r = httpx.get(
        BASE_URL,
        headers={'Authorization': f'Bearer {READ_TOKEN}'},
        params={'sql': sql},
        timeout=30
    )
    if r.status_code == 200:
        return r.json()
    print(f"Query error: {r.status_code} - {r.text[:200]}")
    return {}


def main():
    print("Fetching columns from 'records' table...")
    
    # Just get one row to see columns
    data = query("SELECT * FROM records LIMIT 1")
    
    if data and 'columns' in data:
        print("Columns available:")
        for col in data['columns']:
            # Just print the name
            print(f"  - {col.get('name', 'UNKNOWN_NAME')}")
    else:
        print("Could not retrieve columns.")

if __name__ == "__main__":
    main()
