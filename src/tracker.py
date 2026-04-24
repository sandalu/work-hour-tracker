import json
import os
from datetime import datetime, date
from config import FORTNIGHTLY_HOUR_LIMIT, DATA_FILE, ALERT_THRESHOLD, APP_NAME

def load_data():
    """Load existing work hours from file"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, DATA_FILE)
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {"entries": []}

def save_data(data):
    """Save work hours to file"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, DATA_FILE)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def log_hours(hours, job_name):
    """Log work hours for today"""
    data = load_data()
    
    entry = {
        "date": str(date.today()),
        "hours": hours,
        "job": job_name
    }
    
    data["entries"].append(entry)
    save_data(data)
    print(f"✅ Logged {hours} hours for {job_name} on {date.today()}")

def get_fortnightly_hours():
    """Calculate total hours in the current fortnight"""
    data = load_data()
    today = date.today()
    total = 0

    for entry in data["entries"]:
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        days_diff = (today - entry_date).days
        if days_diff <= 14:
            total += entry["hours"]

    return total

def check_status():
    """Check your current hour status and warn if close to limit"""
    total = get_fortnightly_hours()
    remaining = FORTNIGHTLY_HOUR_LIMIT - total
    percentage = total / FORTNIGHTLY_HOUR_LIMIT

    print(f"\n📊 {APP_NAME} Status")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Hours worked (last 14 days): {total}hrs")
    print(f"Remaining hours:             {remaining}hrs")
    print(f"Limit:                       {FORTNIGHTLY_HOUR_LIMIT}hrs")

    if percentage >= 1:
        print(f"🚨 LIMIT REACHED! You have used all {FORTNIGHTLY_HOUR_LIMIT} hours!")
    elif percentage >= ALERT_THRESHOLD:
        print(f"⚠️  WARNING: You've used {total}hrs — getting close to your limit!")
    else:
        print(f"✅ You're safe — {remaining} hours remaining this fortnight.")

def show_history():
    """Show all logged entries"""
    data = load_data()
    
    if not data["entries"]:
        print("No entries yet.")
        return

    print(f"\n📋 Work History")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━")
    for entry in data["entries"]:
        print(f"  {entry['date']} | {entry['job']} | {entry['hours']}hrs")

def main():
    print(f"\nWelcome to {APP_NAME} 👋")
    print("1. Log hours")
    print("2. Check status")
    print("3. Show history")
    print("4. Exit")

    choice = input("\nChoose an option (1-4): ")

    if choice == "1":
        job = input("Job/Company name: ")
        hours = float(input("Hours worked: "))
        log_hours(hours, job)
        check_status()
    elif choice == "2":
        check_status()
    elif choice == "3":
        show_history()
    elif choice == "4":
        print("Goodbye! 👋")
    else:
        print("Invalid option.")

if __name__ == "__main__":
    main()