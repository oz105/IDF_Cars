from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
from datetime import datetime, timedelta
from pathlib import Path
from twilio.rest import Client


# 8fa8dc62e3385133ec364a8dc5d165ae

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # שנה למשהו בטוח

DATA_FILE = 'cars.json'
USERS_FILE = 'users.json'


def send_sms(to, body):
    # הפרטים שלך מטוויליו
    account_sid = ''
    auth_token = ''
    from_number = '+18563725713'

    print("We sending SMS")

    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=body,
        from_=from_number,
        to=to
    )
    return message.sid


def notify_upcoming_appointments():
    data = load_data()
    today = datetime.today().date()
    target_date = today + timedelta(days=3)

    for car in data:
        phone = car.get('phone')
        if not phone:
            continue

        messages = []
        try:
            maint_date = datetime.strptime(car['next_maintenance_date'], "%Y-%m-%d").date()
            if maint_date == target_date:
                license_plate = car.get('license_plate')
                next_maintenance_date = car.get('next_maintenance_date')
                messages.append(f"תזכורת: טיפול רגיל לרכב מספר {license_plate} מתקרב. תאריך הטיפול: {next_maintenance_date} ")
        except:
            pass

        try:
            oil_date = datetime.strptime(car['oil_change_date'], "%Y-%m-%d").date()
            if oil_date == target_date:
                license_plate = car.get('license_plate')
                messages.append(f" תזכורת: החלפת שמנים לרכב מספר  {license_plate}  מתקרבת בעוד 3 ימים. ")
        except:
            pass

        for msg in messages:
            send_sms(phone, msg)


def load_data():
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_users():
    if Path(USERS_FILE).exists():
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def check_login(username, password):
    users = load_users()
    return any(user['username'] == username and user['password'] == password for user in users)


# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         users = load_users()
#         username = request.form['username']
#         password = request.form['password']
#         if username in users and users[username] == password:
#             session['username'] = username
#             return redirect(url_for('index'))
#         else:
#             return render_template('login.html', error='שם משתמש או סיסמה לא נכונים')
#     return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_login(username, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash("שם משתמש או סיסמה שגויים")
            return redirect(url_for('login'))
    return render_template('login.html')

# @app.route('/')
# def index():
#     if 'username' not in session:
#         return redirect(url_for('login'))
#     with open(DATA_FILE, 'r', encoding='utf-8') as f:
#         car = json.load(f)
#     return render_template('index.html', car=car, username=session['username'])


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


def login_required(func):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


@app.route('/')
@login_required
def index():
    cars = load_data()
    today = datetime.today().date()

    def closest_cars_by_field(field, n=3):
        filtered = []
        for car in cars:
            try:
                date_val = datetime.strptime(car[field], "%Y-%m-%d").date()
                if date_val >= today:
                    filtered.append((car, date_val))
            except:
                continue
        filtered.sort(key=lambda x: x[1])
        return [car for car, _ in filtered[:n]]

    closest_maintenance = closest_cars_by_field("next_maintenance_date")
    closest_oil = closest_cars_by_field("oil_change_date")
    closest_test = closest_cars_by_field("test_due_date")

    return render_template(
        'index.html',
        cars=cars,
        closest_maintenance=closest_maintenance,
        closest_oil=closest_oil,
        closest_test=closest_test
    )


@app.route('/add', methods=['POST'])
@login_required
def add_car():
    new_car = {
        "license_plate": request.form['license_plate'],
        "car_model": request.form['car_model'],
        "ownership": request.form['ownership'],
        "status": request.form['status'],
        "test_due_date": request.form['test_due_date'],
        "next_maintenance_date": request.form['next_maintenance_date'],
        "oil_change_date": request.form['oil_change_date'],
        "km": int(request.form['km'])
    }
    data = load_data()
    for car in data:
        if car['license_plate'] == new_car['license_plate']:
            return "רכב עם מספר זה כבר קיים"
    data.append(new_car)
    save_data(data)
    return redirect(url_for('index'))


@app.route('/update_km', methods=['GET', 'POST'])
@login_required
def update_km():
    data = load_data()
    if request.method == 'POST':
        plate = request.form['license_plate']
        new_km = request.form['km']
        try:
            new_km_int = int(new_km)
        except:
            return 'ק"מ לא תקין'
        for car in data:
            if car['license_plate'] == plate:
                car['km'] = new_km_int
                save_data(data)
                return redirect(url_for('index'))
        return "רכב לא נמצא"
    return render_template('update_km.html', cars=data)

