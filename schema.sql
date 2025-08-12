DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS flights;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS payments;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    phone TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
);

CREATE TABLE flights (
    flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airline TEXT NOT NULL,
    flight_number TEXT NOT NULL,
    departure_airport TEXT NOT NULL,
    arrival_airport TEXT NOT NULL,
    departure_time TEXT NOT NULL,
    arrival_time TEXT NOT NULL,
    total_seats INTEGER NOT NULL,
    available_seats INTEGER NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    flight_id INTEGER NOT NULL,
    booking_date TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (flight_id) REFERENCES flights (flight_id)
);

CREATE TABLE payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_date TEXT NOT NULL,
    payment_status TEXT NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings (booking_id)
);
