import mysql.connector
import re
import time
from datetime import datetime
from decimal import Decimal
import bcrypt

# Connect to MySQL database
db = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='Athira@001',
    database="root"
)
cursor = db.cursor()

# Utility function to generate a Booking ID
def generate_booking_id():
    prefix = "BK"
    suffix = str(time.time_ns())[-5:]
    return prefix + suffix

# 1. Display the Category-wise list of rooms and their Rate per day
def display_rooms_by_category():
    query = "SELECT c.name AS category, r.room_no, c.price_per_day, c.price_per_hour FROM rooms r JOIN category c ON r.category_id = c.id ORDER BY c.name;"
    cursor.execute(query)
    rooms = cursor.fetchall()
    for room in rooms:
        category, room_no, rate_per_day, rate_per_hour = room
        if rate_per_hour:
            print(f"Room No: {room_no}, Category: {category}, Rate per Day: {rate_per_day}, Rate per Hour: {rate_per_hour}")
        else:
            print(f"Room No: {room_no}, Category: {category}, Rate per Day: {rate_per_day}")

# 2. List all rooms occupied for the next two days
def list_occupied_rooms_next_two_days():
    query = """
    SELECT rooms.room_no, bookings.occupancy_date 
    FROM rooms 
    JOIN bookings ON rooms.id = bookings.room_id 
    WHERE bookings.occupancy_date BETWEEN CURDATE() AND CURDATE() + INTERVAL 2 DAY
    """
    cursor.execute(query)
    occupied_rooms = cursor.fetchall()
    for room_no, occupancy_date in occupied_rooms:
        print(f"Room No: {room_no}, Occupied on: {occupancy_date}")

# 3. Display the list of all rooms in their increasing order of rate per day
def display_rooms_by_rate():
    query="SELECT r.room_no,c.name AS category, c.price_per_day AS rate_per_day FROM rooms r JOIN category c ON r.category_id = c.id ORDER BY c.price_per_day ASC"
    cursor.execute(query)
    rooms = cursor.fetchall()
    for room_no, category, rate_per_day in rooms:
        print(f"Room No: {room_no}, Category: {category}, Rate per Day: {rate_per_day}")

# 4. Search Rooms based on BookingID and display the customer details
def search_room_by_booking_id(booking_id):
    query = """
    SELECT rooms.room_no, customers.first_name, customers.last_name, bookings.booking_date
    FROM bookings 
    JOIN rooms ON bookings.room_id = rooms.id 
    JOIN customers ON bookings.customer_id = customers.id 
    WHERE bookings.booking_id = %s
    """
    cursor.execute(query, (booking_id,))
    result = cursor.fetchone()
    if result:
        room_no, first_name, last_name, booking_date = result
        print(f"Booking ID: {booking_id}, Room No: {room_no}, Customer: {first_name} {last_name}, Booking Date: {booking_date}")
    else:
        print("No booking found with that ID.")

# 5. Display rooms which are not booked
def display_unbooked_rooms():
    query = """
    SELECT r.room_no, c.name AS category, c.price_per_day, c.price_per_hour
    FROM rooms r
    JOIN category c ON r.category_id = c.id
    WHERE r.status = 'unoccupied'
    """
    cursor.execute(query)
    unbooked_rooms = cursor.fetchall()
    for room_no, category, price_per_day, price_per_hour in unbooked_rooms:
        print(f"Room No: {room_no}, Category: {category}, Rate per day: {price_per_day}, Rate per hour: {price_per_hour if price_per_hour else 'N/A'}")

# 6. Update room when the customer leaves to Unoccupied
def update_room_to_unoccupied(room_no):
    query = "UPDATE rooms SET status = 'unoccupied' WHERE room_no = %s"
    cursor.execute(query, (room_no,))
    db.commit()
    print(f"Room {room_no} status updated to unoccupied.")

# 7. Store all records in file and display from file
def store_records_in_file():
    query = "SELECT * FROM bookings"
    cursor.execute(query)
    bookings = cursor.fetchall()
    with open('bookings.txt', 'w') as f:
        for booking in bookings:
            f.write(str(booking) + '\n')
    print("Records stored in bookings.txt")

def display_records_from_file():
    try:
        with open('bookings.txt', 'r') as f:
            records = f.readlines()
            for record in records:
                fields = record.strip().split(", ")
                print(f"Booking ID: {fields[0]}, Room ID: {fields[1]}, Customer ID: {fields[2]}, Booking Date: {fields[3]}, Occupancy Date: {fields[4]}, No. of Days: {fields[5]}, Advance Received: {fields[6]}, Total Amount: {fields[7]}")
    except Exception as e:
        print(f"Error reading file: {e}")