@app.route('/maintenance/<license_plate>')
def maintenance_details(license_plate):
    with open('cars.json', 'r', encoding='utf-8') as f:
        cars = json.load(f)
    car = next((c for c in cars if c['license_plate'] == license_plate), None)
    if not car:
        flash("רכב לא נמצא")
        return redirect(url_for('index'))
    return render_template('maintenance_details.html', car=car)


@app.route('/update_test', methods=['GET', 'POST'])
@login_required
def update_test():
    data = load_data()
    if request.method == 'POST':
        plate = request.form['license_plate']
        new_date = request.form['test_due_date']
        for car in data:
            if car['license_plate'] == plate:
                car['test_due_date'] = new_date
                save_data(data)
                return redirect(url_for('index'))
        return "רכב לא נמצא"
    return render_template('update_test.html', cars=data)

@app.route('/delete/<license_plate>', methods=['POST'])
def delete_car(license_plate):
    data = load_data()
    data = [car for car in data if car['license_plate'] != license_plate]
    save_data(data)
    flash(f"הרכב {license_plate} נמחק בהצלחה!", 'success')
    return redirect(url_for('index'))


@app.route('/update_maintenance', methods=['GET', 'POST'])
@login_required
def update_maintenance():
    data = load_data()
    if request.method == 'POST':
        plate = request.form['license_plate']
        new_maintenance = request.form['next_maintenance_date']
        new_oil = request.form['oil_change_date']
        for car in data:
            if car['license_plate'] == plate:
                car['next_maintenance_date'] = new_maintenance
                if new_oil:
                    car['oil_change_date'] = new_oil
                save_data(data)
                return redirect(url_for('index'))
        return "רכב לא נמצא"
    return render_template('update_maintenance.html', cars=data)

@app.route("/send_km_request/<license_plate>")
def send_km_request(license_plate):
    with open("cars.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for car in data:
        if car["license_plate"] == license_plate:
            phone = car.get("phone")
            if not phone:
                flash("לא נמצא מספר טלפון לרכב זה", "danger")
                print("לא נמצא מספר טלפון לרכב זה", "danger")
                return redirect(url_for("index"))

            message = f"שלום, אנא שלח את הקילומטראז' הנוכחי לרכב {license_plate} כמספר בלבד (למשל: 84520). תודה!"
            send_sms(phone, message)
            flash("הודעת SMS נשלחה לבעל הרכב", "success")
            print("הודעת SMS נשלחה לבעל הרכב", "success")
            return redirect(url_for('index', success=1))

    flash("הרכב לא נמצא", "danger")
    return redirect(url_for("index"))


@app.route("/send_reminder/<license_plate>")
def send_reminder(license_plate):
    reminder_type = request.args.get("type")

    with open("cars.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for car in data:
        if car["license_plate"] == license_plate:
            phone = car.get("phone")
            if not phone:
                flash("לא נמצא מספר טלפון לרכב זה", "danger")
                return redirect(url_for("index"))

            if reminder_type == "maintenance":
                message = f"שלום, תזכורת לטיפול תקופתי לרכב {license_plate}. אנא קבע מועד בהקדם."
            elif reminder_type == "oil":
                message = f"שלום, תזכורת להחלפת שמנים לרכב {license_plate}."
            elif reminder_type == "test":
                message = f"שלום, תזכורת לחידוש טסט לרכב {license_plate}."
            else:
                flash("סוג תזכורת לא חוקי", "danger")
                return redirect(url_for("index"))

            # send_sms(phone, message)
            flash(f"התזכורת נשלחה לבעל הרכב {license_plate}", "success")
            return redirect(url_for("index"))

    flash("הרכב לא נמצא", "danger")
    return redirect(url_for("index"))

@app.route("/update_maintenance_details/<license_plate>", methods=["POST"])
def update_maintenance_details(license_plate):
    new_details = request.form.get("new_details")

    with open("cars.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for car in data:
        if car["license_plate"] == license_plate:
            current_details = car.get("last_maintenance_details", "")
            # הוספה למידע קיים או כתיבה מחדש
            car["last_maintenance_details"] = new_details.strip()
            break

    with open("cars.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    flash("המלל עודכן בהצלחה", "success")
    return redirect(url_for("maintenance_details", license_plate=license_plate))


if __name__ == '__main__':
    print("We run")
    notify_upcoming_appointments()  # שלח תזכורות לפני שמרימים את השרת
    app.run(host="0.0.0.0", port=5000, debug=True)
    print()
    # app.run(debug=True)



