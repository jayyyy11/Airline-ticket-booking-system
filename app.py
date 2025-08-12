from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def get_db_connection():
    conn = sqlite3.connect('database.db', timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        role = request.form['role']

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (name, email, password, phone, role) VALUES (?, ?, ?, ?, ?)',
                         (name, email, password, phone, role))
            conn.commit()
            flash('Signup successful. Please log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists.')
        finally:
            conn.close()
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', 
                            (email, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            session['name'] = user['name']
            session['email'] = user['email']

            flash('Logged in successfully.')

            if user['role'] == 'admin':
                return redirect(url_for('admin_index'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

@app.route('/admin_index')
def admin_index():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_index.html', username=session.get('name'))

@app.route('/user_dashboard')
def user_dashboard():
    if session.get('role') != 'user':
        return redirect(url_for('login'))
    return render_template('user_dashboard.html', username=session.get('name'))

@app.route('/add_flight', methods=['GET', 'POST'])
def add_flight():
    if session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        airline = request.form['airline']
        flight_number = request.form['flight_number']
        departure_airport = request.form['departure_airport']
        arrival_airport = request.form['arrival_airport']
        departure_time = request.form['departure_time']
        arrival_time = request.form['arrival_time']
        total_seats = int(request.form['total_seats'])
        price = float(request.form['price'])

        conn = get_db_connection()
        conn.execute("""INSERT INTO flights 
            (airline, flight_number, departure_airport, arrival_airport, 
             departure_time, arrival_time, total_seats, available_seats, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (airline, flight_number, departure_airport, arrival_airport,
             departure_time, arrival_time, total_seats, total_seats, price))
        conn.commit()
        conn.close()
        flash("Flight added successfully.")
        return redirect(url_for('all_flights'))

    return render_template('add_flight.html')

@app.route('/all_flights')
def all_flights():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    flights = conn.execute('SELECT * FROM flights').fetchall()
    conn.close()

    flights = [dict(flight) for flight in flights]

    for flight in flights:
        dt_str = flight['departure_time']
        at_str = flight['arrival_time']

        try:
            dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')

        try:
            at = datetime.strptime(at_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            at = datetime.strptime(at_str, '%Y-%m-%d %H:%M')

        flight['departure_time'] = dt.strftime('%d-%b %I:%M %p')
        flight['arrival_time'] = at.strftime('%d-%b %I:%M %p')

    return render_template('all_flights.html', flights=flights)

@app.route('/delete_flight/<int:flight_id>', methods=['POST'])
def delete_flight(flight_id):
    if session.get('role') != 'admin':
        flash("Access denied.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM flights WHERE flight_id = ?', (flight_id,))
    conn.commit()
    conn.close()

    flash("Flight deleted successfully.")
    return redirect(url_for('all_flights'))

@app.route('/book/<int:flight_id>', methods=['GET', 'POST'])
def book_flight(flight_id):
    if session.get('role') != 'user':
        flash("Only users can book flights.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        conn = get_db_connection()

        conn.execute('UPDATE flights SET available_seats = available_seats - 1 WHERE flight_id = ? AND available_seats > 0', (flight_id,))
        conn.execute('INSERT INTO bookings (user_id, flight_id, booking_date, status) VALUES (?, ?, CURRENT_TIMESTAMP, ?)',
                     (user_id, flight_id, 'Booked'))
        conn.commit()
        conn.close()
        return redirect(url_for('payment', flight_id=flight_id))

    return render_template('booking.html', flight_id=flight_id)

@app.route('/payment/<int:flight_id>', methods=['GET', 'POST'])
def payment(flight_id):
    if request.method == 'POST':
        amount = request.form['amount']
        conn = get_db_connection()
        booking = conn.execute('SELECT booking_id FROM bookings WHERE flight_id = ? AND user_id = ? ORDER BY booking_id DESC LIMIT 1',
                               (flight_id, session['user_id'])).fetchone()
        if booking:
            conn.execute('INSERT INTO payments (booking_id, amount, payment_date, payment_status) VALUES (?, ?, CURRENT_TIMESTAMP, ?)',
                         (booking['booking_id'], amount, 'Paid'))
            conn.commit()
        conn.close()
        return redirect(url_for('confirmation'))

    return render_template('payment.html')

@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')

@app.route('/flights', methods=['GET', 'POST'])
def flights():
    if 'role' not in session or session['role'] != 'user':
        return redirect(url_for('login'))

    flights = []  # Don't show anything by default

    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM flights WHERE departure_airport=? AND arrival_airport=?", (source, destination))
        flights = c.fetchall()
        conn.close()

    return render_template('flights.html', flights=flights)

@app.route('/init_db')
def init_db():
    conn = sqlite3.connect('database.db')
    with open('schema.sql') as f:
        conn.executescript(f.read())
    conn.close()
    return "✅ Database initialized!"

@app.route('/add_sample')
def add_sample():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO flights 
        (airline, flight_number, departure_airport, arrival_airport, departure_time, arrival_time, total_seats, available_seats, price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'IndiGo', '6E123', 'Bangalore', 'Mumbai', 
        '2025-08-10 08:00', '2025-08-10 10:30',
        180, 180, 4999.00
    ))
    conn.commit()
    conn.close()
    return "✅ Sample flight added!"

if __name__ == '__main__':
    app.run(debug=True)
