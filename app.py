from flask import Flask, render_template, request, jsonify
import weather_engine

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/weather')
def get_weather():
    city = request.args.get('city')
    lat_str = request.args.get('lat')
    lon_str = request.args.get('lon')
    
    if city:
        data = weather_engine.get_weather_data(city_name=city.strip())
        return jsonify(data)
    elif lat_str and lon_str:
        try:
            lat = float(lat_str)
            lon = float(lon_str)
            data = weather_engine.get_weather_data(lat=lat, lon=lon)
            return jsonify(data)
        except ValueError:
            return jsonify({"error": "Invalid latitude or longitude format"}), 400
    else:
        # Default fallback to New Delhi if nothing specified
        data = weather_engine.get_weather_data(city_name="New Delhi")
        return jsonify(data)

if __name__ == '__main__':
    # Start the server locally
    app.run(debug=True, port=5000)
