import os
import requests
import datetime
import time
import threading
from dotenv import load_dotenv

# Load .env variables (safe to call multiple times)
load_dotenv()

# Optional: Open-Meteo customer/pro API key.
# Leave this empty for the current free Open-Meteo endpoint.
OPEN_METEO_API_KEY = os.environ.get("OPEN_METEO_API_KEY", "").strip()

# ---------------------------------------------------------------------------
# FUTURE API TEMPLATE — COMMENTED ON PURPOSE
# ---------------------------------------------------------------------------
# If you get another weather API in the future, DO NOT put the key here.
# Add it to your local .env / Render Environment Variables instead.
#
# Example:
# WEATHER_API_KEY=your_real_key_here
#
# Then uncomment/adapt the provider-specific code below:
#
# FUTURE_WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "").strip()
# FUTURE_WEATHER_URL = "https://YOUR-WEATHER-PROVIDER-ENDPOINT"
# headers = {"Authorization": f"Bearer {FUTURE_WEATHER_API_KEY}"}
# response = requests.get(FUTURE_WEATHER_URL, headers=headers, timeout=10)
# response.raise_for_status()
# data = response.json()
#
# IMPORTANT: Every weather provider has a different URL, authentication
# method, and JSON structure. Configure this section only after choosing
# the provider. Keep the API key in an environment variable, never GitHub.
# ---------------------------------------------------------------------------

# Dependency-free in-memory cache for localhost and Render.
# Weather/AQI: 1 hour. Geocoding: 24 hours.
# A previous successful result may be served for up to 6 hours when
# Open-Meteo temporarily returns 429/5xx or a network error.
_WEATHER_CACHE = {}
_GEOCODE_CACHE = {}
_CACHE_LOCK = threading.Lock()
WEATHER_CACHE_TTL = 60 * 60
WEATHER_STALE_TTL = 6 * 60 * 60
GEOCODE_CACHE_TTL = 24 * 60 * 60


def _cache_get(cache, key, ttl, allow_stale=False):
    with _CACHE_LOCK:
        item = cache.get(key)
    if not item:
        return None, False
    age = time.time() - item["saved_at"]
    if age <= ttl:
        return item["data"], True
    if allow_stale and age <= WEATHER_STALE_TTL:
        return item["data"], False
    with _CACHE_LOCK:
        cache.pop(key, None)
    return None, False


def _cache_set(cache, key, data):
    with _CACHE_LOCK:
        cache[key] = {"saved_at": time.time(), "data": data}

# Indian Seasons (Ritus) Calculation
def get_indian_ritu(date_obj):
    month = date_obj.month
    day = date_obj.day
    
    # Ritus boundary definitions (approximate dates in Hindu calendar mapped to Gregorian)
    if (month == 2 and day >= 19) or month == 3 or (month == 4 and day <= 19):
        return {
            "name_sanskrit": "Vasanta (वसन्त)",
            "name_english": "Spring",
            "desc": "The season of rejuvenation, blooming flowers, pleasant breezes, and mustard fields in gold.",
            "element": "spring"
        }
    elif (month == 4 and day >= 20) or month == 5 or (month == 6 and day <= 21):
        return {
            "name_sanskrit": "Grishma (ग्रीष्म)",
            "name_english": "Summer",
            "desc": "The hot season of bright sun, dusty dry winds (Loo), and ripening mangoes.",
            "element": "summer"
        }
    elif (month == 6 and day >= 22) or month == 7 or (month == 8 and day <= 22):
        return {
            "name_sanskrit": "Varsha (वर्षा)",
            "name_english": "Monsoon / Rains",
            "desc": "The rainy season of dark thunderclouds, fresh green foliage, and cool rain showers.",
            "element": "monsoon"
        }
    elif (month == 8 and day >= 23) or month == 9 or (month == 10 and day <= 22):
        return {
            "name_sanskrit": "Sharad (शरद)",
            "name_english": "Autumn",
            "desc": "The pleasant autumn with clear blue skies, harvesting crops, and crisp moonlight nights.",
            "element": "spring" # reuse pleasant backdrop
        }
    elif (month == 10 and day >= 23) or month == 11 or (month == 12 and day <= 21):
        return {
            "name_sanskrit": "Hemant (हेमन्त)",
            "name_english": "Pre-winter",
            "desc": "The transition to winter with chilly morning dew, golden harvests, and cool nights.",
            "element": "winter" # reuse winter backdrop
        }
    else: # Dec 22 - Feb 18
        return {
            "name_sanskrit": "Shishir (शिशिर)",
            "name_english": "Winter",
            "desc": "The cold winter season with foggy mornings, cold northern winds, and warm fires.",
            "element": "winter"
        }

