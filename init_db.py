import sqlite3

connection = sqlite3.connect('database.db')

with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

# Add some sample data
cur.execute("INSERT INTO flights (airline, flight_number, departure_airport, arrival_airport, departure_time, arrival_time, total_seats, available_seats, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ('Airline A', 'AA101', 'JFK', 'LAX', '2024-07-01 06:00', '2024-07-01 09:00', 200, 200, 150))

connection.commit()
connection.close()
