from flask import Flask, render_template, url_for, request, redirect, flash, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import RPi.GPIO as GPIO
import sys
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///e-pera.db'
app.config['SECRET_KEY'] = 'g1mo9je(e9jo0uv+(8(^1fl31dd%$5rldf04zm$^20am)z=c(h'
app.config['UPLOAD_FOLDER'] = './uploads/'
db = SQLAlchemy(app)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Admin(db.Model, UserMixin):

    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

    fullname = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Admin {self.username}>'

class Beneficiary(db.Model):

    __tablename__ = 'beneficiary'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    gcash_number = db.Column(db.String(15), nullable=False)
    assistance_type = db.Column(db.String(50), nullable=False)
    image_attachment = db.Column(db.String(100))
    assistance_confirmed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Beneficiary {self.first_name} {self.last_name}>'

class Confirmation(db.Model):

    __tablename__ = 'confirmation'

    id = db.Column(db.Integer, primary_key=True)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey('beneficiary.id'))
    confirmation_date = db.Column(db.DateTime, default=datetime.now)
    confirmed_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')

    def __repr__(self):
        return f'<Confirmation {self.beneficiary_id} {self.date_confirmed}>'

class Money(db.Model):

    __tablename__ = 'money'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Money {self.amount} {self.date_added}>'
    
login_manager = LoginManager()
login_manager.login_view = 'login.html'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

@app.cli.command("init-db")
def init_db():
    db.create_all()
    # Check if admin account exists, if not create one
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', password=generate_password_hash('admin'), fullname='Administrator')
        db.session.add(admin)
        db.session.commit()

@app.cli.command("drop-db")
def drop_db():
    db.drop_all()
        
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = Admin.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))

        login_user(user)

        return redirect(url_for('dashboard'))

    return render_template('login.html')  # Render the login template

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():

    return render_template("dashboard.html", fullname=current_user.fullname)

@app.route('/addbeneficiary')
@login_required
def addbeneficiary():

    return render_template("addbeneficiary.html")

@app.route('/addbeneficiary', methods=["POST"])
@login_required
def addbeneficiary_post():
    first_name = request.form.get('first_name')
    middle_name = request.form.get('middle_name')
    last_name = request.form.get('last_name')
    contact_number = request.form.get('contact_number')
    gcash_number = request.form.get('gcash_number')
    assistance_type = request.form.get('assistance_type')
    
    # Check if the post request has the file part
    if 'image_attachment' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['image_attachment']

    # If the user does not select a file, the browser submits an empty file without a filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Save the file to the uploads folder
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Save the filename in the database
        new_beneficiary = Beneficiary(first_name=first_name, middle_name=middle_name, last_name=last_name, contact_number=contact_number, gcash_number=gcash_number, assistance_type=assistance_type, image_attachment=filename)
        db.session.add(new_beneficiary)
        db.session.commit()
        return redirect(url_for('dashboard'))
    else:
        flash('File type not allowed')
        return redirect(request.url)
    
@app.route('/beneficiaries')
@login_required
def beneficiaries():
    beneficiaries = Beneficiary.query.filter_by(assistance_confirmed=False).order_by(Beneficiary.last_name).all()

    return render_template("beneficiaries.html", beneficiaries=beneficiaries)

@app.route('/delete/<name>')
@login_required
def delete(name):
    delete = Beneficiary.query.get_or_404(name)

    db.session.delete(delete)
    db.session.commit()
    return redirect(url_for('beneficiaries'))

@app.route('/uploads/<filename>')
def view_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/assistance')
def assistance():
    return render_template("assistance.html")

@app.route('/get_names', methods=['POST'])
def get_names():
    assistance_type = request.form.get('assistance_type')
    # Query the database to get names based on assistance type
    beneficiaries = Beneficiary.query.filter_by(assistance_type=assistance_type, assistance_confirmed=False).all()
    # Create a list of dictionaries containing names and IDs
    names = [{'id': beneficiary.id, 'full_name': f"{beneficiary.first_name} {beneficiary.last_name}"} for beneficiary in beneficiaries]
    # Return the names as JSON
    return jsonify({'names': names})