# CPCB Indian AQI Standard based on PM2.5 levels
def analyze_aqi(pm25, pm10=None):
    if pm25 <= 30:
        return {
            "category": "Good",
            "cpcb_color": "#2E7D32", # deep green
            "text_color": "#E8F5E9",
            "description": "Minimal health impact. Perfect weather for outdoor yoga and morning walks."
        }
    elif pm25 <= 60:
        return {
            "category": "Satisfactory",
            "cpcb_color": "#4CAF50", # light green
            "text_color": "#E8F5E9",
            "description": "May cause minor breathing discomfort to sensitive people. Fine for outdoor activities."
        }
    elif pm25 <= 90:
        return {
            "category": "Moderate",
            "cpcb_color": "#FBC02D", # yellow/amber
            "text_color": "#3E2723",
            "description": "May cause breathing discomfort to people with lung disease, asthma, and heart conditions."
        }
    elif pm25 <= 120:
        return {
            "category": "Poor",
            "cpcb_color": "#F57C00", # orange
            "text_color": "#FFF3E0",
            "description": "May cause breathing discomfort to most people on prolonged exposure. Avoid strenuous outdoor activities."
        }
    elif pm25 <= 250:
        return {
            "category": "Very Poor",
            "cpcb_color": "#D32F2F", # red
            "text_color": "#FFEBEE",
            "description": "May cause respiratory illness on prolonged exposure. Consider wearing a mask outdoors."
        }
    else:
        return {
            "category": "Severe",
            "cpcb_color": "#B71C1C", # dark red
            "text_color": "#FFEBEE",
            "description": "Healthy people may experience respiratory effects; serious impacts on those with existing diseases. Keep indoors."
        }