# 8. Register a new customer
def register_customer(first_name, last_name, email, phone, username, password):
    try:
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")

        # Validate phone number format
        if not re.match(r"^\d{10}$", phone):
            raise ValueError("Phone number should be 10 digits")

        # Validate username
        if not re.match(r"^[a-zA-Z0-9_]{5,20}$", username):
            raise ValueError("Username should be 5-20 characters long and contain only letters, numbers, or underscores")

        # Validate password
        if len(password) < 8:
            raise ValueError("Password should be at least 8 characters long")

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert new customer into the database
        query = """
        INSERT INTO customers (first_name, last_name, email, phone, username, password)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (first_name, last_name, email, phone, username, hashed_password))
        db.commit()
        print("Customer registered successfully!")
    except mysql.connector.IntegrityError as e:
        if 'username' in str(e):
            print("Error: Username already exists.")
        elif 'email' in str(e):
            print("Error: Customer with this email already exists.")
    except ValueError as e:
        print(f"Validation Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# 9. Pre-book a room
def pre_book_room(customer_id, room_no, occupancy_date, no_of_days, advance_received):
    try:
        query_room = """
        SELECT r.id, c.price_per_day, c.price_per_hour, c.name 
        FROM rooms r 
        JOIN category c ON r.category_id = c.id 
        WHERE r.room_no = %s
        """
        cursor.execute(query_room, (room_no,))
        room = cursor.fetchone()
        if not room:
            raise ValueError("Invalid room number")

        room_id, rate_per_day, rate_per_hour, category = room
        booking_id = generate_booking_id()

        additional_charges = Decimal('100.00')  # Fixed amount for tax, housekeeping, etc.
        tax_rate = Decimal('0.10')  # Example: 10% tax

        rate_per_day = Decimal(str(rate_per_day))

        if category in ('convention_hall', 'ballroom'):
            base_amount = rate_per_hour * Decimal(no_of_days) * Decimal('24.00')
        else:
            base_amount = rate_per_day * Decimal(no_of_days)

        total_amount = base_amount + additional_charges
        total_amount_with_tax = total_amount + (total_amount * tax_rate)

        query_booking = """
        INSERT INTO bookings (booking_id, customer_id, room_id, booking_date, occupancy_date, no_of_days, advance_received, total_amount)
        VALUES (%s, %s, %s, CURDATE(), %s, %s, %s, %s)
        """
        cursor.execute(query_booking,
                       (booking_id, customer_id, room_id, occupancy_date, no_of_days, advance_received, total_amount_with_tax))

        query_update_room = "UPDATE rooms SET status = 'occupied' WHERE id = %s"
        cursor.execute(query_update_room, (room_id,))
        db.commit()

        print(f"Room {room_no} pre-booked successfully with Booking ID: {booking_id}")
    except ValueError as e:
        print(f"Error: {e}")

# 10. Display Booking History for a Customer
def display_booking_history(customer_id):
    query = """
    SELECT bookings.booking_id, rooms.room_no, bookings.occupancy_date, bookings.no_of_days, bookings.total_amount
    FROM bookings 
    JOIN rooms ON bookings.room_id = rooms.id 
    WHERE bookings.customer_id = %s
    """
    cursor.execute(query, (customer_id,))
    bookings = cursor.fetchall()
    for booking_id, room_no, occupancy_date, no_of_days, total_amount in bookings:
        print(f"Booking ID: {booking_id}, Room No: {room_no}, Occupancy Date: {occupancy_date}, No. of Days: {no_of_days}, Total Amount: {total_amount}")

# 11. Admin - View Room Categories
def view_room_categories():
    query = "SELECT * FROM category"
    cursor.execute(query)
    categories = cursor.fetchall()
    for category in categories:
        print(category)

# 12. Admin - Add a Room Category
def add_room_category(name, price_per_day, price_per_hour):
    query = """
    INSERT INTO category (name, price_per_day, price_per_hour)
    VALUES (%s, %s, %s)
    """
    cursor.execute(query, (name, price_per_day, price_per_hour))
    db.commit()
    print("Room category added successfully.")

# 13. Admin - Remove a Room Category
def remove_room_category(category_id):
    query = "DELETE FROM category WHERE id = %s"
    cursor.execute(query, (category_id,))
    db.commit()
    print("Room category removed successfully.")

# 14. Admin - View and Manage Room Inventory
def add_room(room_no, category_id, status='unoccupied'):
    query = """
    INSERT INTO rooms (room_no, category_id, status)
    VALUES (%s, %s, %s)
    """
    cursor.execute(query, (room_no, category_id, status))
    db.commit()
    print("Room added successfully.")

def remove_room(room_no):
    query = "DELETE FROM rooms WHERE room_no = %s"
    cursor.execute(query, (room_no,))
    db.commit()
    print("Room removed successfully.")

# 15. Admin - View Customer List
def view_customers():
    query = "SELECT * FROM customers"
    cursor.execute(query)
    customers = cursor.fetchall()
    for customer in customers:
        print(customer)

# Menu for Admin
def admin_menu():
    while True:
        print("\nAdmin Menu:")
        print("1. View Category-wise Room List")
        print("2. List Occupied Rooms for Next Two Days")
        print("3. Display Rooms by Rate per Day")
        print("4. Search Room by Booking ID")
        print("5. Display Unbooked Rooms")
        print("6. Update Room Status to Unoccupied")
        print("7. Store Records in File")
        print("8. Display Records from File")
        print("9. Register Customer")
        print("10. Pre-book Room")
        print("11. Display Booking History")
        print("12. View Room Categories")
        print("13. Add Room Category")
        print("14. Remove Room Category")
        print("15. Add Room")
        print("16. Remove Room")
        print("17. View Customer List")
        print("18. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            display_rooms_by_category()
        elif choice == '2':
            list_occupied_rooms_next_two_days()
        elif choice == '3':
            display_rooms_by_rate()
        elif choice == '4':
            booking_id = input("Enter Booking ID: ")
            search_room_by_booking_id(booking_id)
        elif choice == '5':
            display_unbooked_rooms()
        elif choice == '6':
            room_no = input("Enter Room Number to Update Status: ")
            update_room_to_unoccupied(room_no)
        elif choice == '7':
            store_records_in_file()
        elif choice == '8':
            display_records_from_file()
        elif choice == '9':
            first_name = input("Enter First Name: ")
            last_name = input("Enter Last Name: ")
            email = input("Enter Email: ")
            phone = input("Enter Phone Number: ")
            username = input("Enter Username: ")
            password = input("Enter Password: ")
            register_customer(first_name, last_name, email, phone, username, password)
        elif choice == '10':
            customer_id = input("Enter Customer ID: ")
            room_no = input("Enter Room Number: ")
            occupancy_date = input("Enter Occupancy Date (YYYY-MM-DD): ")
            no_of_days = int(input("Enter Number of Days: "))
            advance_received = Decimal(input("Enter Advance Received: "))
            pre_book_room(customer_id, room_no, occupancy_date, no_of_days, advance_received)
        elif choice == '11':
            customer_id = input("Enter Customer ID: ")
            display_booking_history(customer_id)
        elif choice == '12':
            view_room_categories()
        elif choice == '13':
            name = input("Enter Room Category Name: ")
            price_per_day = Decimal(input("Enter Price Per Day: "))
            price_per_hour = Decimal(input("Enter Price Per Hour: "))
            add_room_category(name, price_per_day, price_per_hour)
        elif choice == '14':
            category_id = int(input("Enter Category ID to Remove: "))
            remove_room_category(category_id)
        elif choice == '15':
            room_no = input("Enter Room Number: ")
            category_id = int(input("Enter Category ID: "))
            add_room(room_no, category_id)
        elif choice == '16':
            room_no = input("Enter Room Number to Remove: ")
            remove_room(room_no)
        elif choice == '17':
            view_customers()
        elif choice == '18':
            break
        else:
            print("Invalid choice. Please try again.")

# Menu for Customers
def customer_menu():
    while True:
        print("\nCustomer Menu:")
        print("1. Register")
        print("2. Pre-book Room")
        print("3. View Booking History")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            first_name = input("Enter First Name: ")
            last_name = input("Enter Last Name: ")
            email = input("Enter Email: ")
            phone = input("Enter Phone Number: ")
            username = input("Enter Username: ")
            password = input("Enter Password: ")
            register_customer(first_name, last_name, email, phone, username, password)
        elif choice == '2':
            customer_id = input("Enter Customer ID: ")
            room_no = input("Enter Room Number: ")
            occupancy_date = input("Enter Occupancy Date (YYYY-MM-DD): ")
            no_of_days = int(input("Enter Number of Days: "))
            advance_received = Decimal(input("Enter Advance Received: "))
            pre_book_room(customer_id, room_no, occupancy_date, no_of_days, advance_received)
        elif choice == '3':
            customer_id = input("Enter Customer ID: ")
            display_booking_history(customer_id)
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")

# Main Menu
def main_menu():
    while True:
        print("\nMain Menu:")
        print("1. Admin Login")
        print("2. Customer Login")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            # Admin Login
            admin_menu()
        elif choice == '2':
            # Customer Login
            customer_menu()
        elif choice == '3':
            db.close()
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()
