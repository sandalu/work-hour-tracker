# 🕐 Work Hour Tracker

A command-line app to track work hours and stay within the Australian student visa 48hr/fortnight limit.

Built with Python and Docker as part of my DevOps learning journey.

## 🌐 Live Demo
Access the app at: http://3.27.241.208

## 🛠️ Tech Stack
- Python 3.11
- Docker

## 🚀 How to Run

### With Docker (recommended)
```bash
docker build -t work-hour-tracker .
docker run -it -v $(pwd)/data:/app/data work-hour-tracker
```

### Without Docker
```bash
cd src
python tracker.py
```

## ✨ Features
- Log work hours by job/company
- Tracks hours within current 14-day fortnight
- Warns at 80% of visa limit
- Alerts when limit is reached
- Persistent data storage

## 📚 What I Learned
- Python project structure
- Docker containerisation
- Docker volumes for data persistence
- Git version control