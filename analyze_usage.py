#!/usr/bin/env python3
"""Analyze Cerebras usage patterns from CSV."""
import csv
from datetime import datetime

data = []
with open('cerebras_usage_NEW.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if int(row['Requests']) > 0:
            data.append({
                'time': datetime.fromisoformat(row['Time Start'].replace('Z', '+00:00')),
                'requests': int(row['Requests']),
                'input': int(row['Input Tokens']),
                'output': int(row['Output Tokens']),
                'total': int(row['Total Tokens']),
            })

# Group by session (gaps > 10 min = new session)
sessions = []
current_session = []
for i, row in enumerate(data):
    if i == 0 or (row['time'] - data[i-1]['time']).total_seconds() > 600:
        if current_session:
            sessions.append(current_session)
        current_session = [row]
    else:
        current_session.append(row)
if current_session:
    sessions.append(current_session)

print("=" * 70)
print("CEREBRAS USAGE ANALYSIS - Session by Session")
print("=" * 70)

total_input = sum(r['input'] for r in data)
total_output = sum(r['output'] for r in data)
total_requests = sum(r['requests'] for r in data)

print(f"\n📊 OVERALL TOTALS:")
print(f"   Total Requests: {total_requests:,}")
print(f"   Total Input Tokens: {total_input:,}")
print(f"   Total Output Tokens: {total_output:,}")
print(f"   Input:Output Ratio: {total_input/total_output:.1f}:1")
print(f"   Avg Input/Request: {total_input/total_requests:,.0f} tokens")

print(f"\n📅 SESSION BREAKDOWN ({len(sessions)} sessions):")
print("-" * 70)

for i, session in enumerate(sessions):
    start = session[0]['time']
    end = session[-1]['time']
    duration = (end - start).total_seconds() / 60
    
    s_requests = sum(r['requests'] for r in session)
    s_input = sum(r['input'] for r in session)
    s_output = sum(r['output'] for r in session)
    
    if s_requests > 0:
        avg_input = s_input / s_requests
        ratio = s_input / s_output if s_output > 0 else 0
        
        # Identify high-burn minutes (>500K input)
        high_burn = [r for r in session if r['input'] > 500000]
        
        print(f"\nSession {i+1}: {start.strftime('%Y-%m-%d %H:%M')} ({duration:.0f} min)")
        print(f"   Requests: {s_requests:,} | Input: {s_input:,} | Output: {s_output:,}")
        print(f"   Avg Input/Req: {avg_input:,.0f} | Ratio: {ratio:.0f}:1")
        if high_burn:
            print(f"   ⚠️  HIGH BURN MINUTES: {len(high_burn)} (>500K input)")
            
# Find peak usage minutes
print("\n" + "=" * 70)
print("🔥 TOP 10 HIGHEST TOKEN-BURN MINUTES:")
print("-" * 70)
sorted_data = sorted(data, key=lambda x: x['input'], reverse=True)[:10]
for row in sorted_data:
    avg = row['input'] // row['requests'] if row['requests'] > 0 else 0
    print(f"   {row['time'].strftime('%m-%d %H:%M')} | {row['requests']:2} reqs | {row['input']:>10,} input | {avg:>7,}/req")

# Calculate trend over sessions
print("\n" + "=" * 70)
print("📈 EFFICIENCY TREND (Avg Input/Request per Session):")
print("-" * 70)
for i, session in enumerate(sessions):
    s_requests = sum(r['requests'] for r in session)
    s_input = sum(r['input'] for r in session)
    if s_requests > 0:
        avg = s_input / s_requests
        bar = "█" * min(int(avg / 5000), 40)
        print(f"   Session {i+1:2}: {avg:>8,.0f} tokens/req  {bar}")

# Daily breakdown
print("\n" + "=" * 70)
print("📆 DAILY TOTALS:")
print("-" * 70)
daily = {}
for row in data:
    day = row['time'].strftime('%Y-%m-%d')
    if day not in daily:
        daily[day] = {'requests': 0, 'input': 0, 'output': 0}
    daily[day]['requests'] += row['requests']
    daily[day]['input'] += row['input']
    daily[day]['output'] += row['output']

for day, stats in sorted(daily.items()):
    pct = stats['input'] / 24_000_000 * 100  # 24M daily limit
    print(f"   {day}: {stats['requests']:,} reqs | {stats['input']:,} input ({pct:.1f}% of daily limit)")
