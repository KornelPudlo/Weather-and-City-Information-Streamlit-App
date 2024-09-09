import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# OpenWeatherMap API key
API_KEY = os.getenv('API_KEY')

# GeoNames API setup (replace with your GeoNames username)
GEONAMES_USERNAME = os.getenv('GEONAMES_USERNAME')

# Custom headers with a user agent for requests to Wikipedia
HEADERS = {
    "User-Agent": "CityInfoApp/1.0 (https://yourwebsite.com; contact@yourdomain.com)"
}


# Function to get real-time weather data using city name (always in Fahrenheit)
def get_weather_by_city(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=imperial"
    response = requests.get(url)
    return response.json()


# Function to get 5-day weather forecast using city name
def get_weather_forecast(city):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=imperial"
    response = requests.get(url)
    return response.json()


# Function to get air quality data using latitude and longitude
def get_air_quality(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    response = requests.get(url)
    return response.json()


# Function to get detailed city info from GeoNames API with logging and error handling
def get_city_details_geonames(city_name, username):
    url = f"http://api.geonames.org/searchJSON?q={city_name}&maxRows=1&username={username}"
    response = requests.get(url)

    # Check for valid response and handle errors
    if response.status_code == 200:
        data = response.json()
        # st.write(f"GeoNames API Response: {data}")  # Log the raw response

        if 'geonames' in data and data['geonames']:
            city_data = data['geonames'][0]
            return {
                "name": city_data.get("name", "N/A"),
                "country": city_data.get("countryName", "N/A"),
                "population": city_data.get("population", "N/A"),
                "timezone": city_data.get("timezone", {}).get("timeZoneId", "N/A"),
                "elevation": city_data.get("elevation", "N/A"),
                "lat": city_data.get("lat", "N/A"),
                "lng": city_data.get("lng", "N/A")
            }
        else:
            st.error("No city details found in GeoNames response.")
            return None
    else:
        st.error(f"Error fetching city details from GeoNames. Status Code: {response.status_code}")
        return None


# Function to fetch city description from Wikipedia using requests
def get_city_description_wikipedia(city_name):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{city_name.replace(' ', '_')}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data.get('extract', 'No description available.')
    return "No description available."


# Function to display real-time weather data
def display_weather_data(weather_data, col1):
    with col1:
        st.subheader(f"Weather in {weather_data['name']}, {weather_data['sys']['country']}")
        st.write(f"**Temperature**: {weather_data['main']['temp']} °F")
        st.write(f"**Weather**: {weather_data['weather'][0]['description'].capitalize()}")
        st.write(f"**Humidity**: {weather_data['main']['humidity']}%")
        st.write(f"**Wind Speed**: {weather_data['wind']['speed']} m/s")
        st.write(f"**Pressure**: {weather_data['main']['pressure']} hPa")
        st.write(f"**Sunrise**: {datetime.utcfromtimestamp(weather_data['sys']['sunrise']).strftime('%H:%M:%S')} UTC")
        st.write(f"**Sunset**: {datetime.utcfromtimestamp(weather_data['sys']['sunset']).strftime('%H:%M:%S')} UTC")

        # Display weather icon with description
        icon_code = weather_data['weather'][0]['icon']
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
        st.write(f"**Current Weather**: {weather_data['weather'][0]['description'].capitalize()}")
        st.image(icon_url, width=80)


# Function to display 5-day weather forecast in rows with icon in the last column
def display_forecast_data(forecast_data, col1):
    with col1:
        st.subheader(f"5-Day Forecast for {forecast_data['city']['name']}, {forecast_data['city']['country']}")

        # List to hold forecast data
        forecast_list = []

        for forecast in forecast_data['list'][:5]:  # Show only the first 5 forecasts for simplicity
            # Convert the date/time to MM/DD/YYYY format
            time_raw = forecast['dt_txt']
            time_parsed = datetime.strptime(time_raw, '%Y-%m-%d %H:%M:%S')
            time_formatted = time_parsed.strftime('%m/%d/%Y %H:%M')  # MM/DD/YYYY HH:MM format

            temp = forecast['main']['temp']
            weather_desc = forecast['weather'][0]['description'].capitalize()
            pressure = forecast['main']['pressure']
            humidity = forecast['main']['humidity']
            icon_code = forecast['weather'][0]['icon']
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"

            # Add data to forecast list
            forecast_list.append({
                "Date/Time": time_formatted,
                "Temperature (°F)": temp,
                "Description": weather_desc,
                "Pressure (hPa)": pressure,
                "Humidity (%)": humidity,
                "Icon": icon_url
            })

        # Convert list to DataFrame for display
        forecast_df = pd.DataFrame(forecast_list)

        # Display the forecast row by row
        for i, row in forecast_df.iterrows():
            col_date, col_temp, col_desc, col_press, col_hum, col_icon = st.columns([2, 2, 2, 2, 2, 1])
            with col_date:
                st.write(f"**{row['Date/Time']}**")
            with col_temp:
                st.write(f"**Temperature**: {row['Temperature (°F)']} °F")
            with col_desc:
                st.write(f"**Description**: {row['Description']}")
            with col_press:
                st.write(f"**Pressure**: {row['Pressure (hPa)']} hPa")
            with col_hum:
                st.write(f"**Humidity**: {row['Humidity (%)']}%")
            with col_icon:
                st.image(row['Icon'], width=60)
            st.write("---")  # Separator for each forecast


# Function to display air quality data in two columns: components in one column, definitions in another
def display_air_quality(air_quality_data, col2, col3):
    # Air quality tooltips (definitions for pollutants)
    air_quality_tooltip = {
        "CO": "Carbon Monoxide (CO): A colorless, odorless gas that can be harmful when inhaled in large amounts.",
        "NO": "Nitric Oxide (NO): A precursor to nitrogen dioxide, found in vehicle emissions.",
        "NO2": "Nitrogen Dioxide (NO2): Contributes to air pollution and respiratory problems.",
        "PM2.5": "Particulate Matter (PM2.5): Fine inhalable particles that can cause health issues.",
        "PM10": "Particulate Matter (PM10): Larger inhalable particles that can cause respiratory issues."
    }

    pollutants_to_display = ['co', 'no', 'no2', 'pm2_5', 'pm10']

    # Display air quality components in the first column
    with col2:
        st.subheader("Air Quality Components")
        aqi = air_quality_data['list'][0]['main']['aqi']
        st.write(f"**Air Quality Index (AQI)**: {aqi}")

        components = air_quality_data['list'][0]['components']

        for key, value in components.items():
            if key in pollutants_to_display:
                st.write(f"**{key.upper()}**: {value} µg/m³")

    # Display air quality definitions in the second column
    with col3:
        st.subheader("Air Quality Definitions")
        for pollutant, definition in air_quality_tooltip.items():
            st.write(f"**{pollutant}**: {definition}")



# App Overview Page
def app_overview():
    st.title("Welcome to the Weather and City Information Dashboard App :robot_face:")

    # Explain the app's purpose
    st.markdown("""
    ## Purpose of the App
    This Weather and City Information Dashboard provides detailed weather forecasts, city data, and air quality information. 
    It helps users gather real-time weather information, forecasts, and detailed data about any city they choose.

    This app is perfect for those who need:
    - Real-time weather updates
    - A detailed weather forecast with additional details such as pressure and humidity
    - Information about air quality and its components
    - Detailed city information like population, timezone, and elevation.

    ## APIs Used:
    - **OpenWeatherMap API**: Used for fetching real-time weather data, 5-day weather forecasts, and air quality information.
    - **GeoNames API**: Used to fetch detailed city information, including population, timezone, and elevation.
    - **Wikipedia API**: Used to retrieve a brief description of the city from Wikipedia.

    ## Libraries Used:
    - `Streamlit`: For building the interactive web application.
    - `Requests`: For handling API requests.
    - `Pandas`: For handling and displaying the weather forecast data.
    - `datetime`: For manipulating date and time data.

    ## How to Use the App
    1. **Overview**: This page gives you an introduction to the app and its purpose.
    2. **Weather Forecast**: Enter the city name, and the app will display the current weather conditions, a detailed 5-day forecast, air quality data, and general city information.
    3. **About the Author**: Learn more about the app developer and find links to their GitHub, LinkedIn, and Medium profiles.

    ## Features
    - **Real-time weather**: Get the current weather, temperature, wind speed, and more.
    - **Detailed forecast**: Detailed forecast, including temperature, humidity, pressure, and weather conditions with an icon.
    - **Air quality data**: See levels of air pollutants like CO, NO2, and PM2.5.
    - **City information**: Learn about the population, timezone, and elevation of the city.

    
    Let's get started! 🚀
    Dive into the next section by picking a sub-page from the navigation menu on the left and have a blast, just like Michael Scott and his Crew!
    """, unsafe_allow_html=True)



    # Embed the GIF using components.html
    components.html(
        """
        <iframe src="https://j.gifs.com/2R6PGM.gif" width="100%" height="600px" style="border:none;"></iframe>
        """,
        height=600
    )


# About the Author Page
def about_the_author():
    st.title("About the Author :male-student:")

    # Use icons as images
    st.markdown("""
    Hi, I'm Kornel Pudlo, a Data Engineer  with a passion for building impactful applications and sharing knowledge. 
    This app demonstrates how to integrate various APIs to deliver real-time weather, air quality, and city information.
    Feel free to connect and share your feedback with me! 😊

    You can find more about my work at the following links [click the icon]:

    - [![GitHub](https://img.icons8.com/ios-glyphs/30/000000/github.png)](https://github.com/KornelPudlo) GitHub
    - [![LinkedIn](https://img.icons8.com/ios-filled/30/000000/linkedin.png)](https://www.linkedin.com/in/kornel-pud%C5%82o-a19921b5) LinkedIn
    - [![Medium](https://img.icons8.com/ios-glyphs/30/000000/medium-monogram.png)](https://medium.com/@korn.pudlo) Medium
    """, unsafe_allow_html=True)


# Set up sidebar navigation
page = st.sidebar.radio("Select a page :point_down:", ["Overview :robot_face:", "Weather Forecast :sunny:", "About the Author :male-student: "])

# Call the respective page function based on user selection
if page == "Overview :robot_face:":
    app_overview()
elif page == "Weather Forecast :sunny:":
    city = st.text_input("Enter City Name", "")

    if city:
        col1, col2 = st.columns(2)
        city_details = get_city_details_geonames(city, GEONAMES_USERNAME)

        if city_details:
            with col1:
                st.subheader("City Details")
                st.write(f"**Name**: {city_details.get('name')}")
                st.write(f"**Country**: {city_details.get('country')}")
                st.write(f"**Population**: {city_details.get('population', 'N/A')}")
                st.write(f"**Timezone**: {city_details.get('timezone', 'N/A')}")
                st.write(f"**Elevation**: {city_details.get('elevation', 'N/A')} meters")

        city_description = get_city_description_wikipedia(city)
        with col2:
            st.subheader(f"Basic Information about {city}")
            st.write(f"**Description**: {city_description}")

        weather_data = get_weather_by_city(city)

        if weather_data.get("cod") != 200:
            st.error(f"Error: {weather_data.get('message', 'Unknown error')}")
        else:
            col3, col4 = st.columns(2)
            display_weather_data(weather_data, col3)

            with col4:
                lat = weather_data['coord']['lat']
                lon = weather_data['coord']['lon']
                st.map(pd.DataFrame([[lat, lon]], columns=['lat', 'lon']))

            st.divider()

            col5, col6 = st.columns(2)
            air_quality_data = get_air_quality(lat, lon)
            display_air_quality(air_quality_data, col5, col6)

            st.divider()

            col7 = st.columns(1)[0]
            forecast_data = get_weather_forecast(city)

            if forecast_data.get("cod") != "200":
                st.error(f"Error: {forecast_data.get('message', 'Unknown error')}")
            else:
                display_forecast_data(forecast_data, col7)
elif page == "About the Author :male-student: ":
    about_the_author()


# Add a light blue footer at the bottom of the page
footer_html = """
    <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #ADD8E6;
            color: black;
            text-align: center;
            padding: 10px;
            font-size: 14px;
            z-index: 1000;
            margin-left: 10%; /* Adjust this value to increase or decrease the space on the left */
        }
    </style>
    <div class="footer">
        <strong>Reminder: Don't forget to share your feedback with me! DM me directly on <a href="https://www.linkedin.com/in/kornel-pud%C5%82o-a19921b5" target="_blank">LinkedIn</a>.</strong>
    </div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
