// DOM Elements
const searchForm = document.getElementById('search-form');
const cityInput = document.getElementById('city-input');
const geoBtn = document.getElementById('geo-btn');
const cityPills = document.querySelectorAll('.city-pill');

// Weather info elements
const currentCity = document.getElementById('current-city');
const currentDate = document.getElementById('current-date');
const currentTemp = document.getElementById('current-temp');
const weatherIcon = document.getElementById('weather-icon');
const weatherDesc = document.getElementById('weather-desc');
const feelsLike = document.getElementById('feels-like');

// Ritu elements
const rituTitle = document.getElementById('ritu-title');
const rituEnglish = document.getElementById('ritu-english');
const rituDesc = document.getElementById('ritu-desc');

// Tips and Clothing
const tipsList = document.getElementById('tips-list');
const clothingMenList = document.getElementById('clothing-men-list');
const clothingWomenList = document.getElementById('clothing-women-list');
const tabBtns = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');

// AQI elements
const aqiValue = document.getElementById('aqi-value');
const aqiBadge = document.getElementById('aqi-badge');
const aqiDesc = document.getElementById('aqi-desc');
const aqiCard = document.getElementById('aqi-card');

// Parameters
const sunriseVal = document.getElementById('sunrise-val');
const sunsetVal = document.getElementById('sunset-val');
const windVal = document.getElementById('wind-val');
const humidityVal = document.getElementById('humidity-val');

// Forecast container lists
const hourlyForecastList = document.getElementById('hourly-forecast-list');
const dailyForecastList = document.getElementById('daily-forecast-list');

// Chart instance
let tempChartInstance = null;

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    // Load default city (New Delhi)
    fetchWeatherByCity('New Delhi');
    
    // Set up search handler
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const city = cityInput.value.trim();
        if (city) {
            fetchWeatherByCity(city);
            // Deactivate quick city pills
            cityPills.forEach(p => p.classList.remove('active'));
        }
    });

    // Set up geo-location button
    geoBtn.addEventListener('click', () => {
        if (navigator.geolocation) {
            geoBtn.innerHTML = '<i class="bi bi-hourglass-split"></i>';
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    fetchWeatherByCoords(lat, lon);
                    // Deactivate pills
                    cityPills.forEach(p => p.classList.remove('active'));
                },
                (error) => {
                    console.error("Geolocation error:", error);
                    alert("Unable to fetch location. Please type your city in the search bar.");
                    geoBtn.innerHTML = '<i class="bi bi-geo-alt"></i>';
                }
            );
        } else {
            alert("Geolocation is not supported by your browser.");
        }
    });

    // Set up quick city pill handlers
    cityPills.forEach(pill => {
        pill.addEventListener('click', () => {
            cityPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            fetchWeatherByCity(pill.getAttribute('data-city'));
            cityInput.value = '';
        });
    });

    // Set up Guidance Tabs switcher
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(t => t.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            const targetPane = document.getElementById(`pane-${btn.getAttribute('data-tab')}`);
            if (targetPane) {
                targetPane.classList.add('active');
            }
        });
    });
});

// Fetch functions
async function fetchWeatherByCity(city) {
    showLoadingState();
    try {
        const response = await fetch(`/api/weather?city=${encodeURIComponent(city)}`);
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            resetLoadingState();
            hideLoader();
            return;
        }
        
        updateUI(data);
    } catch (err) {
        console.error("Fetch error:", err);
        alert("An error occurred while connecting to the Mausam server.");
        resetLoadingState();
        hideLoader();
    }
}

async function fetchWeatherByCoords(lat, lon) {
    showLoadingState();
    try {
        const response = await fetch(`/api/weather?lat=${lat}&lon=${lon}`);
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            resetLoadingState();
            hideLoader();
            return;
        }
        
        updateUI(data);
    } catch (err) {
        console.error("Fetch error:", err);
        alert("An error occurred while connecting to the Mausam server.");
        resetLoadingState();
        hideLoader();
    }
}

