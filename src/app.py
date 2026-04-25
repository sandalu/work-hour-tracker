from flask import Flask, render_template, request, redirect, url_for, send_file
import sys
import os
import calendar
from datetime import date, timedelta, datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tracker import (log_hours, get_fortnightly_hours_by_offset, load_data,
                     get_fortnight_by_offset, get_academic_start,
                     set_academic_start, is_before_academic_start, save_data,
                     is_break_active, start_break, end_break, get_break_start)
from config import FORTNIGHTLY_HOUR_LIMIT, ALERT_THRESHOLD
from pdf_export import generate_pdf

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')

app.secret_key = 'workhourtracker2026'

def build_calendar(year, month, fortnight_start, fortnight_end, worked_dates):
    """Build calendar for a specific month"""
    today = date.today()
    cal = calendar.monthcalendar(year, month)
    days = []

    for week in cal:
        for day_num in week:
            if day_num == 0:
                days.append({"empty": True})
            else:
                current = date(year, month, day_num)
                days.append({
                    "empty": False,
                    "day": day_num,
                    "in_fortnight": fortnight_start <= current <= fortnight_end,
                    "worked": str(current) in worked_dates,
                    "is_today": current == today,
                })

    month_name = date(year, month, 1).strftime("%B %Y")

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    return {
        "name": month_name,
        "days": days,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    }

@app.route('/')
def index():
    academic_start = get_academic_start()
    if not academic_start:
        return redirect(url_for('setup'))

    offset = int(request.args.get('offset', 0))
    if offset > 0:
        offset = 0

    total = round(get_fortnightly_hours_by_offset(offset), 2)
    remaining = round(FORTNIGHTLY_HOUR_LIMIT - total, 2)
    percentage = round((total / FORTNIGHTLY_HOUR_LIMIT) * 100, 1)

    on_break = is_break_active()

    if on_break:
        status = "break"
        message = "🏖️ Semester Break — No hour limit active!"
    elif percentage >= 100:
        status = "danger"
        message = "🚨 Limit reached! Stop working immediately!"
    elif percentage >= ALERT_THRESHOLD * 100:
        status = "warning"
        message = f"⚠️ Warning! You've used {percentage}% of your limit!"
    else:
        status = "safe"
        message = f"✅ You're safe — {remaining:.2f} hours remaining"

    fortnight_start, fortnight_end = get_fortnight_by_offset(offset)
    is_current = offset == 0

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

    worked_dates = set(e.get("work_date", e["date"]) for e in filtered_entries)

    cal_year = int(request.args.get('cal_year', fortnight_start.year))
    cal_month = int(request.args.get('cal_month', fortnight_start.month))
    calendar_data = build_calendar(cal_year, cal_month, fortnight_start, fortnight_end, worked_dates)

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
        error=request.args.get('error'),
        calendar_data=calendar_data,
        on_break=on_break,
        break_start=get_break_start()
    )

@app.route('/log', methods=['POST'])
def log():
    job = request.form.get('job')
    hours = float(request.form.get('hours'))
    work_date = request.form.get('work_date')

    if is_before_academic_start(work_date):
        academic_start = get_academic_start()
        return redirect(url_for('index', error=f"Cannot log hours before your academic start date ({academic_start.strftime('%d %b %Y')})"))

    log_hours(hours, job, work_date)
    return redirect(url_for('index'))

@app.route('/delete/<int:index>', methods=['POST'])
def delete(index):
    offset = int(request.form.get('offset', 0))
    fortnight_start, fortnight_end = get_fortnight_by_offset(offset)
    data = load_data()

    period_entries = []
    for entry in data["entries"]:
        date_key = entry.get("work_date", entry["date"])
        entry_date = dt.strptime(date_key, "%Y-%m-%d").date()
        if fortnight_start <= entry_date <= fortnight_end:
            period_entries.append(entry)

    period_entries = sorted(period_entries, key=lambda x: x.get("work_date", x["date"]), reverse=True)

    if index < len(period_entries):
        entry_to_delete = period_entries[index]
        data["entries"].remove(entry_to_delete)
        save_data(data)

    return redirect(url_for('index', offset=offset))

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

@app.route('/toggle-break', methods=['POST'])
def toggle_break():
    if is_break_active():
        end_break()
    else:
        start_break()
    return redirect(url_for('index'))

@app.route('/export-pdf')
def export_pdf():
    offset = int(request.args.get('offset', 0))
    academic_start_date = get_academic_start()
    fortnight_start, fortnight_end = get_fortnight_by_offset(offset)
    on_break = is_break_active()

    total = round(get_fortnightly_hours_by_offset(offset), 2)
    remaining = round(FORTNIGHTLY_HOUR_LIMIT - total, 2)

    data = load_data()
    filtered_entries = []
    for entry in data["entries"]:
        date_key = entry.get("work_date", entry["date"])
        entry_date = dt.strptime(date_key, "%Y-%m-%d").date()
        if fortnight_start <= entry_date <= fortnight_end:
            filtered_entries.append(entry)

    entries = sorted(filtered_entries, key=lambda x: x.get("work_date", x["date"]), reverse=True)

    pdf_buffer = generate_pdf(
        entries=entries,
        total_hours=total,
        remaining_hours=remaining,
        fortnight_start=fortnight_start.strftime("%d %b %Y"),
        fortnight_end=fortnight_end.strftime("%d %b %Y"),
        academic_start=academic_start_date.strftime("%d %b %Y"),
        on_break=on_break
    )

    filename = f"work_hours_{fortnight_start.strftime('%Y%m%d')}_{fortnight_end.strftime('%Y%m%d')}.pdf"

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)