# WMO Weather Code Mapper
def map_weather_code(code):
    mapping = {
        0: {"desc": "Clear Skies", "icon": "bi-sun-fill", "class": "sunny"},
        1: {"desc": "Mainly Clear", "icon": "bi-cloud-sun-fill", "class": "sunny"},
        2: {"desc": "Partly Cloudy", "icon": "bi-cloud-sun", "class": "cloudy"},
        3: {"desc": "Overcast", "icon": "bi-clouds-fill", "class": "cloudy"},
        45: {"desc": "Foggy", "icon": "bi-cloud-fog-fill", "class": "foggy"},
        48: {"desc": "Depositing Rime Fog", "icon": "bi-cloud-fog2-fill", "class": "foggy"},
        51: {"desc": "Light Drizzle", "icon": "bi-cloud-drizzle", "class": "rainy"},
        53: {"desc": "Moderate Drizzle", "icon": "bi-cloud-drizzle-fill", "class": "rainy"},
        55: {"desc": "Heavy Drizzle", "icon": "bi-cloud-drizzle-fill", "class": "rainy"},
        56: {"desc": "Light Freezing Drizzle", "icon": "bi-cloud-snow", "class": "snowy"},
        57: {"desc": "Dense Freezing Drizzle", "icon": "bi-cloud-snow-fill", "class": "snowy"},
        61: {"desc": "Slight Rain", "icon": "bi-cloud-rain", "class": "rainy"},
        63: {"desc": "Moderate Rain", "icon": "bi-cloud-rain-fill", "class": "rainy"},
        65: {"desc": "Heavy Rain", "icon": "bi-cloud-rain-heavy-fill", "class": "rainy"},
        66: {"desc": "Light Freezing Rain", "icon": "bi-cloud-sleet-fill", "class": "snowy"},
        67: {"desc": "Heavy Freezing Rain", "icon": "bi-cloud-sleet-fill", "class": "snowy"},
        71: {"desc": "Slight Snowfall", "icon": "bi-cloud-snow", "class": "snowy"},
        73: {"desc": "Moderate Snowfall", "icon": "bi-cloud-snow-fill", "class": "snowy"},
        75: {"desc": "Heavy Snowfall", "icon": "bi-cloud-snow-heavy", "class": "snowy"},
        77: {"desc": "Snow Grains", "icon": "bi-cloud-snow", "class": "snowy"},
        80: {"desc": "Slight Rain Showers", "icon": "bi-cloud-rain", "class": "rainy"},
        81: {"desc": "Moderate Rain Showers", "icon": "bi-cloud-rain-fill", "class": "rainy"},
        82: {"desc": "Violent Rain Showers", "icon": "bi-cloud-rain-heavy", "class": "rainy"},
        85: {"desc": "Slight Snow Showers", "icon": "bi-cloud-snow", "class": "snowy"},
        86: {"desc": "Heavy Snow Showers", "icon": "bi-cloud-snow-heavy-fill", "class": "snowy"},
        95: {"desc": "Thunderstorm", "icon": "bi-cloud-lightning-rain-fill", "class": "stormy"},
        96: {"desc": "Thunderstorm with Slight Hail", "icon": "bi-cloud-lightning-rain-fill", "class": "stormy"},
        99: {"desc": "Thunderstorm with Heavy Hail", "icon": "bi-cloud-lightning-rain-fill", "class": "stormy"},
    }
    return mapping.get(code, {"desc": "Unknown Weather", "icon": "bi-question-circle", "class": "sunny"})

