from flask import Flask, render_template, request, redirect, url_for, jsonify

import requests

api_key = 'ZvwP1cZxIoDNRz2hopG2xphJcElCq337'
bot_token = ''


class WeatherForecast:
    def __init__(self, temperature, humidity, wind_speed, wind_probability):
        self.temperature = temperature
        self.humidity = humidity
        self.wind_speed = wind_speed
        self.wind_probability = wind_probability


def get_location_data(lat, lon):
    url = 'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search'
    params = {
        'q': f'{lat},{lon}',
        'apikey': api_key,
        'details': 'true'
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None


def get_current_forecast(key):
    url = f'http://dataservice.accuweather.com/currentconditions/v1/{key}'
    print(key)
    params = {
        'apikey': api_key,
        'details': 'true'
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        else:
            print("Ошибка: данные о погоде не получены или неверный формат")
            return None

        weather_forecast = WeatherForecast(
            temperature=data.get('Temperature', {}).get('Metric', {}).get('Value'),
            humidity=data.get('RelativeHumidity'),
            wind_speed=data.get('Wind', {}).get('Speed', {}).get('Metric', {}).get('Value'),
            wind_probability=data.get('PrecipitationSummary', {}).get('Precipitation', {}).get('Value', 0.0))

        return weather_forecast
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None
    except KeyError as e:
        print(f"Ошибка извлечения данных: {e}")
        return None


def five_days_forecast(key):
    url = f'http://dataservice.accuweather.com/currentconditions/v1/daily/5day/{key}'
    print(key)
    params = {
        'apikey': api_key,
        'details': 'true'
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        else:
            print("Ошибка: данные о погоде не получены или неверный формат")
            return None
        weather_forecasts = list()
        print(data)
        for item in data['DailyForecasts']:
            weather_forecast = WeatherForecast(
                temperature=item.get('Temperature', {}).get('Metric', {}).get('Value'),
                humidity=item.get('RelativeHumidity'),
                wind_speed=item.get('Wind', {}).get('Speed', {}).get('Metric', {}).get('Value'),
                wind_probability=item.get('PrecipitationSummary', {}).get('Precipitation', {}).get('Value', 0.0))
            weather_forecasts.append(weather_forecast)

        return weather_forecasts
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return []
    except KeyError as e:
        print(f"Ошибка извлечения данных: {e}")
        return None


def city_search(city):
    url = 'https://.accuweather.com/accuweather-locations-api/apis/get/locations/v1/cities/search'
    params = {
        'apikey': api_key,
        'q': city
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        print(data)
        return data['Key']
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None


def check_bad_weather(weather_forecast):
    if weather_forecast.temperature < 0 or weather_forecast.temperature > 35:
        return "Ой-ой, погода плохая!"
    elif weather_forecast.humidity > 50:
        return "Ой-ой, погода плохая!"
    elif weather_forecast.wind_probability > 0.7:
        return "Ой-ой, погода плохая!"
    return "Погода — супер!"


app = Flask(__name__)
upload_folder = 'templates'


@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = None
    if request.method == "POST":
        start_point = request.form["start_point"]
        end_point = request.form["end_point"]
        lat, lon = start_point.split(',')
        start_point_params = get_location_data(lat, lon)
        start_point_key = start_point_params['Key']
        lat, lon = end_point.split(',')
        end_point_params = get_location_data(lat, lon)
        end_point_key = end_point_params['Key']
        start_weather = get_current_forecast(start_point_key)
        end_weather = get_current_forecast(end_point_key)
        # 51.514,-0.107
        # 51.38,-2.361
        if not start_weather or not end_weather:
            return redirect(url_for("index"))

        start_weather_evaluation = check_bad_weather(start_weather)
        end_weather_evaluation = check_bad_weather(end_weather)

        weather_data = {
            "start_city": start_point_params['LocalizedName'],
            "end_city": end_point_params['LocalizedName'],
            "start_weather": start_weather_evaluation,
            "end_weather": end_weather_evaluation
        }

    return render_template("index.html", weather_data=weather_data)


if __name__ == "__main__":
    app.run(debug=True)
