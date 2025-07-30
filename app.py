from flask import Flask, render_template, request, redirect
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Database Connection Function
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="minto750",  # Change this to your actual MySQL password
            database="gym",
            auth_plugin="mysql_native_password"
        )
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None  # Handle failure gracefully
    

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/active_members")
def active_members():
    db = get_db_connection()
    if db is None:
        return "Database connection failed", 500

    cursor = db.cursor()
    cursor.execute("""
        SELECT m.member_id, m.name, COALESCE(COUNT(a.session_id), 0) AS session_count
        FROM Members m
        LEFT JOIN Attendance a ON m.member_id = a.member_id
        WHERE m.status = 'Active'
        GROUP BY m.member_id, m.name
        ORDER BY session_count DESC
    """)
    active_members = cursor.fetchall()

    cursor.execute("""
        SELECT m.member_id, m.name, COALESCE(COUNT(a.session_id), 0) AS session_count, m.expiry_date
        FROM Members m
        LEFT JOIN Attendance a ON m.member_id = a.member_id
        WHERE m.status = 'Active'
        GROUP BY m.member_id, m.name, m.expiry_date
        ORDER BY session_count DESC
        LIMIT 1
    """)
    most_active_member = cursor.fetchone()

    cursor.close()
    db.close()
    return render_template("active_members.html", members=active_members, most_active_member=most_active_member)

@app.route("/expiring-members")
def expiring_members():
    db = get_db_connection()
    if db is None:
        return "Database connection failed", 500

    cursor = db.cursor()
    current_month = datetime.now().strftime("%Y-%m")
    cursor.execute("SELECT * FROM Members WHERE expiry_date LIKE %s", (current_month + "%",))
    expiring_members = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template("expiring_members.html", members=expiring_members)

@app.route("/trainer-member-count")
def trainer_member_count():
    db = get_db_connection()
    if db is None:
        return "Database connection failed", 500

    cursor = db.cursor()
    cursor.execute("""
        SELECT m.trainer_id, t.name, COUNT(*) AS member_count
        FROM Members m
        JOIN Trainers t ON m.trainer_id = t.trainer_id
        GROUP BY m.trainer_id, t.name
    """)

    trainer_counts = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template("trainer_member_count.html", trainer_counts=trainer_counts)

@app.route("/all-members")
def all_members():
    db = get_db_connection()
    if db is None:
        return "Database connection failed", 500

    cursor = db.cursor()
    cursor.execute("SELECT * FROM Members")
    all_members = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template("all_members.html", members=all_members)

@app.route("/add-member", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        db = get_db_connection()
        if db is None:
            return "Database connection failed", 500

        cursor = db.cursor()
        name = request.form["name"]
        status = request.form["status"]
        expiry_date = request.form["expiry_date"]
        trainer_id = request.form["trainer_id"]

        cursor.execute("SELECT MAX(member_id) FROM Members")
        last_id = cursor.fetchone()[0]

        new_member_id = 1 if last_id is None else last_id + 1

        query = "INSERT INTO Members (member_id, name, status, expiry_date, trainer_id) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (new_member_id, name, status, expiry_date, trainer_id))
        db.commit()

        cursor.close()
        db.close()

    return render_template("add_member.html")


if __name__ == "__main__":
    app.run(debug=True)