# Generate realistic live weather status text based on weather code and conditions
def get_live_weather_status(weather_code, temp, rain_mm, wind_speed, is_day):
    """Returns a realistic, human-readable weather status string with emoji."""
    
    # Thunderstorms
    if weather_code in [95, 96, 99]:
        if weather_code == 99:
            return {"text": "⛈️ Severe thunderstorm with hail — Stay indoors!", "type": "stormy"}
        return {"text": "⛈️ Thunderstorm in progress — Take shelter!", "type": "stormy"}
    
    # Snow
    if weather_code in [71, 73, 75, 77, 85, 86]:
        if weather_code in [75, 86]:
            return {"text": "🌨️ Heavy snowfall right now — Roads may be slippery", "type": "snowy"}
        elif weather_code == 73:
            return {"text": "❄️ It's snowing moderately — Bundle up warmly", "type": "snowy"}
        return {"text": "🌨️ Light snowfall — A beautiful winter scene", "type": "snowy"}
    
    # Rain (heavy to light)
    if weather_code in [65, 82]:
        return {"text": "🌧️ It's raining heavily — Carry an umbrella & avoid low-lying areas", "type": "rainy"}
    if weather_code in [63, 81]:
        return {"text": "🌧️ Moderate rain right now — Keep your umbrella handy", "type": "rainy"}
    if weather_code in [61, 80]:
        return {"text": "🌦️ Light rain showers — A pleasant drizzle outside", "type": "rainy"}
    
    # Drizzle
    if weather_code in [55]:
        return {"text": "🌧️ Heavy drizzle — Roads may be wet and slippery", "type": "rainy"}
    if weather_code in [53]:
        return {"text": "🌦️ It's drizzling outside — Light moisture in the air", "type": "rainy"}
    if weather_code in [51]:
        return {"text": "💧 A fine drizzle — Barely noticeable but carry a light raincoat", "type": "rainy"}
    
    # Freezing rain/drizzle
    if weather_code in [56, 57, 66, 67]:
        return {"text": "🥶 Freezing rain — Extremely slippery conditions, stay safe", "type": "snowy"}
    
    # Fog
    if weather_code in [45, 48]:
        return {"text": "🌫️ Foggy conditions — Low visibility, drive carefully", "type": "foggy"}
    
    # Overcast
    if weather_code == 3:
        return {"text": "☁️ Overcast skies — A cloudy day with no direct sunlight", "type": "cloudy"}
    
    # Partly cloudy
    if weather_code == 2:
        if is_day:
            return {"text": "⛅ Partly cloudy — Sun peaking through the clouds", "type": "cloudy"}
        return {"text": "🌙 Partly cloudy night — Stars peeking through clouds", "type": "cloudy"}
    
    # Mainly clear
    if weather_code == 1:
        if is_day:
            if temp > 35:
                return {"text": "☀️ Mainly clear & scorching hot — Stay hydrated!", "type": "sunny"}
            return {"text": "🌤️ Mainly clear skies — A lovely day ahead", "type": "sunny"}
        return {"text": "🌙 Clear night with a few clouds — Pleasant stargazing weather", "type": "clear_night"}
    
    # Clear sky (code 0)
    if is_day:
        if temp > 40:
            return {"text": "🔥 Blazing hot sunshine — Extreme heat, avoid going outside", "type": "sunny"}
        elif temp > 35:
            return {"text": "☀️ Bright sunshine & very hot — Apply sunscreen, drink plenty of water", "type": "sunny"}
        elif temp > 28:
            return {"text": "☀️ Warm sunshine — Beautiful weather for outdoor activities", "type": "sunny"}
        elif temp > 20:
            return {"text": "🌤️ Pleasant sunny weather — Perfect day to step outside", "type": "sunny"}
        else:
            return {"text": "☀️ Cool and sunny — A crisp, clear day", "type": "sunny"}
    else:
        if temp > 30:
            return {"text": "🌙 Warm clear night — Still quite warm, stay cool", "type": "clear_night"}
        elif temp > 18:
            return {"text": "🌙 Clear starry night — Pleasant evening weather", "type": "clear_night"}
        else:
            return {"text": "🌙 Cool clear night — Wrap up if stepping out", "type": "clear_night"}


