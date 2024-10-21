# Weather Monitoring and Alert System

This project is a weather monitoring and alert system that fetches real-time weather data for multiple cities, stores it in an SQLite database, generates daily summaries, and sends email alerts when certain thresholds are exceeded.

## Features

- Fetches weather data from the OpenWeatherMap API.
- Stores weather data in an SQLite database.
- Generates daily weather summaries with average, max, min temperatures, and dominant weather conditions.
- Sends email alerts when a specified temperature threshold is exceeded for a set number of consecutive updates.
- Allows temperature conversion between Kelvin, Celsius, and Fahrenheit.
- Schedules weather data fetching at regular intervals using the schedule library.

## Technologies Used

- *Python*: Core language for the project.
- *SQLite*: Local database to store weather data and summaries.
- *OpenWeatherMap API*: For fetching real-time weather data.
- *SMTP*: For sending email alerts.
- *dotenv*: For loading configuration variables from the .env file.
- *Requests*: For handling API requests.
- *Schedule*: For scheduling recurring tasks.

## Prerequisites

- Python 3.x
- OpenWeatherMap API key
- Gmail account for sending alerts

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/shivateja20013/weather_monitoring_application.git
    cd weather_monitoring_application
    ```
    

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```
    

3. Create a .env file in the root directory with the following variables:
```bash
    
    API_KEY=your_openweathermap_api_key
    ALERT_THRESHOLD_TEMP=35.0  # Example: 35 degrees
    ALERT_THRESHOLD_CONSECUTIVE_UPDATES=3  # Number of updates to trigger alert
    TEMP_SCALE=Celsius  # Choose between 'Celsius' or 'Fahrenheit'
    FETCH_INTERVAL=10  # Interval in minutes to fetch data
    CITIES={"City1": {"lat": 12.9716, "lon": 77.5946}, "City2": {"lat": 40.7128, "lon": -74.0060}}  # List of cities
    EMAIL_ADDRESS=your_email@gmail.com
    EMAIL_PASSWORD=your_email_password
    ALERT_RECIPIENTS=recipient_email@example.com
    
```
## Usage

1. Run the weather monitoring script:

    ```bash
    python weather_monitoring.py
    ```
    

2. The system will begin fetching weather data at the specified interval, display current weather data, generate daily summaries, and send email alerts when necessary.

## Database Structure

1. **weather_data** table: Stores weather data for each city with temperature, feels-like temperature, weather condition, and timestamp.
2. **daily_summary** table: Stores daily summary for each city with average, max, min temperatures, and dominant weather condition.

## Project Structure


├── main.py  
├── requirements.txt       
├── .env                   
├── weather_data.db         
└── README.md
