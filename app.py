from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
def init_sqlite_db():
    conn = sqlite3.connect('database.db')
    print("Opened database successfully")

    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT, total_score INTEGER DEFAULT 0)')
    print("Table created successfully")
    conn.close()

init_sqlite_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'admin123':
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        con = sqlite3.connect('database.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        
        if user and check_password_hash(user['password'], password):
            flash('User login successful!', 'success')
            return redirect(url_for('user_dashboard', username=username))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = generate_password_hash(request.form['password'])

            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO users (username, email, password, total_score) VALUES (?, ?, ?, 0)", (username, email, password))
                con.commit()
                flash('Record successfully added', 'success')
                return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error in insert operation: {e}', 'danger')
    return render_template('signup.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admin')
def admin_dashboard():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT username, total_score FROM users")
    users = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', users=users)

@app.route('/user_dashboard')
def user_dashboard():
    username = request.args.get('username')
    return render_template('user_dashboard.html', username=username)

@app.route('/score', methods=['GET', 'POST'])
def score():
    username = request.args.get('username')
    if request.method == 'POST':
        try:
            subject_scores = [int(request.form[f'subject{i}']) for i in range(1, 6)]
            activity_scores = [int(request.form[f'activity{i}']) for i in range(1, 4)]
            research_scores = [int(request.form[f'research{i}']) for i in range(1, 20)]

            total_points = sum(subject_scores) + sum(activity_scores) + sum(research_scores)

            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = cur.fetchone()
                if user:
                    cur.execute("UPDATE users SET total_score = ? WHERE username = ?", (total_points, username))
                    con.commit()
                    flash(f'Your calculated score is: {total_points}', 'success')
                    return redirect(url_for('view_score', username=username))
                else:
                    flash('User not found', 'danger')
        except Exception as e:
            flash(f'Error in calculating score: {e}', 'danger')
    return render_template('score.html', username=username)

@app.route('/view_score')
def view_score():
    username = request.args.get('username')
    con = sqlite3.connect('database.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT total_score FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    if user:
        score = user['total_score']
        increment_message = ""
        promotion_message = None

        if 100 <= score <= 250:
            increment_message = "You are eligible for a 10% salary increment."
        elif 251 <= score <= 500:
            increment_message = "You are eligible for a 20% salary increment."
        elif score > 501:
            increment_message = "You are eligible for a 20% salary increment."
            promotion_message = "Congratulations! You are also eligible for a promotion."

        return render_template('view_score.html', score=score, increment_message=increment_message, promotion_message=promotion_message)
    else:
        flash('User not found', 'danger')
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