# Generate Indian-themed clothing and wellness recommendations (gender-specific)
def get_recommendations(temp, is_rainy, aqi_category, weather_code):
    tips = []
    clothing_men = []
    clothing_women = []
    
    # Rainy weather logic
    if is_rainy:
        tips.append("🍵 Monsoon Season essential — Sip hot 'Adrak Wali Chai' (Ginger Tea) with roasted corn (Bhutta). Avoid street food & raw salads to prevent waterborne infections.")
        tips.append("🌿 Boost immunity with Tulsi (Holy Basil) and Neem water. Keep your feet dry to avoid fungal infections.")
        clothing_men.append("Quick-dry polo t-shirt or synthetic kurta, waterproof sandals or gumboots, and a compact folding umbrella.")
        clothing_men.append("Avoid leather shoes & belts — they get damaged in rain. Carry a raincoat if commuting on two-wheeler.")
        clothing_women.append("Short kurti with churidar or ankle-length pants (avoid long dupattas). Waterproof flats or kolhapuri sandals.")
        clothing_women.append("Tie hair in a bun to avoid frizz. Carry a stylish umbrella and a waterproof tote bag for essentials.")
    
    # Temperature based recommendations
    if temp > 38:
        tips.append("🥵 Extreme heat alert! Drink 'Aam Panna' (raw mango drink), 'Sattu Sharbat', or ORS regularly. Avoid going out between 12–4 PM (peak Loo hours).")
        tips.append("🧊 Apply wet cloth on forehead & wrists. Eat light meals — curd rice, watermelon, cucumber raita are excellent choices.")
        clothing_men.append("White or pastel cotton kurta-pyjama or loose linen shirt with cotton trousers. Wear a cotton 'Gamchha' (towel) around the neck.")
        clothing_men.append("Open-toe leather sandals (Kolhapuri chappal), sunglasses, and a wide-brimmed hat or 'Pagdi' for sun protection.")
        clothing_women.append("Light cotton saree with a sleeveless blouse, or a breezy Anarkali kurta in pastel shades. Choose fabrics like Chanderi or Mul cotton.")
        clothing_women.append("Jute or straw sun hat, UV-protection sunglasses, and lightweight cotton dupatta to cover shoulders from direct sun.")
    elif temp > 33:
        tips.append("☀️ Stay hydrated with 'Jaljeera', sweet 'Lassi' (buttermilk), or refreshing 'Nimbu Pani'. Avoid excess caffeine and oily foods.")
        tips.append("💧 Keep a reusable water bottle (copper bottle ideal in Ayurveda). Apply SPF 30+ sunscreen before stepping out.")
        clothing_men.append("Breathable cotton half-sleeve shirts in light colors, linen trousers or cotton chinos. Avoid dark colors that absorb heat.")
        clothing_women.append("Light cotton kurta with palazzo pants, or a comfortable A-line kurti. Chiffon or georgette dupattas are ideal.")
    elif temp > 25:
        tips.append("🥥 Great weather for 'Nariyal Pani' (coconut water) or sugarcane juice from roadside vendors. Perfect for evening walks in the park.")
        clothing_men.append("Casual cotton kurta or polo t-shirt with comfortable jeans or cotton pants. Light canvas shoes or loafers.")
        clothing_women.append("Floral printed cotton kurti with leggings, or a comfortable salwar suit. Light cotton dupatta optional.")
    elif temp > 18:
        tips.append("🌸 Pleasant weather — Enjoy fresh 'Mosambi' (sweet lime) juice or seasonal citrus fruits. Perfect for outdoor yoga, jogging, or sightseeing.")
        clothing_men.append("Full-sleeve cotton shirt layered with a light Nehru jacket or linen blazer. Chinos or smart cotton trousers.")
        clothing_women.append("Layered cotton kurta with a light shrug or ethnic jacket. Comfortable block-heel juttis or ballet flats.")
    elif temp > 10:
        tips.append("🫖 Sip hot 'Haldi Doodh' (Golden Milk) or Ayurvedic 'Kadha' (herbal decoction with tulsi, ginger, black pepper). Keep ears covered in chilly winds.")
        tips.append("🧘 Practice 'Surya Namaskar' (Sun Salutation) in the morning to generate body warmth naturally.")
        clothing_men.append("Nehru jacket or sleeveless woolen waistcoat over a full-sleeve kurta. Warm socks with closed leather shoes. Light muffler for the neck.")
        clothing_women.append("Woolen shawl or Pashmina stole over a full-sleeve kurta. Warm leggings or churidar. Ankle boots or warm closed shoes.")
    else:
        tips.append("🔥 Consume 'Til' (sesame) laddoo and 'Gud' (jaggery) for natural body warmth — a traditional Indian winter remedy. Drink warm water throughout the day.")
        tips.append("🛏️ Use a 'Razai' (Indian quilt) at night. Apply mustard oil on joints before sleeping to prevent winter stiffness.")
        clothing_men.append("Heavy woolen jacket or leather bomber jacket over thermals. Kashmiri Phiran for extreme cold. Woolen cap, muffler, and warm gloves.")
        clothing_women.append("Kashmiri Phiran with kangri, or a long woolen coat over thermals. Woolen shawl (Kullu or Pashmina), warm gloves, and woolen socks with boots.")
        
    # AQI based advisory additions
    if aqi_category in ["Poor", "Very Poor", "Severe"]:
        tips.append("😷 High pollution alert — Practice 'Pranayama' (breathing exercises) indoors only. Use air purifier if available. Keep windows closed during peak traffic hours.")
        clothing_men.append("Wear an N95/KN95 mask outdoors. Full-sleeve clothing to minimize skin exposure to pollutants.")
        clothing_women.append("N95/KN95 mask essential when stepping out. Use a light scarf to cover hair from settling dust particles.")

    return {
        "tips": tips,
        "clothing_men": clothing_men,
        "clothing_women": clothing_women
    }