@app.route('/confirm_assistance')
@login_required
def confirm_assistance():
    confirmation_list = Confirmation.query.all()

    beneficiary_info = []
    for confirmation in confirmation_list:
        beneficiary = Beneficiary.query.get(confirmation.beneficiary_id)
        if beneficiary:
            beneficiary_info.append({
                'confirmation_id': confirmation.id,
                'beneficiary_name': f"{beneficiary.first_name} {beneficiary.last_name}",
                'assistance_type': beneficiary.assistance_type,
                'contact_number': beneficiary.contact_number,
                'gcash_number': beneficiary.gcash_number,
                'image_attachment': beneficiary.image_attachment
            })
    return render_template('confirm_assistance.html', beneficiary_info=beneficiary_info)

@app.route('/confirm/<int:confirmation_id>')
@login_required
def confirm(confirmation_id):
    confirmation = Confirmation.query.get_or_404(confirmation_id)
    beneficiary = Beneficiary.query.get_or_404(confirmation.beneficiary_id)
    beneficiary.assistance_confirmed = True
    db.session.delete(confirmation)
    db.session.commit()
    flash('Assistance confirmed for {}'.format(beneficiary.first_name))
    return redirect(url_for('confirm_assistance'))

@app.route('/add_to_confirmation', methods=['POST'])
def add_to_confirmation():
    assistance_type = request.form.get('assistance_type')
    beneficiary_id = request.form.get('beneficiary_id')

    existing_confirmation = Confirmation.query.filter_by(beneficiary_id=beneficiary_id).first()

    if existing_confirmation:
        return jsonify({'success': False, 'message': 'Beneficiary already in confirmation list.'}), 400
    
    try:
        # Create a new confirmation record
        confirmation = Confirmation(beneficiary_id=beneficiary_id)
        db.session.add(confirmation)
        db.session.commit()
        return jsonify({'success': True})
    except IntegrityError:
        # Handle case where beneficiary is already in the confirmation list
        return jsonify({'success': False, 'message': 'Beneficiary already in confirmation list.'}), 400
    except Exception as e:
        # Handle other exceptions
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Insert Coin Page

pinNumberingType = GPIO.BCM
bouncetime = 36
readingtype = 1
pinNum = 2  # Assuming this is the GPIO pin connected to the coin acceptor
pulseVal = 0  # Assuming the pulse value for the coin acceptor is 0

interval = 0.01 if readingtype == 2 else 1
non_pulse_val = 1 if pulseVal == 0 else 0
prev = non_pulse_val
total_amount = 0  # Variable to store the total amount

def setup_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(pinNumberingType)
    GPIO.setup(pinNum, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    if readingtype == 1:
        GPIO.add_event_detect(pinNum, GPIO.BOTH, callback=coinInterrupt, bouncetime=bouncetime)

def cleanup_gpio():
    GPIO.cleanup()

def coinInterrupt(pin):
    global prev, total_amount
    gpio_val = GPIO.input(pinNum)
    if gpio_val == pulseVal and prev != pulseVal:
        total_amount += 1  # Increment total amount
        print("Received pulse. Total amount:", total_amount)
        sys.stdout.flush()
    prev = gpio_val

def loop():
    time.sleep(interval)

@app.route('/insertcoin', methods=["GET", "POST"])
def insertcoin():
    global total_amount
    # Calling setup function once

    try:
        print("Coin acceptor started. Press Ctrl+C to exit.")
        setup_gpio()  # Setup GPIO when the insert coin page is visited
        if readingtype == 2:
            while True:
                loop()
                # Check for POST request inside the loop
                if request.method == "POST":
                    new_money = Money(amount=total_amount)
                    db.session.add(new_money)
                    db.session.commit()
                    total_amount = 0  # Reset total_amount after saving to the database
                    return redirect(url_for('index'))
                else:
                    return render_template("insertcoin.html")
        else:
            while True:
                time.sleep(interval)
                # Check for POST request inside the loop
                if request.method == "POST":
                    new_money = Money(amount=total_amount)
                    db.session.add(new_money)
                    db.session.commit()
                    total_amount = 0  # Reset total_amount after saving to the database
                    return redirect(url_for('index'))
                else:
                    return render_template("insertcoin.html")
    except KeyboardInterrupt:
        GPIO.cleanup()  # Cleanup GPIO in case of keyboard interrupt
        return "KeyboardInterrupt occurred, GPIO cleaned up"

@app.route('/get_total_amount', methods=["GET"])
def get_total_amount():
    global total_amount
    # Calculate or obtain the latest total_amount here
    return jsonify(total_amount=total_amount)

if __name__ == "__main__":
    try:
        app.run(debug=True)
    finally:
        cleanup_gpio()  # Cleanup GPIO when the application exits