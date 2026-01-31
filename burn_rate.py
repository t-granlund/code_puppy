#!/usr/bin/env python3
"""Calculate Cerebras burn rate and efficiency comparison."""
import csv
from collections import defaultdict

DAILY_LIMIT = 24_000_000

daily = defaultdict(lambda: {'requests': 0, 'input': 0, 'output': 0, 'total': 0, 'minutes': 0})

with open('January-Cerebras-Usage-30.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ts = row['Time Start']
        day = ts.split('T')[0]
        tokens = int(row['Total Tokens'])
        if tokens > 0:
            daily[day]['requests'] += int(row['Requests'])
            daily[day]['input'] += int(row['Input Tokens'])
            daily[day]['output'] += int(row['Output Tokens'])
            daily[day]['total'] += tokens
            daily[day]['minutes'] += 1

# Daily breakdown
print()
print('=' * 75)
print('CEREBRAS I/O EFFICIENCY - Daily Breakdown')
print('=' * 75)

for day in sorted(daily.keys()):
    d = daily[day]
    input_per_min = d['input'] / d['minutes']
    output_per_min = d['output'] / d['minutes']
    io_ratio = d['input'] / d['output'] if d['output'] > 0 else 0
    pct = (d['total'] / DAILY_LIMIT) * 100
    
    print()
    print(f"DATE: {day}")
    print(f"   Requests:      {d['requests']:>8,}   |  Reqs/min:    {d['requests']/d['minutes']:>6.1f}")
    print(f"   Input tokens:  {d['input']:>12,}   |  Input/min:   {input_per_min:>12,.0f}")
    print(f"   Output tokens: {d['output']:>12,}   |  Output/min:  {output_per_min:>12,.0f}")
    print(f"   I/O Ratio:     {io_ratio:>12.1f}x  |  (lower = more efficient)")
    print(f"   % of 24M:      {pct:>11.2f}%")

# Compare today vs past days
past = [daily[d] for d in sorted(daily.keys())[:-1]]
today = daily[max(daily.keys())]
today_date = max(daily.keys())

avg_input_per_min = sum(d['input']/d['minutes'] for d in past) / len(past)
avg_output_per_min = sum(d['output']/d['minutes'] for d in past) / len(past)
avg_io_ratio = sum(d['input']/d['output'] for d in past) / len(past)
avg_input_per_req = sum(d['input']/d['requests'] for d in past) / len(past)

today_input_per_min = today['input'] / today['minutes']
today_output_per_min = today['output'] / today['minutes']
today_io_ratio = today['input'] / today['output']
today_input_per_req = today['input'] / today['requests']

print()
print('=' * 75)
print('EFFICIENCY COMPARISON: Jan 27-29 (before) vs Jan 30 (after changes)')
print('=' * 75)
print()
print(f"                         BEFORE (avg)        TODAY           CHANGE")
print(f"                         -----------        ------           ------")
print(f"  Input/min:         {avg_input_per_min:>12,.0f}    {today_input_per_min:>12,.0f}    {((today_input_per_min/avg_input_per_min)-1)*100:>+7.1f}%")
print(f"  Output/min:        {avg_output_per_min:>12,.0f}    {today_output_per_min:>12,.0f}    {((today_output_per_min/avg_output_per_min)-1)*100:>+7.1f}%")
print(f"  I/O Ratio:         {avg_io_ratio:>12.1f}x   {today_io_ratio:>12.1f}x   {((today_io_ratio/avg_io_ratio)-1)*100:>+7.1f}%")
print(f"  Input/request:     {avg_input_per_req:>12,.0f}    {today_input_per_req:>12,.0f}    {((today_input_per_req/avg_input_per_req)-1)*100:>+7.1f}%")

# Work capacity projection
before_tokens_per_req = sum(d['total']/d['requests'] for d in past) / len(past)
today_tokens_per_req = today['total'] / today['requests']
before_reqs_per_day = 24_000_000 / before_tokens_per_req
today_reqs_per_day = 24_000_000 / today_tokens_per_req

print()
print('=' * 75)
print('WORK CAPACITY PROJECTION (with 24M daily limit)')
print('=' * 75)
print()
print(f"  Avg tokens/request (before):  {before_tokens_per_req:>12,.0f}")
print(f"  Avg tokens/request (today):   {today_tokens_per_req:>12,.0f}")
print(f"  Change:                       {((today_tokens_per_req/before_tokens_per_req)-1)*100:>+11.1f}%")
print()
print(f"  Requests possible/day (before): {before_reqs_per_day:>10,.0f}")
print(f"  Requests possible/day (today):  {today_reqs_per_day:>10,.0f}")
print(f"  EFFICIENCY GAIN:                {((today_reqs_per_day/before_reqs_per_day)-1)*100:>+9.1f}%")
print()

# Output efficiency
before_output_pct = sum(d['output']/d['total'] for d in past) / len(past) * 100
today_output_pct = today['output'] / today['total'] * 100

print(f"  Output % of total (before):   {before_output_pct:>11.2f}%  (actual work)")
print(f"  Output % of total (today):    {today_output_pct:>11.2f}%  (actual work)")
print(f"  Output efficiency gain:       {((today_output_pct/before_output_pct)-1)*100:>+10.1f}%")

# Today projection
rate = today['total'] / today['minutes']
remaining = DAILY_LIMIT - today['total']
hrs = remaining / rate / 60

print()
print('=' * 75)
print(f"TODAY ({today_date}) - REMAINING CAPACITY")
print('=' * 75)
print(f"   Used so far:    {today['total']:>15,} tokens")
print(f"   Remaining:      {remaining:>15,} tokens")
print(f"   Current rate:   {rate:>15,.0f} tokens/min")
print(f"   Time to 24M:    {hrs:>15.1f} hours of active use")
print(f"   Requests left:  {remaining/today_tokens_per_req:>15,.0f} at today's efficiency")
print('=' * 75)
