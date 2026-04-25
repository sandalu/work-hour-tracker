# 🕐 Work Hour Tracker

A web app to help Australian international students track their work hours and stay within the **48hr fortnightly visa limit**.

🌐 **Live App:** http://3.27.241.208

---

## 📸 Features

- ✅ Track work hours per job and date
- ✅ Automatic fortnight period calculation from academic start date
- ✅ Visual progress bar and hour limit warnings
- ✅ 🏖️ Semester break mode — pause the 48hr limit
- ✅ Navigate previous fortnights and history
- ✅ Interactive calendar showing worked days
- ✅ Hr/Min converter for delivery app payslips
- ✅ Export work history as PDF (for visa/tax purposes)
- ✅ Analytics dashboard with charts
- ✅ Delete incorrect entries

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Backend logic |
| Flask | Web framework |
| Docker | Containerisation |
| GitHub Actions | CI/CD pipeline |
| AWS EC2 | Cloud deployment |
| Chart.js | Analytics charts |
| ReportLab | PDF generation |
| pytest | Automated testing |

---

## 🚀 Run Locally

### With Docker (recommended)
```bash
docker build -t work-hour-tracker .
docker run -it -p 5000:5000 -v $(pwd)/data:/app/data work-hour-tracker
```

Then open: http://localhost:5000

### Without Docker
```bash
pip install -r requirements.txt
cd src
python app.py
```

---

## 🧪 Tests

```bash
pytest tests/ -v
```

22 automated tests covering all core features.

---

## 📁 Project Structure

---

## 👨‍💻 Author

Built by **Sandalu** — Data Science student at University of Canberra
- GitHub: [@sandalu](https://github.com/sandalu)
- LinkedIn: [https://www.linkedin.com/in/sandalusumudith/]

---

## 📄 License

MIT License