// UI Updating functions
function updateUI(data) {
    // 1. Reset loading icons and hide loader overlay
    resetLoadingState();
    hideLoader();
    
    // 2. Set Current Location details
    currentCity.textContent = data.city;
    
    // Format local date beautifully
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    currentDate.textContent = new Date().toLocaleDateString('en-IN', options);
    
    // 3. Current Weather metrics
    currentTemp.textContent = data.temp;
    feelsLike.textContent = `Feels like ${data.feels_like}°C`;
    weatherDesc.textContent = data.weather_desc;
    
    // Icon mapping logic adjustment
    weatherIcon.className = `bi ${data.weather_icon}`;
    
    // 4. Update Sanskrit Ritu
    rituTitle.textContent = data.ritu.name_sanskrit;
    rituEnglish.textContent = data.ritu.name_english;
    rituDesc.textContent = data.ritu.desc;
    
    // 5. Update Theme Background dynamically (realistic response)
    // If it's rainy, default to Varsha (Monsoon). If freezing, default to Shishir (Winter).
    // Otherwise, follow the calculated calendar Ritu.
    document.body.className = ''; // clear classes
    let activeTheme = `theme-${data.ritu.element}`;
    
    if (data.weather_class === 'rainy' || data.weather_class === 'stormy') {
        activeTheme = 'theme-monsoon';
    } else if (data.temp < 15) {
        activeTheme = 'theme-winter';
    } else if (data.temp > 32 && data.weather_class === 'sunny') {
        activeTheme = 'theme-summer';
    }
    document.body.classList.add(activeTheme);
    
    // 6. Update Guidance — Wellness Tips (with emojis already from backend)
    tipsList.innerHTML = data.tips.map(tip => `<li>${tip}</li>`).join('');
    
    // 6b. Update Guidance — Poshak Guide (gender-specific)
    clothingMenList.innerHTML = data.clothing_men.map(item => `<li>${item}</li>`).join('');
    clothingWomenList.innerHTML = data.clothing_women.map(item => `<li>${item}</li>`).join('');
    
    // 6c. Update Live Weather Status Banner
    const statusBanner = document.getElementById('weather-status-banner');
    const statusText = document.getElementById('weather-status-text');
    if (data.weather_status) {
        statusText.textContent = data.weather_status.text;
        // Apply status-type class for color styling
        statusBanner.className = 'weather-status-banner';
        statusBanner.classList.add(`status-${data.weather_status.type}`);
    }
    
    // 7. Update AQI Widget
    const aqi = data.aqi;
    aqiValue.textContent = Math.round(aqi.pm2_5);
    aqiBadge.textContent = aqi.category;
    aqiBadge.style.backgroundColor = aqi.color;
    aqiBadge.style.color = aqi.text_color;
    aqiDesc.textContent = aqi.desc;
    aqiCard.style.borderColor = aqi.color;
    aqiCard.style.boxShadow = `0 8px 32px 0 rgba(0, 0, 0, 0.25), 0 0 15px ${aqi.color}33`;
    
    // 8. Parameters Card details
    sunriseVal.textContent = data.sunrise;
    sunsetVal.textContent = data.sunset;
    windVal.textContent = `${data.wind_speed} km/h`;
    humidityVal.textContent = `${data.humidity}%`;
    
    // 9. Render Hourly list (horizontal scroll)
    hourlyForecastList.innerHTML = '';
    data.hourly_forecast.forEach(item => {
        const div = document.createElement('div');
        div.className = 'hourly-item';
        div.innerHTML = `
            <span class="hourly-time">${item.time}</span>
            <i class="bi ${item.weather.icon}"></i>
            <span class="hourly-temp">${item.temp}°C</span>
        `;
        hourlyForecastList.appendChild(div);
    });
    
    // 10. Update Chart.js temperature trend line
    renderTempChart(data.hourly_forecast);
    
    // 11. Render Daily outlook list (7 days)
    dailyForecastList.innerHTML = '';
    data.daily_forecast.forEach(item => {
        const div = document.createElement('div');
        div.className = 'daily-item';
        div.innerHTML = `
            <div class="daily-day-block">
                <span class="daily-day">${item.day}</span>
                <span class="daily-date">${item.date}</span>
            </div>
            <div class="daily-rain-prob" style="opacity: ${item.rain_prob > 10 ? 1 : 0.3}">
                <i class="bi bi-droplet-fill"></i> ${item.rain_prob}%
            </div>
            <div class="daily-weather-block">
                <i class="bi ${item.weather.icon}"></i>
                <span>${item.weather.desc}</span>
            </div>
            <div class="daily-temp-block">
                <span class="daily-temp-max">${item.temp_max}°C</span>
                <span class="daily-temp-min">${item.temp_min}°C</span>
            </div>
        `;
        dailyForecastList.appendChild(div);
    });
}

function renderTempChart(hourlyForecast) {
    const ctx = document.getElementById('tempTrendChart').getContext('2d');
    
    // Show chart container
    document.querySelector('.chart-container').style.display = 'block';
    
    // Extract labels (every 2nd hour to avoid overlap) and temperatures
    const labels = [];
    const temps = [];
    
    // Limit to next 12 hours for the charts to keep it clean
    const limitedData = hourlyForecast.slice(0, 12);
    
    limitedData.forEach(item => {
        labels.push(item.time);
        temps.push(item.temp);
    });
    
    if (tempChartInstance) {
        tempChartInstance.destroy();
    }
    
    // Get style custom color
    const activeColor = getComputedStyle(document.body).getPropertyValue('--accent').trim() || '#FF9933';
    
    tempChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Temperature (°C)',
                data: temps,
                borderColor: activeColor,
                borderWidth: 2,
                pointBackgroundColor: activeColor,
                pointHoverRadius: 6,
                tension: 0.4,
                fill: true,
                backgroundColor: createGradient(ctx, activeColor)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y}°C`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.5)',
                        font: {
                            size: 9
                        }
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.5)',
                        font: {
                            size: 9
                        }
                    }
                }
            }
        }
    });
}

function createGradient(ctx, color) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 120);
    gradient.addColorStop(0, `${color}33`);
    gradient.addColorStop(1, `${color}00`);
    return gradient;
}

// Helpers
function showLoadingState() {
    geoBtn.innerHTML = '<i class="bi bi-hourglass-split"></i>';
}

function resetLoadingState() {
    geoBtn.innerHTML = '<i class="bi bi-geo-alt"></i>';
}

function hideLoader() {
    const loader = document.getElementById('loader-wrapper');
    if (loader) {
        loader.classList.add('fade-out');
        setTimeout(() => loader.remove(), 600);
    }
}
