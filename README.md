# 🌦️ MAUSAM – AI-Ready Weather Dashboard

MAUSAM is a full-stack weather dashboard built using **Python Flask** and **JavaScript** that provides real-time weather information, air quality insights, hourly forecasts, and 7-day weather predictions. The application integrates live weather data from the Open-Meteo APIs and presents it through a clean, responsive interface with intelligent weather recommendations.

---

## 🚀 Features

- 🌍 Search weather by city name
- 🌡️ Real-time temperature and weather conditions
- 💨 Wind speed, humidity, and atmospheric pressure
- 🌅 Sunrise and sunset timings
- 🌧️ 24-hour weather forecast
- 📅 7-day weather forecast
- 🌫️ Air Quality Index (AQI) analysis
- 🇮🇳 Indian Ritu (Season) detection
- 👕 Smart clothing recommendations
- ❤️ Health and weather advisory
- 📱 Responsive and user-friendly interface

---

## 🛠️ Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript
- Fetch API

### Backend
- Python
- Flask

### APIs
- Open-Meteo Weather API
- Open-Meteo Geocoding API
- Open-Meteo Air Quality API

### Tools
- Git
- GitHub

---

## 📂 Project Structure

```
MAUSAM/
│
├── app.py
├── weather_engine.py
├── requirements.txt
├── Makefile
├── README.md
├── .gitignore
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
│
└── templates/
    └── index.html
```

---

## ⚙️ Installation

### Clone the repository

```bash
git clone https://github.com/shivamakashproj/MAUSAM.git
```

### Navigate to the project

```bash
cd MAUSAM
```

### Create and activate a virtual environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the application

```bash
python app.py
```

Open your browser and visit:

```
http://127.0.0.1:5000
```

---

## 🔄 Application Workflow

1. User enters a city name.
2. Flask receives the request.
3. The Geocoding API converts the city name into latitude and longitude.
4. The Weather API retrieves current weather and forecast data.
5. The Air Quality API fetches pollution data.
6. Backend processes and formats the data.
7. JavaScript dynamically updates the dashboard without reloading the page.

---

## 💡 Key Highlights

- REST API integration with Open-Meteo services
- Modular Flask backend architecture
- Dynamic frontend using Fetch API
- Real-time weather and AQI visualization
- Intelligent weather interpretation and recommendations
- Clean separation of frontend and backend logic

---

## 📈 Future Enhancements

- 🎤 Voice-enabled weather assistant
- 📍 Automatic location detection
- 🌐 Multi-language support
- ⭐ Favorite cities
- 📊 Weather history and analytics
- ⚠️ Severe weather alerts
- 🤖 AI-powered natural language weather assistant

---

## 👨‍💻 Author

**Shivam**

- GitHub: https://github.com/shivamakashproj
- Project: https://github.com/shivamakashproj/MAUSAM

---

## ⭐ Support

If you found this project useful, consider giving it a **⭐ Star** on GitHub!
