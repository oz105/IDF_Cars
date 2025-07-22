from flask import Flask, render_template, request, redirect
import json
from pathlib import Path

app = Flask(__name__)
DATA_FILE = 'cars.json'

def load_data():
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route('/')
def index():
    cars = load_data()
    return render_template('index.html', cars=cars)

@app.route('/add', methods=['POST'])
def add_car():
    data = load_data()
    try:
        new_car = {
            "license_plate": request.form['license_plate'],
            "car_model": request.form['car_model'],
            "ownership": request.form.get('ownership', 'לא ידוע'),
            "status": request.form.get('status', 'לא ידוע'),
            "year": request.form.get('year'),
            "last_service_km": request.form.get('last_service_km'),
            "next_service_km": request.form.get('next_service_km'),
            "test_due_date": request.form.get('test_due_date'),
            "next_maintenance_date": request.form.get('next_maintenance_date'),
            "oil_change_date": request.form.get('oil_change_date'),
            "km": int(request.form['km']),
        }
    except Exception as e:
        return f"שגיאה בקלט: {e}", 400

    for car in data:
        if car['license_plate'] == new_car['license_plate']:
            return "רכב עם מספר זה כבר קיים במערכת", 400

    data.append(new_car)
    save_data(data)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