def get_weather_data(city_name=None, lat=None, lon=None):
    """Fetch Open-Meteo data with caching and graceful 429 fallback."""
    cache_key = None
    stale_result = None
    try:
        # 1) Geocode only when needed, and cache the result for 24 hours.
        if city_name:
            normalized_city = " ".join(city_name.strip().lower().split())
            geo_cached, _ = _cache_get(_GEOCODE_CACHE, normalized_city, GEOCODE_CACHE_TTL)
            if geo_cached:
                match = geo_cached
            else:
                geocode_url = (
                    "https://geocoding-api.open-meteo.com/v1/search"
                    f"?name={requests.utils.quote(city_name)}&count=5&language=en&format=json"
                )
                geo_response = requests.get(geocode_url, timeout=10)
                geo_response.raise_for_status()
                geo_data = geo_response.json()
                if "results" not in geo_data or not geo_data["results"]:
                    return {"error": f"City '{city_name}' not found. Please try another Indian city."}
                results = geo_data["results"]
                match = results[0]
                for r in results:
                    if r.get("country_code") == "IN":
                        match = r
                        break
                _cache_set(_GEOCODE_CACHE, normalized_city, match)
            lat = match["latitude"]
            lon = match["longitude"]
            location_name = match["name"]
            state = match.get("admin1", "")
            country = match.get("country", "")
            full_location = f"{location_name}, {state}" if state else location_name
            if country != "India" and country:
                full_location += f", {country}"
        else:
            if lat is None or lon is None:
                return {"error": "Please provide a city name or coordinates."}
            full_location = f"Coordinates ({lat:.2f}, {lon:.2f})"

        cache_key = f"{round(float(lat), 3)},{round(float(lon), 3)}"

        # 2) Fresh cache: no Open-Meteo calls at all.
        cached_result, _ = _cache_get(_WEATHER_CACHE, cache_key, WEATHER_CACHE_TTL)
        if cached_result:
            return cached_result

        # 3) Keep stale data as a fallback if the provider is temporarily unavailable.
        stale_result, _ = _cache_get(
            _WEATHER_CACHE, cache_key, WEATHER_STALE_TTL, allow_stale=True
        )

        api_key_param = f"&apikey={OPEN_METEO_API_KEY}" if OPEN_METEO_API_KEY else ""
        weather_url = (
            "https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m"
            "&hourly=temperature_2m,relative_humidity_2m,weather_code"
            "&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_probability_max"
            "&timezone=auto"
            f"{api_key_param}"
        )

        try:
            weather_response = requests.get(weather_url, timeout=10)
            weather_response.raise_for_status()
            weather_data = weather_response.json()
        except requests.RequestException as exc:
            if stale_result:
                print(f"Open-Meteo weather request failed ({exc}); serving cached data.")
                return stale_result
            raise

        if "current" not in weather_data:
            reason = weather_data.get("reason", "Unexpected response from weather API")
            if stale_result:
                print(f"Open-Meteo returned an unexpected response ({reason}); serving cached data.")
                return stale_result
            return {"error": f"Weather API error: {reason}"}

        # 4) AQI is also cached together with the weather result.
        aqi_url = (
            "https://air-quality-api.open-meteo.com/v1/air-quality?"
            f"latitude={lat}&longitude={lon}"
            "&current=pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone"
            f"{api_key_param}"
        )
        try:
            aqi_response = requests.get(aqi_url, timeout=10)
            aqi_response.raise_for_status()
            aqi_data = aqi_response.json()
        except requests.RequestException as exc:
            if stale_result:
                print(f"Open-Meteo AQI request failed ({exc}); serving cached data.")
                return stale_result
            raise

        if "current" not in aqi_data:
            reason = aqi_data.get("reason", "Unexpected response from AQI API")
            if stale_result:
                print(f"Open-Meteo returned an unexpected AQI response ({reason}); serving cached data.")
                return stale_result
            return {"error": f"AQI API error: {reason}"}

        # 5) Existing MAUSAM processing logic remains unchanged.
        current = weather_data["current"]
        temp = current["temperature_2m"]
        feels_like = current["apparent_temperature"]
        humidity = current["relative_humidity_2m"]
        w_code = current["weather_code"]
        wind_speed = current["wind_speed_10m"]
        rain = current["rain"] + current["showers"]
        is_rainy = rain > 0
        weather_mapped = map_weather_code(w_code)
        local_dt = datetime.datetime.fromisoformat(current["time"])
        ritu = get_indian_ritu(local_dt)

        pm25 = aqi_data["current"]["pm2_5"]
        pm10 = aqi_data["current"]["pm10"]
        co = aqi_data["current"]["carbon_monoxide"]
        no2 = aqi_data["current"]["nitrogen_dioxide"]
        so2 = aqi_data["current"]["sulphur_dioxide"]
        o3 = aqi_data["current"]["ozone"]
        aqi_analysis = analyze_aqi(pm25, pm10)
        recs = get_recommendations(temp, is_rainy, aqi_analysis["category"], w_code)
        weather_status = get_live_weather_status(
            w_code, temp, rain, wind_speed, current["is_day"]
        )

        # Hourly forecast (next 24 hours).
        hourly = weather_data["hourly"]
        current_iso = current["time"]
        current_time_index = 0
        for idx, t in enumerate(hourly["time"]):
            if t >= current_iso:
                current_time_index = idx
                break
        hourly_list = []
        for i in range(current_time_index, current_time_index + 24):
            if i >= len(hourly["time"]):
                break
            h_time = datetime.datetime.fromisoformat(hourly["time"][i])
            hourly_list.append({
                "time": h_time.strftime("%I %p"),
                "temp": round(hourly["temperature_2m"][i]),
                "humidity": hourly["relative_humidity_2m"][i],
                "weather": map_weather_code(hourly["weather_code"][i])
            })

        # Daily forecast.
        daily = weather_data["daily"]
        daily_list = []
        for i in range(len(daily["time"])):
            d_date = datetime.date.fromisoformat(daily["time"][i])
            daily_list.append({
                "day": d_date.strftime("%a"),
                "date": d_date.strftime("%b %d"),
                "temp_max": round(daily["temperature_2m_max"][i]),
                "temp_min": round(daily["temperature_2m_min"][i]),
                "rain_prob": daily["precipitation_probability_max"][i],
                "weather": map_weather_code(daily["weather_code"][i])
            })

        result = {
            "city": full_location, "latitude": lat, "longitude": lon,
            "temp": round(temp), "feels_like": round(feels_like),
            "humidity": humidity, "wind_speed": wind_speed,
            "weather_desc": weather_mapped["desc"],
            "weather_icon": weather_mapped["icon"],
            "weather_class": weather_mapped["class"],
            "is_day": current["is_day"], "ritu": ritu,
            "aqi": {
                "pm2_5": pm25, "pm10": pm10, "co": round(co, 1),
                "no2": round(no2, 1), "so2": round(so2, 1), "o3": round(o3, 1),
                "category": aqi_analysis["category"],
                "color": aqi_analysis["cpcb_color"],
                "text_color": aqi_analysis["text_color"],
                "desc": aqi_analysis["description"]
            },
            "tips": recs["tips"],
            "clothing_men": recs["clothing_men"],
            "clothing_women": recs["clothing_women"],
            "weather_status": weather_status,
            "sunrise": datetime.datetime.fromisoformat(daily["sunrise"][0]).strftime("%I:%M %p"),
            "sunset": datetime.datetime.fromisoformat(daily["sunset"][0]).strftime("%I:%M %p"),
            "hourly_forecast": hourly_list,
            "daily_forecast": daily_list
        }

        _cache_set(_WEATHER_CACHE, cache_key, result)
        return result

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        if stale_result:
            print("Serving stale cached weather data after unexpected error.")
            return stale_result
        return {"error": f"Failed to retrieve weather data: {str(e)}"}
