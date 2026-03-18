# HealthSync

HealthSync is a lightweight health tracking web application built with Flask.

## Features

- User authentication (login/register)
- Blood glucose logging
- Medication reminders
- CSV data export
- REST API for glucose data
- Dashboard with Chart.js visualization

## Tech Stack

Backend:
- Flask
- SQLite
- SQLAlchemy

Frontend:
- HTML
- CSS
- Chart.js

## Project Structure

routes/
    auth.py
    dashboard.py
    glucose.py
    reminders.py
    settings.py

templates/
static/

app.py
db.py
utils.py
requirements.txt

## Run Locally

Install dependencies:

pip install -r requirements.txt

Run the application:

python app.py
