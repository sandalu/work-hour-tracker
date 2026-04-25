from flask import Flask, render_template, request, redirect, url_for, flash
import sys
import os
from datetime import datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tracker import (log_hours, get_fortnightly_hours_by_offset, load_data,
                     get_fortnight_by_offset, get_academic_start,
                     set_academic_start, is_before_academic_start, save_data)
from config import FORTNIGHTLY_HOUR_LIMIT, ALERT_THRESHOLD

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')

app.secret_key = 'workhourtracker2026'

@app.route('/')
def index():
    # Check if academic start is set
    academic_start = get_academic_start()
    if not academic_start:
        return redirect(url_for('setup'))

    offset = int(request.args.get('offset', 0))
    if offset > 0:
        offset = 0

    total = get_fortnightly_hours_by_offset(offset)
    remaining = FORTNIGHTLY_HOUR_LIMIT - total
    percentage = round((total / FORTNIGHTLY_HOUR_LIMIT) * 100, 1)

    if percentage >= 100:
        status = "danger"
        message = "🚨 Limit reached! Stop working immediately!"
    elif percentage >= ALERT_THRESHOLD * 100:
        status = "warning"
        message = f"⚠️ Warning! You've used {percentage}% of your limit!"
    else:
        status = "safe"
        message = f"✅ You're safe — {remaining} hours remaining"

    fortnight_start, fortnight_end = get_fortnight_by_offset(offset)
    is_current = offset == 0

    # Check if can go further back
    academic_start_date = get_academic_start()
    prev_start, _ = get_fortnight_by_offset(offset - 1)
    can_go_back = prev_start >= academic_start_date

    data = load_data()
    filtered_entries = []
    for entry in data["entries"]:
        date_key = entry.get("work_date", entry["date"])
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
        is_current=is_current,
        can_go_back=can_go_back,
        academic_start=academic_start_date.strftime("%d %b %Y"),
        error=request.args.get('error')
    )

@app.route('/log', methods=['POST'])
def log():
    job = request.form.get('job')
    hours = float(request.form.get('hours'))
    work_date = request.form.get('work_date')

    # Block if before academic start
    if is_before_academic_start(work_date):
        academic_start = get_academic_start()
        return redirect(url_for('index', error=f"❌ Cannot log hours before your academic start date ({academic_start.strftime('%d %b %Y')})"))

    log_hours(hours, job, work_date)
    return redirect(url_for('index'))

@app.route('/delete/<int:index>', methods=['POST'])
def delete(index):
    fortnight_start, fortnight_end = get_fortnight_by_offset(0)
    data = load_data()

    current_entries = []
    for entry in data["entries"]:
        date_key = entry.get("work_date", entry["date"])
        entry_date = dt.strptime(date_key, "%Y-%m-%d").date()
        if fortnight_start <= entry_date <= fortnight_end:
            current_entries.append(entry)

    current_entries = sorted(current_entries, key=lambda x: x.get("work_date", x["date"]), reverse=True)

    if index < len(current_entries):
        entry_to_delete = current_entries[index]
        data["entries"].remove(entry_to_delete)
        save_data(data)

    return redirect(url_for('index'))

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        academic_start = request.form.get('academic_start')
        set_academic_start(academic_start)
        return redirect(url_for('index'))
    return render_template('setup.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        academic_start = request.form.get('academic_start')
        set_academic_start(academic_start)
        return redirect(url_for('index'))
    current = get_academic_start()
    return render_template('settings.html', current_start=current.strftime("%Y-%m-%d") if current else "")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)