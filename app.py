from flask import Flask, render_template, request, redirect, url_for, flash, session, g, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
from database import get_db, init_app
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
init_app(app)



# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required.'
        elif db.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = f'User {username} is already registered.'
        elif db.execute(
            'SELECT id FROM users WHERE email = ?', (email,)
        ).fetchone() is not None:
            error = f'Email {email} is already registered.'

        if error is None:
            db.execute(
                'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), email)
            )
            db.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))

        flash(error)

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        error = None
        
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))

        flash(error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    
    return render_template('dashboard.html', user=user)

@app.route('/add_balance', methods=['POST'])
@login_required
def add_balance():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        
        db = get_db()
        error = None
        
        if amount <= 0:
            error = 'Amount must be positive.'
        
        if error is None:
            # Get current user's username
            current_username = session['username']
            
            # Add amount to user's balance
            db.execute(
                'UPDATE users SET balance = balance + ? WHERE id = ?',
                (amount, session['user_id'])
            )
            
            # Record transaction as a deposit - user is both sender and receiver
            db.execute(
                '''INSERT INTO transactions 
                (sender_id, receiver_id, sender_name, receiver_name, amount, description, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (session['user_id'], session['user_id'], 
                 current_username, current_username, 
                 amount, 'Account deposit', 'completed')
            )
            
            db.commit()
            flash(f'${amount:.2f} successfully added to your balance!')
            return redirect(url_for('dashboard'))
            
        flash(error)
        return redirect(url_for('dashboard'))

@app.route('/check_balance')
@login_required
def check_balance():
    db = get_db()
    user = db.execute(
        'SELECT balance FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    
    return jsonify({
        'balance': user['balance'],
        'formatted_balance': f"${user['balance']:.2f}"
    })

@app.route('/send_money', methods=['POST'])
@login_required
def send_money():
    if request.method == 'POST':
        receiver_username = request.form['receiver']
        amount = float(request.form['amount'])
        description = request.form.get('description', '')  # Use get() with default value
        
        db = get_db()
        error = None
        
        # Check if receiver exists
        receiver = db.execute(
            'SELECT * FROM users WHERE username = ?', (receiver_username,)
        ).fetchone()
        
        if receiver is None:
            error = f'User {receiver_username} does not exist.'
        elif receiver['id'] == session['user_id']:
            error = 'You cannot send money to yourself.'
        elif amount <= 0:
            error = 'Amount must be positive.'
        
        # Check if sender has enough balance
        sender = db.execute(
            'SELECT * FROM users WHERE id = ?', (session['user_id'],)
        ).fetchone()
        
        if sender['balance'] < amount:
            error = 'Insufficient balance.'
            
        if error is None:
            # Get sender username
            sender_username = session['username']
            
            # Update balances
            db.execute(
                'UPDATE users SET balance = balance - ? WHERE id = ?',
                (amount, session['user_id'])
            )
            db.execute(
                'UPDATE users SET balance = balance + ? WHERE id = ?',
                (amount, receiver['id'])
            )
            
            # Record transaction with sender and receiver names
            db.execute(
                '''INSERT INTO transactions 
                (sender_id, receiver_id, sender_name, receiver_name, amount, description, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (session['user_id'], receiver['id'], 
                 sender_username, receiver_username, 
                 amount, description, 'completed')
            )
            
            db.commit()
            flash('Payment sent successfully!')
            return redirect(url_for('dashboard'))
            
        flash(error)
        return redirect(url_for('dashboard'))

@app.route('/transactions')
@login_required
def transactions():
    db = get_db()
    
    # Get all transactions where user is sender or receiver
    # Using the updated schema with sender_name and receiver_name
    transactions = db.execute(
        '''
        SELECT * FROM transactions
        WHERE sender_id = ? OR receiver_id = ?
        ORDER BY created_at DESC
        ''',
        (session['user_id'], session['user_id'])
    ).fetchall()
    
    return render_template('transactions.html', transactions=transactions)

@app.route('/api/user_balance')
@login_required
def user_balance():
    db = get_db()
    user = db.execute(
        'SELECT balance FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    
    return jsonify({'balance': user['balance']})

if __name__ == '__main__':
    app.run(debug=True)