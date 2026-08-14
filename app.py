import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import weather_engine

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/weather")
def get_weather():
    city = request.args.get("city")
    lat_str = request.args.get("lat")
    lon_str = request.args.get("lon")

    if city:
        return jsonify(weather_engine.get_weather_data(city_name=city.strip()))

    if lat_str and lon_str:
        try:
            return jsonify(weather_engine.get_weather_data(lat=float(lat_str), lon=float(lon_str)))
        except ValueError:
            return jsonify({"error": "Invalid coordinates"}), 400

    return jsonify(weather_engine.get_weather_data(city_name="New Delhi"))


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug, host="0.0.0.0", port=port)
