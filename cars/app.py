from flask import Flask, render_template, request, redirect
import json
from pathlib import Path

app = Flask(__name__)
DATA_FILE = "cars.json"

def load_data():
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route('/')
def index():
    cars = load_data()
    return render_template("index.html", cars=cars)

@app.route('/add_car', methods=["POST"])
def add_car():
    data = load_data()
    license_plate = request.form["license_plate"]
    if any(car["license_plate"] == license_plate for car in data):
        return "רכב כבר קיים", 400
    new_car = {
        "license_plate": license_plate,
        "car_model": request.form["car_model"],
        "ownership": request.form["ownership"],
        "status": request.form["status"],
        "test_due_date": request.form["test_due_date"],
        "next_maintenance_date": request.form["next_maintenance_date"],
        "oil_change_date": request.form["oil_change_date"],
        "km": int(request.form["km"])
    }
    data.append(new_car)
    save_data(data)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
