import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///resavr.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

firebase_creds = os.getenv("FIREBASE_CREDS")
if firebase_creds:
    cred = credentials.Certificate(json.loads(firebase_creds))
    initialize_app(cred)
else:
    raise ValueError("FIREBASE_CREDS environment variable not set")

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Load environment variables from .env file
load_dotenv()

# Initialize Firebase
json_path = os.path.join(os.path.dirname(__file__), 'firebase-adminsdk.json')
try:
    cred = credentials.Certificate(json_path)
    initialize_app(cred)
    print("Firebase credentials initialized successfully.")
except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Make sure the 'firebase-adminsdk.json' file is in the same directory as 'app.py'.")

# OAuth configuration
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_redirect_uri=os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/google_callback'),
    client_kwargs={'scope': 'openid profile email'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
)

# Define User and Business models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    food_surplus = db.relationship('FoodSurplus', backref='business', lazy=True)

class FoodSurplus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_type = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.String(80), nullable=False)
    expiration_date = db.Column(db.String(80), nullable=False)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)

# Create database tables
def create_database():
    with app.app_context():
        db.create_all()

# Routes
@app.route('/')
def home():
    username = session.get('username')
    form_submitted = session.get('form_submitted', False)
    return render_template('home.html', username=username)

@app.route('/google_login', methods=['POST'])
def google_login():
    token = request.json.get('idToken')
    email = request.json.get('email')
    displayName = request.json.get('displayName')

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, username=displayName, password=generate_password_hash(os.urandom(24).hex(), method='pbkdf2:sha256', salt_length=8))
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id
    session['username'] = user.username
    session.permanent = True
    flash('Login successful!', 'success')
    return jsonify(success=True, redirect_url=url_for('home'))  # Updated to 'home'

@app.route('/google_callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = google.parse_id_token(token)
    email = user_info['email']
    username = user_info['name']

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, username=username, password=generate_password_hash(os.urandom(24).hex(), method='pbkdf2:sha256', salt_length=8))
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id
    session['username'] = user.username
    session.permanent = True
    flash('Login successful!', 'success')
    return redirect(url_for('home'))  # Updated to 'home'

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('form_submitted', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/page')
def page():
    return render_template('page.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/discover')
def discover():
    surplus_food = FoodSurplus.query.all()  # Display all available food surplus
    return render_template('discover.html', surplus_food=surplus_food)

@app.route('/reserve', methods=['POST'])
def reserve():
    reservation = {
        'food_type': request.form['food_type'],
        'quantity': request.form['quantity'],
        'expiration_date': request.form['expiration_date'],
    }

    if 'reservations' not in session:
        session['reservations'] = []

    session['reservations'].append(reservation)
    return jsonify(success=True)

@app.route('/profile')
def profile():
    user = User.query.filter_by(id=session.get('user_id')).first()
    business = Business.query.filter_by(id=user.id).first()  # Assuming user is a business owner
    surplus_food = FoodSurplus.query.filter_by(business_id=business.id).all()  # Display food surplus for business owner
    return render_template('profile.html', surplus_food=surplus_food)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        
        new_user = User(email=email, username=username, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now login.', 'success')
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            session.permanent = True
            return redirect(url_for('new_hp'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
            return redirect(url_for('register'))

    return render_template('reg.html')

@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        new_business = Business(name=name, email=email, password=hashed_password)
        db.session.add(new_business)
        db.session.commit()
        flash('Business registration successful!', 'success')
        return redirect(url_for('home'))

    return render_template('join.html')

@app.route('/community')
def community():
    return render_template('community.html')  # Ensure a 'community.html' file exists

@app.route('/Dashboard')
def Dashboard():
    return render_template('Dashboard.html')

@app.route('/thank_you')
def thank_you():
    return "Thank you for contacting us! We will get back to you shortly."

@app.route('/faq')
def faq():
    return render_template('faq_terms_privacy.html')

@app.route('/plans')
def plans():
    return render_template('plans.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # handle form submission (store, email, etc.)
        flash("Message sent successfully!", "success")
    return render_template('contact.html')

if __name__ == '__main__':
    create_database()
    app.run(debug=True)
