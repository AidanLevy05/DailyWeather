import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

WEATHER_API = 'visual-crossing-api-key'
CITY_ONE = 'CITY_ONE_HERE'
CITY_TWO = 'CITY_TWO_HERE'
WEATHER_URL_ONE = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{CITY_ONE}?key={WEATHER_API}"
WEATHER_URL_TWO = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{CITY_TWO}?key={WEATHER_API}"

EMAIL_ADDRESS = "your-email"
EMAIL_PASSWORD = "your-password"

TRAFFIC_API = 'tom-tom-api-key'
ORIGIN = 'long,lat'
DESTINATION = 'long,lat'

strong_breeze = False
rain_cities = {}
thunder_cities = {}

def get_weather(url, city):

    global strong_breeze, rain_cities, thunder_cities

    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        if 'days' in weather_data:
            today = weather_data['days'][0]
            hourly_data = today['hours']
            weather_at_times = {}
            for hour in hourly_data:
                time = hour['datetime']
                if time in ['06:00:00', '12:00:00', '18:00:00']:

                    wind_speed = hour['windspeed']
                    conditions = hour['conditions']

                    if wind_speed >= 15:
                        strong_breeze = True
                    if "Rain" in conditions:
                        rain_cities[city] = True
                    if "Thunder" in conditions:
                        thunder_cities[city] = True

                    weather_at_times[time] = {
                        'temperature': hour['temp'],
                        'wind_speed': hour['windspeed']
                    }

            return weather_at_times
    return None

def get_travel_time():
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{ORIGIN}:{DESTINATION}/json?key={TRAFFIC_API}&traffic=true"
    response = requests.get(url)
    if response.status_code == 200:
        route_data = response.json()
        if route_data['routes']:
            travel_time_in_seconds = route_data['routes'][0]['summary']['travelTimeInSeconds']
            travel_time_in_minutes = travel_time_in_seconds // 60
            return f"\nEstimated travel time to {CITY_TWO}: {travel_time_in_minutes} minutes.\n"
        else:
            return "\nNo routes found in the response."
    else:
        return f"\nFailed to get travel time. Status code: {response.status_code}, Response: {response.text}"


def format_weather_email(w1, w2):

    global strong_breeze, rain_cities, thunder_cities

    message = MIMEMultipart()
    message['From'] = EMAIL_ADDRESS
    message['To'] = EMAIL_ADDRESS
    message['Subject'] = 'Weather Update'

    body = f"Good morning, YOUR_NAME_HERE!\n\n"

    # display date and time
    now = datetime.now()
    day_of_week = now.strftime("%A")
    date = now.strftime("%m/%d/%Y")
    body += f"Today is {day_of_week}, {date}.\n\n"

    # get weather in your cities
    body += f"Weather for {CITY_ONE}:\n"
    for time, data in w1.items():
        body += f"\t{time} | Temp: {data['temperature']}°F | Wind: {data['wind_speed']}mph\n"

    body += f"\nWeather for {CITY_TWO}:\n"
    for time, data in w2.items():
        body += f"\t{time} | Temp: {data['temperature']}°F | Wind: {data['wind_speed']}mph\n"

    # weather conditions
    if strong_breeze:
        body += "\nThere will be a strong breeze."
    if rain_cities:
        body += "\nCities with rain:\n"
        for city in rain_cities:
            body += f"\t{city}\n"
    if thunder_cities:
        body += "\nCities with thunderstorms:\n"
        for city in thunder_cities:
            body += f"\t{city}\n"

    # travel times
    travel_time = get_travel_time()
    body += travel_time

    # attach message
    message.attach(MIMEText(body, 'plain'))
    return message

def send_email(message):
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(message)

if __name__ == "__main__":
    weather_one = get_weather(WEATHER_URL_ONE, CITY_ONE)
    weather_two = get_weather(WEATHER_URL_TWO, CITY_TWO)

    if weather_one and weather_two:
        email_message = format_weather_email(weather_one, weather_two)
        send_email(email_message)
        print("Message sent!")
