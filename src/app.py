from flask import Flask, render_template, request, redirect, url_for
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tracker import log_hours, get_fortnightly_hours, load_data
from config import FORTNIGHTLY_HOUR_LIMIT, ALERT_THRESHOLD

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

@app.route('/')
def index():
    total = get_fortnightly_hours()
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

    # Get history
    data = load_data()
    entries = sorted(data["entries"], key=lambda x: x["date"], reverse=True)

    return render_template('index.html',
        total=total,
        remaining=remaining,
        percentage=percentage,
        limit=FORTNIGHTLY_HOUR_LIMIT,
        status=status,
        message=message,
        entries=entries
    )

@app.route('/log', methods=['POST'])
def log():
    job = request.form.get('job')
    hours = float(request.form.get('hours'))
    log_hours(hours, job)
    return redirect(url_for('index'))

@app.route('/delete/<int:index>', methods=['POST'])
def delete(index):
    data = load_data()
    entries = sorted(data["entries"], key=lambda x: x["date"], reverse=True)
    
    # Find the actual entry to delete
    entry_to_delete = entries[index]
    
    # Remove it from original data
    data["entries"].remove(entry_to_delete)
    
    from tracker import save_data
    save_data(data)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)