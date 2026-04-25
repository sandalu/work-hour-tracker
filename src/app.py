from flask import Flask, render_template, request, redirect, url_for
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tracker import log_hours, get_fortnightly_hours, load_data, get_fortnight_start, get_fortnight_end, get_fortnight_by_offset, get_fortnightly_hours_by_offset
from config import FORTNIGHTLY_HOUR_LIMIT, ALERT_THRESHOLD

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

@app.route('/')
def index():
    offset = int(request.args.get('offset', 0))
    
    # Clamp offset to 0 max (can't go to future)
    if offset > 0:
        offset = 0

    total = get_fortnightly_hours_by_offset(offset)
    remaining = FORTNIGHTLY_HOUR_LIMIT - total
    percentage = round((total / FORTNIGHTLY_HOUR_LIMIT) * 100, 1)

    # Determine status
    if percentage >= 100:
        status = "danger"
        message = "🚨 Limit reached! Stop working immediately!"
    elif percentage >= ALERT_THRESHOLD * 100:
        status = "warning"
        message = f"⚠️ Warning! You've used {percentage}% of your limit!"
    else:
        status = "safe"
        message = f"✅ You're safe — {remaining} hours remaining"

    # Get fortnight dates
    fortnight_start, fortnight_end = get_fortnight_by_offset(offset)
    is_current = offset == 0

    # Get history for this fortnight only
    data = load_data()
    all_entries = data["entries"]
    filtered_entries = []
    for entry in all_entries:
        date_key = entry.get("work_date", entry["date"])
        from datetime import datetime as dt
        entry_date = dt.strptime(date_key, "%Y-%m-%d").date()
        if fortnight_start <= entry_date <= fortnight_end:
            filtered_entries.append(entry)

    entries = sorted(filtered_entries, key=lambda x: x.get("work_date", x["date"]), reverse=True)

    return render_template('index.html',
        total=total,
        remaining=max(remaining, 0),
        percentage=percentage,
        limit=FORTNIGHTLY_HOUR_LIMIT,
        status=status,
        message=message,
        entries=entries,
        fortnight_start=fortnight_start.strftime("%d %b %Y"),
        fortnight_end=fortnight_end.strftime("%d %b %Y"),
        offset=offset,
        is_current=is_current
    )

@app.route('/log', methods=['POST'])
def log():
    job = request.form.get('job')
    hours = float(request.form.get('hours'))
    work_date = request.form.get('work_date')
    log_hours(hours, job, work_date)
    return redirect(url_for('index'))

@app.route('/delete/<int:index>', methods=['POST'])
def delete(index):
    # Only allow delete on current fortnight
    fortnight_start, fortnight_end = get_fortnight_by_offset(0)
    data = load_data()

    # Get current fortnight entries only
    current_entries = []
    for entry in data["entries"]:
        date_key = entry.get("work_date", entry["date"])
        from datetime import datetime as dt
        entry_date = dt.strptime(date_key, "%Y-%m-%d").date()
        if fortnight_start <= entry_date <= fortnight_end:
            current_entries.append(entry)

    current_entries = sorted(current_entries, key=lambda x: x.get("work_date", x["date"]), reverse=True)

    if index < len(current_entries):
        entry_to_delete = current_entries[index]
        data["entries"].remove(entry_to_delete)
        from tracker import save_data
        save_data(data)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)