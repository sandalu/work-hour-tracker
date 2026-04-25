from flask import Flask, render_template, request, redirect, url_for, send_file
import sys
import os
import calendar
from collections import defaultdict
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

@app.route('/analytics')
def analytics():
    academic_start = get_academic_start()
    if not academic_start:
        return redirect(url_for('setup'))

    data = load_data()
    all_entries = data["entries"]
    range_param = request.args.get('range', 'semester')
    today = date.today()

    # Filter entries by range
    if range_param == 'current':
        start_filter, end_filter = get_fortnight_by_offset(0)
    elif range_param == 'month':
        start_filter = today - timedelta(days=30)
        end_filter = today
    elif range_param == '3months':
        start_filter = today - timedelta(days=90)
        end_filter = today
    elif range_param == 'all':
        start_filter = academic_start
        end_filter = today
    else:  # semester default
        start_filter = academic_start
        end_filter = today

    filtered = []
    for entry in all_entries:
        date_key = entry.get("work_date", entry["date"])
        entry_date = dt.strptime(date_key, "%Y-%m-%d").date()
        if start_filter <= entry_date <= end_filter:
            filtered.append(entry)

    # Summary calculations
    total_hours = round(sum(e["hours"] for e in filtered), 2)
    semester_hours = round(sum(e["hours"] for e in filtered if not e.get("is_break", False)), 2)
    break_hours = round(sum(e["hours"] for e in filtered if e.get("is_break", False)), 2)
    total_shifts = len(filtered)

    # Average per fortnight
    days_range = max((end_filter - start_filter).days, 14)
    fortnights = days_range / 14
    avg_per_fortnight = round(semester_hours / fortnights, 2) if fortnights > 0 else 0

    # Busiest day
    day_hours = defaultdict(float)
    for entry in filtered:
        day_hours[entry.get("work_date", entry["date"])] += entry["hours"]
    busiest_day = max(day_hours, key=day_hours.get) if day_hours else None

    summary = {
        "total_hours": total_hours,
        "semester_hours": semester_hours,
        "break_hours": break_hours,
        "total_shifts": total_shifts,
        "avg_per_fortnight": avg_per_fortnight,
        "busiest_day": busiest_day
    }

    # Hours per fortnight chart
    fortnight_data = defaultdict(float)
    for entry in filtered:
        if entry.get("is_break", False):
            continue
        date_key = entry.get("work_date", entry["date"])
        entry_date = dt.strptime(date_key, "%Y-%m-%d").date()
        # Find which fortnight this belongs to
        days_from_start = (entry_date - academic_start).days
        fortnight_num = days_from_start // 14
        f_start = academic_start + timedelta(days=fortnight_num * 14)
        f_end = f_start + timedelta(days=13)
        label = f"{f_start.strftime('%d %b')} - {f_end.strftime('%d %b')}"
        fortnight_data[label] += entry["hours"]

    fortnight_labels = list(fortnight_data.keys())
    fortnight_hours = [round(v, 2) for v in fortnight_data.values()]

    # Hours per job chart
    job_data = defaultdict(float)
    for entry in filtered:
        job_data[entry["job"]] += entry["hours"]
    job_labels = list(job_data.keys())
    job_hours = [round(v, 2) for v in job_data.values()]

    # Hours per week chart
    week_data = defaultdict(float)
    for entry in filtered:
        date_key = entry.get("work_date", entry["date"])
        entry_date = dt.strptime(date_key, "%Y-%m-%d").date()
        week_start = entry_date - timedelta(days=entry_date.weekday())
        label = week_start.strftime("%d %b")
        week_data[label] += entry["hours"]
    week_labels = list(week_data.keys())
    week_hours = [round(v, 2) for v in week_data.values()]

    chart_data = {
        "fortnight_labels": fortnight_labels,
        "fortnight_hours": fortnight_hours,
        "job_labels": job_labels,
        "job_hours": job_hours,
        "week_labels": week_labels,
        "week_hours": week_hours,
        "break_data": [semester_hours, break_hours]
    }

    return render_template('analytics.html',
        range=range_param,
        summary=summary,
        chart_data=chart_data
    )

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)