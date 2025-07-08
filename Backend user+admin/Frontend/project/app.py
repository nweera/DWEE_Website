from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb  # Add this import
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import uuid
import datetime
import MySQLdb.cursors
import secrets  # For generating secure tokens
from datetime import datetime, timedelta
from flask_login import LoginManager, current_user, login_required
import requests  # For API calls


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration - Updated for standalone MySQL
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'dwee'
app.config['MYSQL_PORT'] = 3306  

mysql = MySQL(app)

# Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'yaakoubn2004@gmail.com'
app.config['MAIL_PASSWORD'] = 'mgjv ccbg bvob mevb'
app.config['MAIL_DEFAULT_SENDER'] = 'yaakoubn2004@gmail.com' 

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

def send_reset_email(to_email, reset_link):
    msg = Message('Réinitialisation du mot de passe - D-WEE', recipients=[to_email])
    msg.body = f"""Bonjour,

Pour réinitialiser votre mot de passe, cliquez sur le lien ci-dessous :
{reset_link}

Ce lien expirera dans 1 heure. Si vous n'avez pas demandé cette réinitialisation, ignorez simplement ce message.

Merci,
L'équipe D-WEE
"""
    mail.send(msg)

# Add password_reset_tokens table if it doesn't exist
def init_db():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                token VARCHAR(100) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        mysql.connection.commit()

# Initialize database
with app.app_context():
    init_db()

@app.route('/', methods=['GET', 'POST'])
def login_signup():
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'register':
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            country = request.form.get('country', '').strip()
            province = request.form.get('province', '').strip()
            phone_prefix = request.form.get('phone_prefix', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()

            # Updated validation - removed hardcoded country check
            if not all([first_name, last_name, email, password, country, province, phone_prefix, phone, address]):
                flash('All fields are required.', 'error')
            elif len(password) < 8:
                flash('Password must be at least 8 characters long.', 'error')
            else:
                try:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    
                    # Check if email already exists
                    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                    if cursor.fetchone():
                        flash('This email is already registered. Please log in or use another email.', 'error')
                    else:
                        # Get role ID for 'user' - Updated to handle UUID
                        cursor.execute("SELECT id FROM roles WHERE name = %s", ('user',))
                        role_result = cursor.fetchone()
                        
                        if role_result:
                            role_id = role_result['id']
                            
                            # Combine phone prefix and number
                            full_phone = f"{phone_prefix}{phone}"
                            
                            # Insert new user
                            cursor.execute(
                                "INSERT INTO users (email, password_hash, first_name, last_name, phone_country_code, phone_number, address_country, address_province, address_detail, role_id, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                (email, password, first_name, last_name, phone_prefix, phone, country, province, address, role_id, 'active')
                            )
                            mysql.connection.commit()
                            flash('Registration successful! Please log in.', 'success')
                        else:
                            flash('User role not found. Please contact administrator.', 'register')
                    
                    cursor.close()
                
                except Exception as e:
                    flash(f'Registration failed: {str(e)}', 'error')

        elif form_type == 'login':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')

            if not email or not password:
                flash('Please enter both email and password.', 'error')
            else:
                try:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    
                    # First check in users table
                    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
                    user = cursor.fetchone()
                    
                    # If not found in users table, check in super_admins table
                    if not user:
                        cursor.execute('SELECT * FROM super_admins WHERE email = %s', (email,))
                        user = cursor.fetchone()
                        
                        if user:
                            # Check password for super admin
                            if user['password_hash'] == password:
                                session['loggedin'] = True
                                session['id'] = user['id']
                                session['email'] = user['email']
                                session['role_id'] = user['role_id']
                                session['first_name'] = user['first_name']
                                session['last_name'] = user['last_name']
                                
                                # For super admin, we already know the role
                                print("DEBUG: Super admin login successful")
                                return redirect(url_for('superadmin_dashboard'))  # This is correct
                            else:
                                flash('Incorrect password!', 'error')
                        else:
                            flash('Email not registered', 'error')
                    else:
                        # For regular users, continue with existing logic
                        if user['password_hash'] == password:
                            session['loggedin'] = True
                            session['id'] = user['id']
                            session['email'] = user['email']
                            session['role_id'] = user['role_id']
                            session['first_name'] = user['first_name']
                            session['last_name'] = user['last_name']

                            # Check user role and redirect accordingly
                            cursor.execute("SELECT name FROM roles WHERE id = %s", (user['role_id'],))
                            role = cursor.fetchone()
                            
                            print(f"DEBUG: User role: {role}")
                            
                            if role and role['name'].lower() == 'superadmin':
                                return redirect(url_for('superadmin_dashboard'))
                            elif role and role['name'].lower() == 'sales':
                                return redirect(url_for('sales_rep_dashboard'))
                            else:
                                return redirect(url_for('user_dashboard'))
                        else:
                            flash('Incorrect password!', 'error')
                    
                    cursor.close()
                
                except Exception as e:
                    flash(f'Login failed: {str(e)}', 'login')
                    print(f"Login error: {e}")  # For debugging

        elif form_type == 'forgot':
            email = request.form.get('email', '').strip()
            if not email:
                flash('Please enter your email address.', 'error')
            else:
                try:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
                    user = cursor.fetchone()
                    
                    if user:
                        # Generate a secure token
                        token = secrets.token_urlsafe(32)
                        expires_at = datetime.now() + timedelta(hours=1)
                        
                        # Store the token in the database
                        cursor.execute(
                            'INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)',
                            (user['id'], token, expires_at)
                        )
                        mysql.connection.commit()
                        
                        # Send the reset link via email using the send_reset_email function
                        reset_link = url_for('reset_password', token=token, _external=True)
                        try:
                            send_reset_email(email, reset_link)
                            flash('A password reset link has been sent to your email address.', 'success')
                        except Exception as e:
                            flash(f'Failed to send email: {str(e)}', 'error')
                    else:
                        flash('No account found with that email address.', 'error')
                    
                    cursor.close()
                except Exception as e:
                    flash(f'Password reset failed: {str(e)}', 'error')
                    print(f"Password reset error: {e}")

    return render_template('Login_signup_index.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not new_password or not confirm_password:
            flash('Please fill in all fields.')
        elif len(new_password) < 8:
            flash('Password must be at least 8 characters long.')
        elif new_password != confirm_password:
            flash('Passwords do not match.')
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # Check if token is valid and not expired
            cursor.execute('''
                SELECT user_id FROM password_reset_tokens 
                WHERE token = %s AND expires_at > NOW() 
                ORDER BY created_at DESC LIMIT 1
            ''', (token,))
            token_data = cursor.fetchone()
            
            if token_data:
                # Update the user's password
                cursor.execute(
                    'UPDATE users SET password_hash = %s WHERE id = %s',
                    (new_password, token_data['user_id'])
                )
                # Delete the used token
                cursor.execute('DELETE FROM password_reset_tokens WHERE token = %s', (token,))
                mysql.connection.commit()
                flash('Your password has been reset successfully. Please log in with your new password.')
                return redirect(url_for('login_signup'))
            else:
                flash('Invalid or expired reset token.')
    
    return render_template('Login_reset_password.html')

def get_role_id(role_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
    result = cursor.fetchone()
    cursor.close()
    return result['id'] if result else None

def get_role_id_by_name(role_name):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT id FROM roles WHERE name = %s', (role_name,))
        result = cur.fetchone()
        cur.close()
        return result['id'] if result else None
    except Exception as e:
        print(f"Error getting role ID: {e}")
        return None

# Add API proxy routes to avoid CORS issues
@app.route('/api/countries')
def get_countries():
    import requests
    
    headers = {
        'X-CSCAPI-KEY': 'QXJXRGZqd085dGRHYlVocmR2cFdrUlVpUnFOVkVMNm1adENlWmxEbw=='
    }
    
    try:
        response = requests.get('https://api.countrystatecity.in/v1/countries', headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        print(f"API Error: {e}")
        # Return fallback countries with phone codes if API fails
        fallback_countries = [
            {"iso2": "TN", "name": "Tunisia", "phonecode": "+216"},
            {"iso2": "CA", "name": "Canada", "phonecode": "+1"},
            {"iso2": "US", "name": "United States", "phonecode": "+1"},
            {"iso2": "FR", "name": "France", "phonecode": "+33"},
            {"iso2": "GB", "name": "United Kingdom", "phonecode": "+44"},
            {"iso2": "DE", "name": "Germany", "phonecode": "+49"},
            {"iso2": "IT", "name": "Italy", "phonecode": "+39"},
            {"iso2": "ES", "name": "Spain", "phonecode": "+34"},
            {"iso2": "MA", "name": "Morocco", "phonecode": "+212"},
            {"iso2": "DZ", "name": "Algeria", "phonecode": "+213"},
            {"iso2": "EG", "name": "Egypt", "phonecode": "+20"}
        ]
        return jsonify(fallback_countries)

@app.route('/api/states/<country_iso>')
def get_states(country_iso):
    import requests
    
    headers = {
        'X-CSCAPI-KEY': 'QXJXRGZqd085dGRHYlVocmR2cFdrUlVpUnFOVkVMNm1adENlWmxEbw=='  # Same API key here
    }
    
    try:
        response = requests.get(f'https://api.countrystatecity.in/v1/countries/{country_iso}/states', headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        print(f"States API Error: {e}")
        return jsonify([])

@app.route('/api/cities/<country_iso>/<state_iso>')
def get_cities(country_iso, state_iso):
    import requests
    
    headers = {
        'X-CSCAPI-KEY': 'QXJXRGZqd085dGRHYlVocmR2cFdrUlVpUnFOVkVMNm1adENlWmxEbw=='  # Same API key here
    }
    
    try:
        response = requests.get(f'https://api.countrystatecity.in/v1/countries/{country_iso}/states/{state_iso}/cities', headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        print(f"Cities API Error: {e}")
        return jsonify([])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_signup'))

#############################################################
#USER DASHBOARD ROUTES
#############################################################

@app.route('/user_dashboard')
def user_dashboard():
    if 'id' not in session:
        return redirect(url_for('login_signup'))

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Fetch user info
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    # Fetch only validated D-KITs*
    cursor.execute("SELECT * FROM devices WHERE user_id = %s AND validated = 1", (user_id,))
    devices = cursor.fetchall()
    # Fetch confirmed urgent maintenances
    cursor.execute("""
        SELECT a.*, d.serial_number, 'urgente' as type
        FROM maintenances_urgentes a
        JOIN devices d ON a.device_serial_number = d.serial_number
        WHERE d.user_id = %s AND a.status = 'confirmed'
    """, (user_id,))
    urgent_appointments = cursor.fetchall()
    # Fetch confirmed regular maintenances
    cursor.execute("""
        SELECT a.*, d.serial_number, 'reguliere' as type
        FROM maintenances_regulieres a
        JOIN devices d ON a.device_serial_number = d.serial_number
        WHERE d.user_id = %s AND a.status = 'confirmed'
    """, (user_id,))
    regular_appointments = cursor.fetchall()
    # Ensure all are dicts (robustness)
    urgent_appointments = [dict(x) for x in urgent_appointments]
    regular_appointments = [dict(x) for x in regular_appointments]
    # Merge both lists
    appointments = urgent_appointments + regular_appointments
    # Sort by datetime ascending
    appointments.sort(key=lambda x: x['datetime'])
    # Fetch notifications if you have a notifications table or logic
    notifications = []  # Replace with your notification fetching logic if needed
    cursor.close()
    return render_template('user_dashboard.html', user=user, devices=devices, appointments=appointments, notifications=notifications)

@app.route('/user_dkits')
def user_dkits():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['id'],))
        user = cursor.fetchone()
        cursor.execute("SELECT * FROM devices WHERE user_id = %s", (session['id'],))
        devices = cursor.fetchall()
        cursor.close()
        python_data = {"example": 123}  # Replace with your actual data
        return render_template(
            'user_dkits.html',
            python_data=python_data,
            user=user,
            devices=devices
        )
    else:
        return redirect(url_for('login_signup'))

@app.route('/user_calendar')
def user_calendar():
    if 'id' not in session:
        return redirect(url_for('login_signup'))
    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM devices WHERE user_id = %s AND validated = 1", (user_id,))
    validated_devices = cursor.fetchall()
    cursor.close()
    return render_template(
        'user_calendar.html',
        user=user,
        validated_devices=validated_devices
    )

@app.route('/user_profile')
def user_profile():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
        user = cursor.fetchone()
        cursor.close()
        return render_template('user_profile.html', user=user)
    else:
        return redirect(url_for('login_signup'))

@app.route('/user_support')
def user_support():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT first_name, last_name FROM users WHERE id = %s', (session['id'],))
        user = cursor.fetchone()
        cursor.close()
        return render_template('user_support.html', user=user)
    else:
        return redirect(url_for('login_signup'))

@app.route('/user_commercial_registration', methods=['GET', 'POST'])
def user_commercial_registration():
    if 'loggedin' not in session:
        return redirect(url_for('login_signup'))

    user_role = session.get('role', 'user')
    if user_role == 'superadmin':
        dashboard_url = url_for('superadmin_dashboard')
    elif user_role == 'sales':
        dashboard_url = url_for('sales_rep_dashboard')
    else:
        dashboard_url = url_for('user_dashboard')

    if request.method == 'POST':
        print('DEBUG: Received POST to /user_commercial_registration')
        raison_sociale = request.form.get('raisonSociale', '').strip()
        matricule_fiscale = request.form.get('matriculeFiscale', '').strip()
        adresse = request.form.get('adresse', '').strip()
        telephone = request.form.get('telephone', '').strip()
        email = request.form.get('email', '').strip()
        secteur_activite = request.form.get('secteurActivite', '').strip()
        motivation = request.form.get('motivation', '').strip()
        user_id = session['id']

        print(f'DEBUG: Data - raison_sociale={raison_sociale}, matricule_fiscale={matricule_fiscale}, adresse={adresse}, telephone={telephone}, email={email}, secteur_activite={secteur_activite}, motivation={motivation}, user_id={user_id}')

        # Check if user already has a registration
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id FROM commercial_registrations WHERE user_id = %s", (user_id,))
        existing = cursor.fetchone()
        if existing:
            flash("Vous avez déjà soumis une demande d'inscription commerciale.", "error")
            cursor.close()
            return render_template('user_commercial-registration.html', dashboard_url=dashboard_url)

        if secteur_activite == 'autre':
            secteur_activite = request.form.get('autreSecteur', '').strip()

        if not raison_sociale or not matricule_fiscale or not adresse or not telephone or not email or not secteur_activite:
            flash("Tous les champs obligatoires doivent être remplis.", "error")
            cursor.close()
            return render_template('user_commercial-registration.html', dashboard_url=dashboard_url)

        try:
            cursor.execute("""
                INSERT INTO commercial_registrations
                (user_id, raison_sociale, matricule_fiscale, adresse, telephone, email, secteur_activite, motivation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, raison_sociale, matricule_fiscale, adresse, telephone, email, secteur_activite, motivation))
            mysql.connection.commit()
            cursor.close()
            flash("Inscription commerciale réussie ! Votre demande a été envoyée.", "success")
            print('DEBUG: Insert successful')
            return render_template('user_commercial-registration.html', dashboard_url=dashboard_url, registration_success=True)
        except Exception as e:
            print(f'DEBUG: Exception - {e}')
            flash(f"Erreur lors de l'envoi de la demande : {str(e)}", "error")
            cursor.close()
            return render_template('user_commercial-registration.html', dashboard_url=dashboard_url)

    return render_template('user_commercial-registration.html', dashboard_url=dashboard_url)

@app.route('/user_add_dkit', methods=['POST'])
def user_add_dkit():
    if 'loggedin' in session:
        serial_number = request.form.get('serial_number', '').strip()
        purchase_date = request.form.get('purchase_date', '').strip()
        location = request.form.get('location', '').strip()
        status = 'active'
        model = None  # Model will be added later by admin

        if not serial_number or not purchase_date or not location:
            flash('All fields are required.', 'error')
        else:
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute(
                    "INSERT INTO devices (user_id, serial_number, model, status, validated) VALUES (%s, %s, %s, %s, %s)",
                    (session['id'], serial_number, model, status, 0)
                )
                mysql.connection.commit()
                cursor.close()
                flash('D-KIT added successfully!', 'success')
            except Exception as e:
                flash(f'Failed to add D-KIT: {str(e)}', 'error')
        return redirect(url_for('user_dkits'))
    else:
        return redirect(url_for('login_signup'))

@app.route('/user_update_profile', methods=['POST'])
def user_update_profile():
    if 'loggedin' not in session:
        return redirect(url_for('login_signup'))

    user_id = session['id']
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    phone_number = request.form.get('phone', '').strip()
    # You can add address fields if you want to allow editing them

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            UPDATE users
            SET first_name = %s, last_name = %s, email = %s, phone_number = %s
            WHERE id = %s
        """, (first_name, last_name, email, phone_number, user_id))
        mysql.connection.commit()
        cursor.close()
        flash('Profil mis à jour avec succès!', 'success')
    except Exception as e:
        flash(f'Erreur lors de la mise à jour du profil: {str(e)}', 'error')

    return redirect(url_for('user_profile'))

@app.route('/user_add_appointment', methods=['POST'])
def user_add_appointment():
    if 'id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié.'}), 401

    data = request.get_json()
    user_id = session['id']
    dkit_serial = data.get('dkit')
    date = data.get('date')
    time = data.get('time')
    notes = data.get('description')

    # Find device id from serial number
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id FROM devices WHERE serial_number = %s AND user_id = %s", (dkit_serial, user_id))
    device = cursor.fetchone()
    if not device:
        return jsonify({'success': False, 'message': 'D-KIT non trouvé.'})

    # Combine date and time for datetime column
    datetime_str = f"{date} {time}:00"

    # Prevent booking in the past
    try:
        appointment_dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        cursor.close()
        return jsonify({'success': False, 'message': 'Format de date ou heure invalide.'})
    now = datetime.now()
    if appointment_dt < now:
        cursor.close()
        return jsonify({'success': False, 'message': 'Vous ne pouvez pas réserver dans le passé.'})
    # Prevent booking on weekends (Saturday=5, Sunday=6)
    if appointment_dt.weekday() in [5, 6]:
        cursor.close()
        return jsonify({'success': False, 'message': 'Vous ne pouvez pas réserver un rendez-vous le week-end.'})

    # Check if user already has an appointment at the same datetime
    cursor.execute('''
        SELECT mu.id FROM maintenances_urgentes mu
        JOIN devices d ON mu.device_serial_number = d.serial_number
        WHERE d.user_id = %s AND mu.datetime = %s
    ''', (user_id, datetime_str))
    existing_appointment = cursor.fetchone()
    if existing_appointment:
        cursor.close()
        return jsonify({'success': False, 'message': 'Vous avez déjà un rendez-vous de maintenance à cette date et heure.'})

    try:
        cursor.execute(
            "INSERT INTO maintenances_urgentes (device_serial_number, datetime, status, notes, technician_id, time_change_status, requested_time) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (dkit_serial, datetime_str, 'scheduled', notes, None, 0, None)
        )
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        cursor.close()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/user/request_change_maintenance_time', methods=['POST'])
def request_change_maintenance_time():
    if 'id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié.'}), 401

    data = request.get_json()
    maintenance_type = data.get('type')  # 'urgent' or 'reguliere'
    maintenance_id = data.get('maintenance_id')
    new_datetime = data.get('requested_datetime')

    if maintenance_type == 'urgent':
        table = 'maintenances_urgentes'
    else:
        table = 'maintenances_regulieres'

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute(
            f"UPDATE {table} SET status = %s, time_change_status = %s, requested_time = %s WHERE id = %s",
            ('scheduled', 1, new_datetime, maintenance_id)
        )
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Demande de changement envoyée.'})
    except Exception as e:
        cursor.close()
        return jsonify({'success': False, 'message': str(e)})


#############################################################
#USER DASHBOARD ROUTES
#############################################################


@app.route('/admin/approve_change_maintenance_time', methods=['POST'])
def approve_change_maintenance_time():
    data = request.get_json()
    maintenance_type = data.get('type')  # 'urgent' or 'reguliere'
    maintenance_id = data.get('maintenance_id')
    approve = data.get('approve')  # True or False
    
    print(f'DEBUG: Admin processing time change request - maintenance_id={maintenance_id}, type={maintenance_type}, approve={approve}')

    if maintenance_type == 'urgent':
        table = 'maintenances_urgentes'
    else:
        table = 'maintenances_regulieres'

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    try:
        # First fetch the current maintenance to log its state
        cursor.execute(f"SELECT * FROM {table} WHERE id = %s", (maintenance_id,))
        maintenance = cursor.fetchone()
        
        if maintenance:
            print(f'DEBUG: Before approval - maintenance id={maintenance_id}, status={maintenance["status"]}, ' +
                  f'time_change_status={maintenance.get("time_change_status")}, ' +
                  f'datetime={maintenance.get("datetime")}, requested_time={maintenance.get("requested_time")}')
        
        if approve:
            # Approve: set status to confirmed, time_change_status to 2, datetime to requested_time, requested_time to NULL
            cursor.execute(
                f"UPDATE {table} SET status = %s, time_change_status = %s, datetime = requested_time, requested_time = NULL WHERE id = %s",
                ('confirmed', 2, maintenance_id)
            )
            print(f'DEBUG: Approved time change request for {maintenance_id}, status set to confirmed, time updated')
        else:
            # Decline: set status to confirmed (back to original), time_change_status to 3 (declined)
            cursor.execute(
                f"UPDATE {table} SET status = %s, time_change_status = %s, requested_time = NULL WHERE id = %s",
                ('confirmed', 3, maintenance_id)
            )
            print(f'DEBUG: Declined time change request for {maintenance_id}, status set back to confirmed')
        
        # Fetch the updated maintenance to verify changes
        cursor.execute(f"SELECT * FROM {table} WHERE id = %s", (maintenance_id,))
        updated = cursor.fetchone()
        
        if updated:
            print(f'DEBUG: After approval decision - maintenance id={maintenance_id}, status={updated["status"]}, ' +
                  f'time_change_status={updated.get("time_change_status")}, ' +
                  f'datetime={updated.get("datetime")}, requested_time={updated.get("requested_time")}')
        
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Demande traitée avec succès'})
    except Exception as e:
        print(f'DEBUG: Error processing approval: {str(e)}')
        cursor.close()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/user_maintenances')
def api_user_maintenances():
    user_id = session.get('id')
    if not user_id:
        return jsonify({'urgent_maintenances': [], 'regular_maintenances': []})

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cur.execute("""
            SELECT m.*, d.serial_number 
            FROM maintenances_urgentes m
            JOIN devices d ON m.device_serial_number = d.serial_number
            WHERE d.user_id = %s
        """, (user_id,))
        urgent_maintenances = cur.fetchall()
        cur.execute("""
            SELECT m.*, d.serial_number 
            FROM maintenances_regulieres m
            JOIN devices d ON m.device_serial_number = d.serial_number
            WHERE d.user_id = %s
        """, (user_id,))
        regular_maintenances = cur.fetchall()
    except Exception as e:
        print(f"Error fetching maintenances: {e}")
        urgent_maintenances = []
        regular_maintenances = []
    finally:
        cur.close()

    # Convert datetime fields to ISO format or empty string
    for app in urgent_maintenances:
        dt = app.get('datetime')
        if isinstance(dt, (datetime, )):
            app['datetime'] = dt.strftime('%Y-%m-%d %H:%M')
        elif dt is None:
            app['datetime'] = ''
        else:
            app['datetime'] = str(dt)[:16].replace('T', ' ')
        req = app.get('requested_time')
        if isinstance(req, (datetime, )):
            app['requested_time'] = req.strftime('%Y-%m-%d %H:%M')
        elif req is None:
            app['requested_time'] = ''
        else:
            app['requested_time'] = str(req)[:16].replace('T', ' ')
    for app in regular_maintenances:
        dt = app.get('datetime')
        if isinstance(dt, (datetime, )):
            app['datetime'] = dt.strftime('%Y-%m-%d %H:%M')
        elif dt is None:
            app['datetime'] = ''
        else:
            app['datetime'] = str(dt)[:16].replace('T', ' ')
        req = app.get('requested_time')
        if isinstance(req, (datetime, )):
            app['requested_time'] = req.strftime('%Y-%m-%d %H:%M')
        elif req is None:
            app['requested_time'] = ''
        else:
            app['requested_time'] = str(req)[:16].replace('T', ' ')

    return jsonify({
        'urgent_maintenances': urgent_maintenances,
        'regular_maintenances': regular_maintenances
    })

@app.route('/api/add_dkit', methods=['POST'])
def add_dkit():
    if 'id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié.'}), 401
    data = request.get_json()
    serial = data.get('serial_number')
    purchase_date = data.get('purchase_date')
    location = data.get('location')
    user_id = session['id']
    if not serial or not purchase_date or not location:
        return jsonify({'success': False, 'message': 'Tous les champs sont requis.'})
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO devices (user_id, serial_number, purchase_date, location) VALUES (%s, %s, %s, %s)",
            (user_id, serial, purchase_date, location)
        )
        mysql.connection.commit()
        return jsonify({'success': True, 'message': 'D-KIT ajouté avec succès.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cur.close()

@app.route('/api/delete_urgent_maintenance/<int:maintenance_id>', methods=['DELETE'])
def delete_urgent_maintenance(maintenance_id):
    if 'id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié.'}), 401
    user_id = session['id']
    cur = mysql.connection.cursor()
    try:
        # Only allow deleting if the maintenance belongs to the user's device
        cur.execute("""
            DELETE m FROM maintenances_urgentes m
            JOIN devices d ON m.device_serial_number = d.serial_number
            WHERE m.id = %s AND d.user_id = %s
        """, (maintenance_id, user_id))
        mysql.connection.commit()
        if cur.rowcount > 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Suppression non autorisée ou maintenance introuvable.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cur.close()

@app.route('/api/update_urgent_maintenance/<int:maintenance_id>', methods=['PUT'])
def update_urgent_maintenance(maintenance_id):
    if 'id' not in session:
        print('DEBUG: Not authenticated')
        return jsonify({'success': False, 'message': 'Non authentifié.'}), 401
    
    data = request.get_json()
    user_id = session['id']
    dkit_serial = data.get('dkit')
    date = data.get('date')
    time = data.get('time')
    notes = data.get('description')
    
    print(f'DEBUG: user_id={user_id}, maintenance_id={maintenance_id}, dkit_serial={dkit_serial}, date={date}, time={time}, notes={notes}')
    
    if not dkit_serial or not date or not time or not notes:
        print('DEBUG: Missing fields')
        return jsonify({'success': False, 'message': 'Tous les champs sont requis.'})
    
    requested_datetime = f"{date} {time}:00"
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    try:
        cur.execute("SELECT * FROM maintenances_urgentes m JOIN devices d ON m.device_serial_number = d.serial_number WHERE m.id = %s AND d.user_id = %s", (maintenance_id, user_id))
        maintenance = cur.fetchone()
        print(f'DEBUG: maintenance row before update: {maintenance}')
        
        if not maintenance:
            return jsonify({'success': False, 'message': 'Modification non autorisée ou maintenance introuvable.'})
        
        # Determine update logic based on status and time_change_status
        if maintenance['status'] == 'scheduled':
            if maintenance.get('time_change_status', 0) == 1:
                # Only update requested_time, not datetime
                cur.execute("""
                    UPDATE maintenances_urgentes m
                    JOIN devices d ON m.device_serial_number = d.serial_number
                    SET m.requested_time = %s, m.notes = %s
                    WHERE m.id = %s AND d.user_id = %s
                """, (requested_datetime, notes, maintenance_id, user_id))
            else:
                # Directly update datetime
                cur.execute("""
                    UPDATE maintenances_urgentes m
                    JOIN devices d ON m.device_serial_number = d.serial_number
                    SET m.datetime = %s, m.notes = %s
                    WHERE m.id = %s AND d.user_id = %s
                """, (requested_datetime, notes, maintenance_id, user_id))
        elif maintenance['status'] == 'confirmed':
            # Keep original datetime, save requested_time and change status to scheduled with time_change_status = 1
            # This indicates a change request that needs admin approval
            original_datetime = maintenance['datetime']
            print(f'DEBUG: User modifying a confirmed maintenance. Original datetime: {original_datetime}, Requested new time: {requested_datetime}')
            
            cur.execute("""
                UPDATE maintenances_urgentes m
                JOIN devices d ON m.device_serial_number = d.serial_number
                SET m.status = %s, m.time_change_status = %s, m.requested_time = %s, m.notes = %s
                WHERE m.id = %s AND d.user_id = %s
            """, ('scheduled', 1, requested_datetime, notes, maintenance_id, user_id))
            
            # Verify the update was applied correctly
            cur.execute("SELECT datetime, requested_time, status, time_change_status FROM maintenances_urgentes WHERE id = %s", (maintenance_id,))
            updated = cur.fetchone()
            print(f'DEBUG: After update - datetime: {updated["datetime"]}, requested_time: {updated["requested_time"]}, status: {updated["status"]}, time_change_status: {updated["time_change_status"]}')
        else:
            return jsonify({'success': False, 'message': 'Modification non autorisée pour ce statut.'})
        mysql.connection.commit()
        print(f'DEBUG: cur.rowcount after update: {cur.rowcount}')
        if cur.rowcount > 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Modification non autorisée ou maintenance introuvable.'})
    except Exception as e:
        print(f'DEBUG: Exception: {e}')
        return jsonify({'success': False, 'message': str(e)}) 
    finally:
        cur.close()

@app.route('/api/update_regular_maintenance/<int:maintenance_id>', methods=['PUT'])
def update_regular_maintenance(maintenance_id):
    if 'id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié.'}), 401
    data = request.get_json()
    user_id = session['id']
    dkit_serial = data.get('dkit')
    date = data.get('date')
    time = data.get('time')
    notes = data.get('description')
    if not dkit_serial or not date or not time or not notes:
        return jsonify({'success': False, 'message': 'Tous les champs sont requis.'})
    requested_datetime = f"{date} {time}:00"
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM maintenances_regulieres m JOIN devices d ON m.device_serial_number = d.serial_number WHERE m.id = %s AND d.user_id = %s", (maintenance_id, user_id))
        maintenance = cur.fetchone()
        if not maintenance:
            return jsonify({'success': False, 'message': 'Modification non autorisée ou maintenance introuvable.'})
        cur.execute("""
            UPDATE maintenances_regulieres m
            JOIN devices d ON m.device_serial_number = d.serial_number
            SET m.status = %s, m.time_change_status = %s, m.requested_time = %s, m.description = %s
            WHERE m.id = %s AND d.user_id = %s
        """, ('scheduled', 1, requested_datetime, notes, maintenance_id, user_id))
        mysql.connection.commit()
        if cur.rowcount > 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Modification non autorisée ou maintenance introuvable.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cur.close()

@app.route('/user_change_password', methods=['POST'])
def user_change_password():
    if 'loggedin' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié.'}), 401
    data = request.get_json()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'Tous les champs sont requis.'}), 400
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT password_hash FROM users WHERE id = %s', (session['id'],))
    user = cursor.fetchone()
    if not user or user['password_hash'] != current_password:
        cursor.close()
        return jsonify({'success': False, 'message': 'Mot de passe actuel incorrect.'}), 400
    cursor.execute('UPDATE users SET password_hash = %s WHERE id = %s', (new_password, session['id']))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'success': True, 'message': 'Mot de passe changé avec succès.'})

def get_maintenance_lifecycle(entry):
    # Determine wished_datetime and actual_datetime
    wished_datetime = entry.get('requested_time') or entry.get('datetime')
    actual_datetime = entry.get('datetime')
    # Determine status
    if entry.get('status') == 'confirmed' and not entry.get('requested_time'):
        status = 'confirmed'
    elif entry.get('requested_time') and entry.get('requested_time') != entry.get('datetime'):
        status = 'modified'
    else:
        status = 'scheduled'
    return {
        'id': entry.get('id'),
        'device_serial_number': entry.get('device_serial_number'),
        'wished_datetime': str(wished_datetime)[:16].replace('T', ' ') if wished_datetime else '',
        'actual_datetime': str(actual_datetime)[:16].replace('T', ' ') if actual_datetime else '',
        'status': status,
        'notes': entry.get('notes', ''),
        'type': 'urgent' if 'maintenances_urgentes' in entry.get('table', '') else 'regular'
    }

@app.route('/api/user_maintenances_lifecycle')
def api_user_maintenances_lifecycle():
    user_id = session.get('id')
    if not user_id:
        return jsonify({'urgent_maintenances': [], 'regular_maintenances': []})
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cur.execute("""
            SELECT m.*, d.serial_number, 'maintenances_urgentes' as table_name
            FROM maintenances_urgentes m
            JOIN devices d ON m.device_serial_number = d.serial_number
            WHERE d.user_id = %s
        """, (user_id,))
        urgent_maintenances = cur.fetchall()
        cur.execute("""
            SELECT m.*, d.serial_number, 'maintenances_regulieres' as table_name
            FROM maintenances_regulieres m
            JOIN devices d ON m.device_serial_number = d.serial_number
            WHERE d.user_id = %s
        """, (user_id,))
        regular_maintenances = cur.fetchall()
    except Exception as e:
        print(f"Error fetching maintenances: {e}")
        urgent_maintenances = []
        regular_maintenances = []
    finally:
        cur.close()
    # Process lifecycle for each
    urgent = [get_maintenance_lifecycle(dict(x, table='maintenances_urgentes')) for x in urgent_maintenances]
    regular = [get_maintenance_lifecycle(dict(x, table='maintenances_regulieres')) for x in regular_maintenances]
    return jsonify({'urgent_maintenances': urgent, 'regular_maintenances': regular})

@app.route('/admin/dashboard')
def superadmin_dashboard():
    # Initialize variables for dashboard stats
    stats = {
        'total_users': 0,
        'new_users_today': 0,
        'total_devices': 0,
        'validated_devices': 0,
        'validated_devices_percentage': 0,
        'device_change': 0
    }
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get total number of users
        cursor.execute('SELECT COUNT(*) as count FROM users')
        result = cursor.fetchone()
        stats['total_users'] = result['count'] if result else 0
        
        # Get new users registered today
        today = datetime.now().date()
        cursor.execute('SELECT COUNT(*) as count FROM users WHERE DATE(created_at) = %s', (today,))
        result = cursor.fetchone()
        stats['new_users_today'] = result['count'] if result else 0
        
        # Get total number of devices
        cursor.execute('SELECT COUNT(*) as count FROM devices')
        result = cursor.fetchone()
        stats['total_devices'] = result['count'] if result else 0
        
        # Get number of validated devices (using the validated column)
        cursor.execute('SELECT COUNT(*) as count FROM devices WHERE validated = 1')
        result = cursor.fetchone()
        validated_devices = result['count'] if result else 0
        stats['validated_devices'] = validated_devices
        
        # Calculate percentage of validated devices
        if stats['total_devices'] > 0:
            stats['validated_devices_percentage'] = int((validated_devices / stats['total_devices']) * 100)
        else:
            stats['validated_devices_percentage'] = 0
        
        # Get device change (new devices added or removed in the last 7 days)
        cursor.execute('''
            SELECT 
                (SELECT COUNT(*) FROM devices WHERE DATE(created_at) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)) -
                (SELECT COUNT(*) FROM devices WHERE DATE(deactivated_at) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY))
            as net_change
        ''')
        result = cursor.fetchone()
        stats['device_change'] = result['net_change'] if result and result['net_change'] is not None else 0
        
        # Get recent activities - Try to fetch from activities table if it exists
        activities = []
        try:
            cursor.execute('''
                SELECT a.action_type, a.action_date, a.status,
                       CONCAT(u.first_name, ' ', u.last_name) as user_name,
                       CASE
                           WHEN a.status = 'pending' THEN 'En attente'
                           WHEN a.status = 'approved' THEN 'Approuvé'
                           WHEN a.status = 'active' THEN 'Terminé'
                           WHEN a.status = 'rejected' THEN 'Refusé'
                           ELSE a.status
                       END as status_text
                FROM activities a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.action_date DESC
                LIMIT 5
            ''')
            activities = cursor.fetchall()
        except Exception as e:
            print(f"Error fetching activities: {str(e)}")
            # If no activities table or error, we'll use the default hardcoded entries
            activities = [
                {
                    'action_type': 'user_registration',
                    'action_date': datetime.now(),
                    'status': 'active',
                    'user_name': 'Admin',
                    'status_text': 'Terminé'
                },
                {
                    'action_type': 'device_activation',
                    'action_date': datetime.now(),
                    'status': 'active',
                    'user_name': 'Admin',
                    'status_text': 'Terminé'
                }
            ]
        
        cursor.close()
        
        # Add activities to the stats dictionary
        stats['activities'] = activities
        
    except Exception as e:
        print(f"Error fetching dashboard stats: {str(e)}")
    
    return render_template('admin_dashboard.html', **stats)

@app.route('/admin/user-management')
def admin_user_management():
    return render_template('admin_userManagement.html')

@app.route('/admin/sales-representative')
def admin_sales_representative():
    return render_template('admin_salesRepresentative.html')

@app.route('/admin/appointment')
def admin_appointment():
    return render_template('admin_appointment.html')

# API endpoint to get a specific maintenance request by ID
@app.route('/api/maintenance/<int:maintenance_id>', methods=['GET'])
def get_maintenance_by_id(maintenance_id):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        query = '''
        SELECT 
            mu.id,
            mu.device_serial_number,
            mu.datetime,
            mu.status,
            mu.description,
            CONCAT(u.first_name, ' ', u.last_name) AS client_name,
            u.id AS user_id,
            DATE_FORMAT(mu.datetime, '%d/%m/%Y') AS formatted_date,
            DATE_FORMAT(mu.datetime, '%H:%i') AS formatted_time,
            d.model AS device_model
        FROM maintenances_urgentes mu
        JOIN devices d ON mu.device_serial_number = d.serial_number
        JOIN users u ON d.user_id = u.id
        WHERE mu.id = %s
        '''
        
        cursor.execute(query, (maintenance_id,))
        maintenance = cursor.fetchone()
        cursor.close()
        
        if maintenance:
            return jsonify({"success": True, "maintenance": maintenance})
        else:
            return jsonify({"success": False, "message": "Maintenance non trouvée"}), 404
            
    except Exception as e:
        print(f"Error fetching maintenance by ID: {str(e)}")
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

# API endpoint to get all pending maintenance requests
@app.route('/api/maintenance/pending', methods=['GET'])
def get_pending_maintenances():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = '''
        SELECT 
            mu.id,
            mu.device_serial_number,
            mu.datetime,
            mu.status,
            mu.notes,
            mu.time_change_status,
            mu.requested_time,
            CONCAT(u.first_name, ' ', u.last_name) AS client_name,
            u.id AS user_id,
            DATE_FORMAT(mu.datetime, '%d/%m/%Y') AS formatted_date,
            DATE_FORMAT(mu.datetime, '%H:%i') AS formatted_time,
            DATE_FORMAT(mu.requested_time, '%d/%m/%Y') AS requested_date,
            DATE_FORMAT(mu.requested_time, '%H:%i') AS requested_time_formatted,
            d.model AS device_model,
            CONCAT(u.address_province, ', ', u.address_country) AS location
        FROM maintenances_urgentes mu
        JOIN devices d ON mu.device_serial_number = d.serial_number
        JOIN users u ON d.user_id = u.id
        WHERE mu.status = 'scheduled'
        ORDER BY mu.datetime ASC
        '''
        
        print("Executing query for pending/scheduled maintenance requests")
        cursor.execute(query)
        maintenances = cursor.fetchall()
        print(f"Found {len(maintenances)} pending/scheduled maintenance requests")
          # Process the results to ensure all required fields are present
        for maintenance in maintenances:
            # Convert datetime objects to string if they're not already formatted
            if isinstance(maintenance['datetime'], datetime):
                maintenance['formatted_date'] = maintenance['datetime'].strftime('%d/%m/%Y')
                maintenance['formatted_time'] = maintenance['datetime'].strftime('%H:%M')
            
            # Format requested_time if it exists
            if maintenance.get('requested_time') and isinstance(maintenance['requested_time'], datetime):
                maintenance['requested_date'] = maintenance['requested_time'].strftime('%d/%m/%Y')
                maintenance['requested_time_formatted'] = maintenance['requested_time'].strftime('%H:%M')
            
            # Determine which datetime to use for display
            if maintenance.get('time_change_status') == 1 and maintenance.get('requested_time'):
                # Use requested_time if time_change_status=1
                maintenance['display_datetime'] = maintenance.get('requested_time')
                maintenance['display_date'] = maintenance.get('requested_date', 
                                                            maintenance.get('formatted_date'))
                maintenance['display_time'] = maintenance.get('requested_time_formatted', 
                                                            maintenance.get('formatted_time'))
                maintenance['using_requested_time'] = True
                print(f"Maintenance {maintenance['id']}: Using requested time {maintenance['requested_time']}")
            else:
                # Use original datetime
                maintenance['display_datetime'] = maintenance.get('datetime')
                maintenance['display_date'] = maintenance.get('formatted_date')
                maintenance['display_time'] = maintenance.get('formatted_time')
                maintenance['using_requested_time'] = False
                print(f"Maintenance {maintenance['id']}: Using original datetime {maintenance['datetime']}")
                
            # Ensure the client_name exists, use placeholder if missing
            if not maintenance.get('client_name'):
                maintenance['client_name'] = 'Client inconnu'
                
            # Ensure device_model exists
            if not maintenance.get('device_model'):
                maintenance['device_model'] = 'Modèle inconnu'
            
            # Ensure location exists
            if not maintenance.get('location'):
                maintenance['location'] = 'Localisation inconnue'
        
        cursor.close()
        
        return jsonify({"success": True, "maintenances": maintenances})
        
    except Exception as e:
        print(f"Error fetching pending maintenances: {str(e)}")
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500


# API endpoint to update maintenance status
@app.route('/api/maintenance/<int:maintenance_id>/status', methods=['POST'])
def update_maintenance_status(maintenance_id):
    try:
        # Debug the incoming request
        print(f"Request method: {request.method}")
        print(f"Request headers: {request.headers}")
        print(f"Request raw data: {request.data}")
        
        # Try to parse JSON properly
        try:
            data = request.json
            print(f"Received status update data (parsed JSON): {data}")
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            # Try to decode manually
            try:
                import json
                data = json.loads(request.data.decode('utf-8'))
                print(f"Manual JSON parse result: {data}")
            except Exception as e2:
                print(f"Manual parse failed too: {e2}")
                data = {}
        
        request_status = data.get('status')
        reject_reason = data.get('reason')
        
        print(f"Processing status update: status={request_status}, reason={reject_reason}")
        
        # Map the requested status to our database status values
        status_mapping = {
            'accepted': 'confirmed',
            'rejected': 'cancelled',
            'confirmed': 'confirmed',  # Allow direct 'confirmed' status from the frontend
            'cancelled': 'cancelled'   # Allow direct 'cancelled' status from the frontend
        }
        
        db_status = status_mapping.get(request_status)
        print(f"Mapped status '{request_status}' to '{db_status}'")
        if not db_status:
            print(f"Invalid status received: {request_status}")
            error_response = {"success": False, "message": f"Statut invalide: {request_status}"}
            print(f"Sending error response: {error_response}")
            return jsonify(error_response), 400
            
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if the maintenance request exists
        cursor.execute('SELECT * FROM maintenances_urgentes WHERE id = %s', (maintenance_id,))
        maintenance = cursor.fetchone()
        
        if not maintenance:
            return jsonify({"success": False, "message": "Demande de maintenance introuvable"}), 404
        
        # Update the status
        if db_status == 'cancelled' and reject_reason:
            try:
                # First check if the 'reject_reason' column exists
                cursor.execute("SHOW COLUMNS FROM maintenances_urgentes LIKE 'reject_reason'")
                if cursor.fetchone():
                    cursor.execute(
                        'UPDATE maintenances_urgentes SET status = %s, reject_reason = %s WHERE id = %s',
                        (db_status, reject_reason, maintenance_id)
                    )
                else:
                    # If the column doesn't exist, still update the status but store the reason in notes
                    cursor.execute(
                        'UPDATE maintenances_urgentes SET status = %s, notes = CONCAT(IFNULL(notes, ""), " | Raison du refus: ", %s) WHERE id = %s',
                        (db_status, reject_reason, maintenance_id)
                    )
                print(f"Updated maintenance {maintenance_id} status to {db_status} with reason: {reject_reason}")
            except Exception as e:
                # If there's any error, fall back to just updating the status
                print(f"Error updating with reject reason: {str(e)}")
                cursor.execute(
                    'UPDATE maintenances_urgentes SET status = %s WHERE id = %s',
                    (db_status, maintenance_id)
                )
        else:
            cursor.execute(
                'UPDATE maintenances_urgentes SET status = %s WHERE id = %s',
                (db_status, maintenance_id)
            )
            print(f"Updated maintenance {maintenance_id} status to {db_status}")
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({"success": True, "message": f"Statut de la maintenance mis à jour: {db_status}"})
        
    except Exception as e:
        print(f"Error updating maintenance status: {str(e)}")
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500
    
# API endpoint to get all accepted maintenance requests for calendar
@app.route('/api/maintenance/accepted', methods=['GET'])
def get_accepted_maintenances():
    try:
        print("===============================================")
        print("API CALL: /api/maintenance/accepted")
        print("===============================================")
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Debug - check total number of entries
        cursor.execute("SELECT COUNT(*) AS total_count FROM maintenances_urgentes")
        total = cursor.fetchone()
        print(f"Total entries in maintenances_urgentes: {total['total_count']}")
        
        # Debug - print all statuses available in the table
        cursor.execute("SELECT DISTINCT status FROM maintenances_urgentes")
        statuses = cursor.fetchall()
        print(f"Available statuses in maintenances_urgentes: {[s['status'] for s in statuses]}")
        
        # List a few confirmed maintenances for debugging (limited to 5)
        cursor.execute("SELECT id, device_serial_number, datetime, status FROM maintenances_urgentes WHERE status = 'confirmed' LIMIT 5")
        sample = cursor.fetchall()
        print(f"Sample of confirmed maintenances: {sample}")        # Count maintenances by status
        cursor.execute("SELECT status, COUNT(*) as count FROM maintenances_urgentes GROUP BY status")
        counts = cursor.fetchall()
        print(f"Maintenance counts by status: {counts}")
        
        query = '''
        SELECT 
            mu.id,
            mu.device_serial_number,
            mu.datetime,
            mu.status,
            mu.notes,
            mu.time_change_status,
            mu.requested_time,
            CONCAT(u.first_name, ' ', u.last_name) AS client_name,
            u.id AS user_id,
            DATE_FORMAT(mu.datetime, '%d/%m/%Y') AS formatted_date,
            DATE_FORMAT(mu.datetime, '%H:%i') AS formatted_time,
            DATE_FORMAT(mu.requested_time, '%d/%m/%Y') AS requested_date,
            DATE_FORMAT(mu.requested_time, '%H:%i') AS requested_time_formatted,
            DATE_FORMAT(mu.datetime, '%Y-%m-%d %H:%M:%S') AS datetime_str,
            DATE_FORMAT(mu.requested_time, '%Y-%m-%d %H:%M:%S') AS requested_time_str,
            d.model AS device_model,
            CONCAT(u.address_province, ', ', u.address_country) AS location
        FROM maintenances_urgentes mu
        JOIN devices d ON mu.device_serial_number = d.serial_number
        JOIN users u ON d.user_id = u.id
        WHERE mu.status = 'confirmed'
        ORDER BY mu.datetime ASC
        '''
        cursor.execute(query)
        maintenances = cursor.fetchall()
        
        print(f"Found {len(maintenances)} confirmed maintenance(s)")
        
        # Process the results to ensure all required fields are present
        result_maintenances = []
        for maintenance in maintenances:
            try:
                # Convert datetime objects to string if they're not already formatted
                if isinstance(maintenance['datetime'], datetime):
                    maintenance['formatted_date'] = maintenance['datetime'].strftime('%d/%m/%Y')
                    maintenance['formatted_time'] = maintenance['datetime'].strftime('%H:%M')
                    # Ensure we have a string version of datetime for JSON serialization
                    maintenance['datetime_str'] = maintenance['datetime'].strftime('%Y-%m-%d %H:%M:%S')
                
                # Format requested_time if it exists
                if maintenance.get('requested_time') and isinstance(maintenance['requested_time'], datetime):
                    maintenance['requested_date'] = maintenance['requested_time'].strftime('%d/%m/%Y')
                    maintenance['requested_time_formatted'] = maintenance['requested_time'].strftime('%H:%M')
                    maintenance['requested_time_str'] = maintenance['requested_time'].strftime('%Y-%m-%d %H:%M:%S')
                
                # Determine which datetime to use for display
                if maintenance.get('time_change_status') == 1 and maintenance.get('requested_time'):
                    # Use requested_time if time_change_status=1
                    maintenance['display_datetime'] = maintenance['requested_time_str'] if 'requested_time_str' in maintenance else str(maintenance.get('requested_time', ''))
                    maintenance['display_date'] = maintenance.get('requested_date', maintenance.get('formatted_date', ''))
                    maintenance['display_time'] = maintenance.get('requested_time_formatted', maintenance.get('formatted_time', ''))
                    maintenance['using_requested_time'] = True
                    print(f"Maintenance {maintenance['id']}: Using requested time {maintenance.get('requested_time')}")
                else:
                    # Use original datetime
                    maintenance['display_datetime'] = maintenance['datetime_str'] if 'datetime_str' in maintenance else str(maintenance.get('datetime', ''))
                    maintenance['display_date'] = maintenance.get('formatted_date', '')
                    maintenance['display_time'] = maintenance.get('formatted_time', '')
                    maintenance['using_requested_time'] = False
                    print(f"Maintenance {maintenance['id']}: Using original datetime {maintenance.get('datetime')}")
                
                # Ensure other required fields exist
                for field in ['client_name', 'device_model', 'location', 'notes']:
                    if not maintenance.get(field):
                        if field == 'client_name':
                            maintenance[field] = 'Client inconnu'
                        elif field == 'device_model':
                            maintenance[field] = 'Modèle inconnu'
                        elif field == 'location':
                            maintenance[field] = 'Localisation inconnue'
                        elif field == 'notes':
                            maintenance[field] = ''
                
                result_maintenances.append(maintenance)
                print(f"Successfully processed maintenance {maintenance['id']}")
            except Exception as e:
                print(f"Error processing maintenance {maintenance.get('id', 'unknown')}: {str(e)}")
        
        cursor.close()
        
        print(f"Returning {len(result_maintenances)} processed maintenance(s) to frontend")
        return jsonify({"success": True, "maintenances": result_maintenances})
            
    except Exception as e:
        print(f"Error fetching accepted maintenances: {str(e)}")
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500


@app.route('/api/users/create', methods=['POST'])
def create_user():
    print("Received user creation request") # Debug log
    try:
        data = request.get_json()
        print("Received data:", data) # Debug log
        
        # Validate required fields
        required_fields = ['email', 'phone_country_code', 'phone_number', 'address_country',
                         'address_province', 'address_detail', 'first_name', 'last_name',
                         'password_hash', 'role_id', 'status']
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            print(f"Missing fields: {missing_fields}") # Debug log
            return jsonify({'message': f'Missing required fields: {", ".join(missing_fields)}'}), 400
            
        # Create MySQL cursor
        try:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # DEBUG: Print available roles
            cur.execute('SELECT * FROM roles')
            available_roles = cur.fetchall()
            print("Available roles in database:", available_roles)
            
            # Check if email already exists
            cur.execute('SELECT * FROM users WHERE email = %s', (data['email'],))
            if cur.fetchone():
                cur.close()
                return jsonify({'message': 'Email already exists'}), 400

            # Map role_id from integer to UUID if needed
            data['role_id'] = map_role_id(data['role_id'])

            # Check if role_id exists
            cur.execute('SELECT id FROM roles WHERE id = %s', (data['role_id'],))
            if not cur.fetchone():
                cur.close()
                return jsonify({'message': f'Invalid role_id: {data["role_id"]}. Available roles: {available_roles}'}), 400

            # Generate current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
              # Get full country name from ISO code
            import requests
            headers = {
                'X-CSCAPI-KEY': 'QXJXRGZqd085dGRHYlVocmR2cFdrUlVpUnFOVkVMNm1adENlWmxEbw=='
            }
            
            try:
                # Get country name
                country_response = requests.get(f'https://api.countrystatecity.in/v1/countries/{data["address_country"]}', headers=headers)
                country_data = country_response.json()
                full_country_name = country_data.get('name', data['address_country'])                # Get state/province name
                state_response = requests.get(f'https://api.countrystatecity.in/v1/countries/{data["address_country"]}/states', headers=headers)
                states_data = state_response.json()
                print(f"Retrieved {len(states_data)} provinces for country {data['address_country']}")
                
                # Create a mapping of all possible identifiers to the full province name
                province_mapping = {}
                for state in states_data:
                    name = state.get('name')
                    if name:
                        # Map ID to name
                        province_mapping[str(state.get('id'))] = name
                        # Map name to name (case insensitive)
                        province_mapping[name.lower()] = name
                        # Map ISO2 code to name if available
                        if state.get('iso2'):
                            province_mapping[state.get('iso2').lower()] = name
                
                province_input = str(data['address_province']).strip().lower()
                full_province_name = None
                
                # First try direct lookup in our mapping
                if province_input in province_mapping:
                    full_province_name = province_mapping[province_input]
                    print(f"Found exact match: {data['address_province']} → {full_province_name}")
                else:
                    # If no exact match, try to find the most similar name
                    for state in states_data:
                        state_name = state.get('name', '')
                        if (province_input in state_name.lower() or 
                            state_name.lower() in province_input):
                            full_province_name = state_name
                            print(f"Found similar match: {data['address_province']} → {full_province_name}")
                            break
                
                # If still not found, keep original but log warning
                if not full_province_name:
                    full_province_name = data['address_province']
                    print(f"Warning: Could not find province match for '{data['address_province']}'. Using original value.")
                
                if full_province_name == data['address_province']:
                    print(f"Warning: Could not find exact province match for '{data['address_province']}'. Using original value.")
                
                print(f"Resolved province '{data['address_province']}' to '{full_province_name}'")
            except Exception as e:
                print(f"Error fetching country/state data: {e}")
                full_country_name = data['address_country']
                full_province_name = data['address_province']

            # Insert new user
            query = '''
            INSERT INTO users (
                email, phone_country_code, phone_number, address_country,
                address_province, address_detail, first_name, last_name,
                password_hash, role_id, status, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            values = (
                data['email'],
                data['phone_country_code'],
                data['phone_number'],
                full_country_name,  # Use full country name
                full_province_name,  # Use full province name
                data['address_detail'],
                data['first_name'],
                data['last_name'],
                data['password_hash'],
                data['role_id'],
                data.get('status', 'active'),
                current_time,
                current_time
            )
            print("Query values:", values) # Debug log
            
            print("Executing query with values:", values) # Debug log
            cur.execute(query, values)
            mysql.connection.commit()
            print("User created successfully") # Debug log
            
            return jsonify({'message': 'User created successfully'}), 201
            
        except MySQLdb.Error as err:
            print(f"Database error: {err}") # Debug log
            mysql.connection.rollback()
            return jsonify({'message': f'Database error occurred: {str(err)}'}), 500
        finally:
            cur.close()
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}") # Debug log
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/api/init/roles')
def init_roles():
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
          # Check existing roles
        cur.execute('SELECT * FROM roles')
        existing_roles = cur.fetchall()
        print("Existing roles:", existing_roles)
        
        # Define required roles with UUID strings
        required_roles = [
            ('013e5385-4fb1-11f0-b923-c43d1aabf058', 'superadmin'),
            ('013e2e4a-4fb1-11f0-b923-c43d1aabf058', 'user'),
            ('013e4af6-4fb1-11f0-b923-c43d1aabf058', 'sales')
        ]
        
        # Insert missing roles if needed
        for role_id, role_name in required_roles:
            cur.execute('INSERT IGNORE INTO roles (id, name) VALUES (%s, %s)', (role_id, role_name))
        
        mysql.connection.commit();
        
        # Get final roles
        cur.execute('SELECT * FROM roles')
        final_roles = cur.fetchall()
        cur.close();
        
        return jsonify({
            'message': 'Roles initialized successfully',
            'roles': final_roles
        })
        
    except Exception as e:
        print(f"Error initializing roles: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/roles')
def get_roles():
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM roles')
        roles = cur.fetchall()
        cur.close()
        return jsonify(roles)
    except Exception as e:
        print(f"Error fetching roles: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/roles/map')
def get_roles_map():
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT name, id FROM roles')
        roles = cur.fetchall()
        cur.close()
        # Create a map of role names to IDs
        role_map = {role['name']: role['id'] for role in roles}
        return jsonify(role_map)
    except Exception as e:
        print(f"Error fetching role map: {e}")
        return jsonify({'error': str(e)}), 500

def map_role_id(role_id):
    """Map integer role IDs to UUID strings"""
    role_map = {
        '1': '013e5385-4fb1-11f0-b923-c43d1aabf058',  # superadmin
        '2': '013e2e4a-4fb1-11f0-b923-c43d1aabf058',  # user
        '3': '013e4af6-4fb1-11f0-b923-c43d1abf058'   # sales
    }
    return role_map.get(role_id, role_id)  # Return mapped UUID or original if not found

@app.route('/api/users/all')
def get_all_users():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get total count for pagination
        cursor.execute('SELECT COUNT(*) as total FROM users')
        total_users = cursor.fetchone()['total']
        
        # Get users with pagination
        cursor.execute('''            SELECT 
                   u.id,
                   CONCAT('USR', LPAD(u.id, 3, '0')) as user_id,
                   CONCAT(u.first_name, ' ', u.last_name) as full_name,
                   'N/A' as dkit,
                   CONCAT(u.phone_country_code, ' ', u.phone_number) as phone,
                   CONCAT(u.address_province, ' - ', u.address_country) as region,
                   u.address_detail as address,
                   u.email,
                   u.password_hash,
                   u.status,
                   u.created_at as date,
                   u.updated_at as last_modified
            FROM users u
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s
        ''', (per_page, offset))
        
        users = cursor.fetchall()
        cursor.close()
        
        # Format dates
        for user in users:
            if user['date']:
                user['date'] = user['date'].strftime('%d/%m/%Y')
            if user['last_modified']:
                user['last_modified'] = user['last_modified'].strftime('%d/%m/%Y')
        
        return jsonify({
            'users': users,
            'total': total_users,
            'page': page,
            'total_pages': (total_users + per_page - 1) // per_page
        })
        
    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/maintenance/debug', methods=['GET'])
def get_maintenance_debug():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get all maintenance requests
        cursor.execute('''
        SELECT 
            mu.id,
            mu.device_serial_number,
            mu.status,
            mu.datetime,
            mu.notes,
            mu.technician_id,
            mu.time_change_status,
            mu.requested_time,
            mu.created_at
        FROM maintenances_urgentes mu
        ''')
        all_maintenances = cursor.fetchall()
        
        # Get all devices
        cursor.execute('''
        SELECT 
            d.id,
            d.serial_number,
            d.user_id,
            d.model,
            d.validated,
            d.status,
            d.purchase_date,
            d.warranty_end,
            d.last_maintenance,
            d.next_maintenance_date,
            d.location
        FROM devices d
        ''')
        all_devices = cursor.fetchall()
        
        # Get all users
        cursor.execute('''
        SELECT 
            u.id, 
            u.first_name,
            u.last_name,
            u.email,
            u.phone_country_code,
            u.phone_number,
            u.address_country,
            u.address_province,
            u.address_detail,
            r.name AS role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        ''')
        all_users = cursor.fetchall()
        
        # Get pending/scheduled maintenance requests with all joins
        cursor.execute('''
        SELECT 
            mu.id,
            mu.device_serial_number,
            mu.status,
            mu.datetime,
            mu.notes,
            d.model AS device_model,
            d.user_id,
            CONCAT(u.first_name, ' ', u.last_name) AS client_name,
            DATE_FORMAT(mu.datetime, '%d/%m/%Y') AS formatted_date,
            DATE_FORMAT(mu.datetime, '%H:%i') AS formatted_time
        FROM maintenances_urgentes mu
        JOIN devices d ON mu.device_serial_number = d.serial_number
        JOIN users u ON d.user_id = u.id
        WHERE mu.status = 'scheduled'
        ORDER BY mu.datetime ASC
        ''')
        pending_maintenances = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            "success": True, 
            "all_maintenances": all_maintenances,
            "all_devices": all_devices,
            "all_users": all_users,
            "pending_maintenances": pending_maintenances
        })
            
    except Exception as e:
        print(f"Error in maintenance diagnostic: {str(e)}")
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

# API endpoint to get all maintenance requests regardless of status
@app.route('/api/maintenance/all', methods=['GET'])
def get_all_maintenances():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        query = '''
        SELECT 
            mu.id,
            mu.device_serial_number,
            mu.datetime,
            mu.status,
            mu.notes,
            CONCAT(u.first_name, ' ', u.last_name) AS client_name,
            u.id AS user_id,
            DATE_FORMAT(mu.datetime, '%d/%m/%Y') AS formatted_date,
            DATE_FORMAT(mu.datetime, '%H:%i') AS formatted_time,
            d.model AS device_model,
            CONCAT(u.address_province, ', ', u.address_country) AS location
        FROM maintenances_urgentes mu
        JOIN devices d ON mu.device_serial_number = d.serial_number
        JOIN users u ON d.user_id = u.id
        ORDER BY mu.datetime ASC
        '''
        
        print("Executing query for ALL maintenance requests")
        cursor.execute(query)
        maintenances = cursor.fetchall()
        print(f"Found {len(maintenances)} maintenance requests in total")
        
        # Process the results to ensure all required fields are present
        for maintenance in maintenances:
            # Convert datetime object to string if it's not already formatted
            if isinstance(maintenance['datetime'], datetime):
                maintenance['formatted_date'] = maintenance['datetime'].strftime('%d/%m/%Y')
                maintenance['formatted_time'] = maintenance['datetime'].strftime('%H:%M')
            
            # Ensure location exists
            if not maintenance.get('location'):
                maintenance['location'] = 'Localisation inconnue'
                
        cursor.close()
        
        return jsonify({"success": True, "maintenances": maintenances})
            
    except Exception as e:
        print(f"Error fetching all maintenances: {str(e)}")
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

# Stock/Device Management API Endpoints
@app.route('/api/admin/devices', methods=['POST'])
def add_device_to_stock():
    """Add a new device to the stock table"""
    try:
        data = request.get_json()
        print("Received device data:", data)  # Debug log
        
        # Validate required fields
        if not data.get('model') or not data.get('serialNumber'):
            return jsonify({'success': False, 'message': 'Model and Serial Number are required'}), 400
        
        # Check if serial number already exists
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT id FROM stock WHERE serial_number = %s", (data['serialNumber'],))
        existing_device = cur.fetchone()
        
        if existing_device:
            cur.close()
            return jsonify({'success': False, 'message': 'Device with this serial number already exists'}), 400
        
        # Insert new device into stock table
        cur.execute("""
            INSERT INTO stock (serial_number, model, status) 
            VALUES (%s, %s, %s)
        """, (data['serialNumber'], data['model'], data.get('status', 'inactive')))
        
        mysql.connection.commit()
        device_id = cur.lastrowid
        cur.close()
        


        print(f"Device added successfully with ID: {device_id}")
        
        return jsonify({
            'success': True, 
            'message': 'Device added successfully',
            'device': {
                'id': device_id,
                'serial_number': data['serialNumber'],
                'model': data['model'],
                'status': data.get('status', 'inactive')
            }
        }), 201
        
    except Exception as e:
        print(f"Error adding device to stock: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/admin/devices/<int:device_id>', methods=['PUT'])
def update_device_in_stock(device_id):
    """Update an existing device in the stock table"""
    try:
        data = request.get_json()
        print(f"Updating device {device_id} with data:", data)
        
        # Validate required fields
        if not data.get('model') or not data.get('serial_number'):
            return jsonify({'success': False, 'message': 'Model and Serial Number are required'}), 400
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if device exists
        cur.execute("SELECT id FROM stock WHERE id = %s", (device_id,))
        existing_device = cur.fetchone()
        
        if not existing_device:
            cur.close()
            return jsonify({'success': False, 'message': 'Device not found'}), 404
        
        # Check if serial number is being changed and if it already exists elsewhere
        cur.execute("SELECT id FROM stock WHERE serial_number = %s AND id != %s", (data['serial_number'], device_id))
        duplicate_serial = cur.fetchone()
        
        if duplicate_serial:
            cur.close()
            return jsonify({'success': False, 'message': 'Device with this serial number already exists'}), 400
        
        # Update device in stock table (ID and creation_date are not modifiable)
        cur.execute("""
            UPDATE stock 
            SET serial_number = %s, model = %s, status = %s
            WHERE id = %s
        """, (data['serial_number'], data['model'], data.get('status', 'inactive'), device_id))
        
        mysql.connection.commit()
        cur.close()
        
        print(f"Device {device_id} updated successfully")
        
        return jsonify({
            'success': True, 
            'message': 'Device updated successfully',
            'device': {
                'id': device_id,
                'serial_number': data['serial_number'],
                'model': data['model'],
                'status': data.get('status', 'inactive')
            }
        }), 200
        
    except Exception as e:
        print(f"Error updating device in stock: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/init/database')
def init_database():
    """Initialize database tables including stock table"""
    try:
        cur = mysql.connection.cursor()
        
        print("Creating stock table...")
        # Create stock table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                id INT AUTO_INCREMENT PRIMARY KEY,
                serial_number VARCHAR(50) NOT NULL UNIQUE,
                model VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status ENUM('active', 'inactive') DEFAULT 'inactive'
            )
        """)
        
        print("Creating indexes...")
        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_serial_number ON stock(serial_number)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_status ON stock(status)")
        
        mysql.connection.commit()
        cur.close()
        
        print("Database tables initialized successfully!")
        
        return jsonify({
            'success': True,
            'message': 'Database tables initialized successfully'
        })
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Database initialization error: {str(e)}'
        }), 500

# Quick setup route for immediate database initialization
@app.route('/setup-database')
def setup_database():
    """Quick route to initialize the database and redirect back"""
    try:
        # Call the init_database function directly
        result = init_database()
        
        if result[0].get_json().get('success'):
            return """
            <html>
            <head><title>Database Setup</title></head>
            <body>
                <h2>✅ Database Setup Complete!</h2>
                <p>The database tables have been successfully created.</p>
                <p>You can now go back to your admin panel and try the device assignment functionality.</p>
                <a href="/admin/dkit-device-management">← Back to Device Management</a>
            </body>
            </html>
            """
        else:
            error_msg = result[0].get_json().get('message', 'Unknown error')
            return f"""
            <html>
            <head><title>Database Setup Error</title></head>
            <body>
                <h2>❌ Database Setup Failed</h2>
                <p>Error: {error_msg}</p>
                <a href="/admin/dkit-device-management">← Back to Device Management</a>
            </body>
            </html>
            """
    except Exception as e:
        return f"""
        <html>
        <head><title>Database Setup Error</title></head>
        <body>
            <h2>❌ Database Setup Failed</h2>
            <p>Error: {str(e)}</p>
            <a href="/admin/dkit-device-management">← Back to Device Management</a>
        </body>
        </html>
        """

@app.route('/api/admin/devices/<int:device_id>', methods=['GET'])
def get_device_by_id(device_id):
    """Get a specific device from the stock table by ID"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT id, serial_number, model, created_at, status 
            FROM stock 
            WHERE id = %s
        """, (device_id,))
        device = cur.fetchone()
        cur.close()
        
        if not device:
            return jsonify({'success': False, 'message': 'Device not found'}), 404
        
        # Format device data for frontend
        formatted_device = {
            'id': device['id'],
            'serial_number': device['serial_number'],
            'model': device['model'],
            'creation_date': device['created_at'].strftime('%Y-%m-%d') if device['created_at'] else '',
            'status': device['status']
        }
        
        return jsonify({'success': True, 'device': formatted_device}), 200
        
    except Exception as e:
        print(f"Error fetching device by ID: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

# Route pour supprimer un appareil par numéro de série
@app.route('/api/admin/devices/serial/<string:serial_number>', methods=['DELETE'])
def delete_device_by_serial(serial_number):
    """Delete a device from the stock table by serial number"""
    try:
        # Vérifier si l'appareil existe
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT id FROM stock WHERE serial_number = %s", (serial_number,))
        device = cur.fetchone()
        
        if not device:
            return jsonify({'success': False, 'message': f"Aucun appareil trouvé avec le numéro de série {serial_number}"}), 404
        
        # Supprimer l'appareil
        cur.execute("DELETE FROM stock WHERE serial_number = %s", (serial_number,))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': f"Appareil avec numéro de série {serial_number} supprimé avec succès"})
    
    except Exception as e:
        print(f"Erreur lors de la suppression de l'appareil: {e}")
        return jsonify({'success': False, 'message': f"Erreur lors de la suppression: {str(e)}"}), 500

@app.route('/api/admin/devices/check/<string:serial_number>', methods=['GET'])
def check_device_serial_number(serial_number):
    """Check if a device serial number exists in the stock table"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT id, serial_number, model, status 
            FROM stock 
            WHERE serial_number = %s
        """, (serial_number,))
        device = cur.fetchone()
        cur.close()
        
        if device:
            return jsonify({
                'success': True, 
                'exists': True, 
                'device': {
                    'id': device['id'],
                    'serial_number': device['serial_number'],
                    'model': device['model'],
                    'status': device['status']
                }
            }), 200
        else:
            return jsonify({'success': True, 'exists': False}), 200
        
    except Exception as e:
        print(f"Error checking device serial number: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/admin/users/search/<string:search_term>', methods=['GET'])
def search_user(search_term):
    """Search for users by name or email"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Recherche par nom, prénom ou email
        cur.execute("""
            SELECT id, first_name, last_name, email 
            FROM users 
            WHERE first_name LIKE %s OR last_name LIKE %s OR email LIKE %s
        """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        users = cur.fetchall()
        cur.close()
        
        if users:
            return jsonify({
                'success': True, 
                'exists': True, 
                'users': [{'id': user['id'], 
                          'name': f"{user['first_name']} {user['last_name']}", 
                          'email': user['email']} for user in users]
            }), 200
        else:
            return jsonify({'success': True, 'exists': False}), 200
        
    except Exception as e:
        print(f"Error searching user: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/admin/dkit-device-management')
def admin_dkit_device_management():
    """Admin D-KIT device management page with stock and assigned devices data"""
    try:
        # Fetch all devices from stock table for the main "Stock" table
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT id, serial_number, model, created_at, status
            FROM stock 
            ORDER BY created_at DESC
        """)
        stock_devices = cursor.fetchall()
        
        # Fetch all clients (users) for assignment
        cursor.execute("""
            SELECT id, first_name, last_name, email 
            FROM users 
            ORDER BY first_name, last_name
        """)
        clients = cursor.fetchall()
        
        print(f"Found {len(stock_devices)} devices in stock table")
        print(f"Found {len(clients)} clients")
        
        # Format stock devices for the template (main table)
        devices = []
        for device in stock_devices:
            # Ensure status is not None
            status = device['status'] if device['status'] else 'available'
            
            # Format dates properly
            try:
                formatted_date = device['created_at'].strftime('%d/%m/%Y') if device['created_at'] else ''
            except AttributeError:
                formatted_date = str(device['created_at']) if device['created_at'] else ''
            
            devices.append({
                'id': device['id'],
                'model': device['model'],
                'serialNumber': device['serial_number'],
                'status': status,
                'addedDate': formatted_date,
                'assignedClient': None,  # Stock devices are not assigned
                'assignedClientId': None,
                'assignmentDate': None,
                'warrantyEndDate': None,
                'location': 'Stock'
            })
        
        # Format clients for the template
        formatted_clients = []
        for client in clients:
            formatted_clients.append({
                'id': client['id'],
                'name': f"{client['first_name']} {client['last_name']}",
                'email': client['email']
            })
        
        cursor.close()
        return render_template('admin_DKITDeviceManagement.html', devices=devices, clients=formatted_clients)
        
    except Exception as e:
        print(f"Error loading devices from devices table: {str(e)}")
        # Fallback to template without devices data
        return render_template('admin_DKITDeviceManagement.html', devices=[], clients=[])

@app.route('/api/admin/devices', methods=['GET'])
def get_devices():
    """Get devices from the devices table with optional filtering"""
    try:
        # Get filter parameters
        show_available_only = request.args.get('available_only', 'false').lower() == 'true'
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if show_available_only:
            # Get devices from stock table for assignment purposes
            cursor.execute("""
                SELECT id, serial_number, model, created_at, status 
                FROM stock 
                WHERE status = 'active' OR status = 'inactive'
                ORDER BY created_at DESC
            """)
        else:
            # Get all devices for general management
            cursor.execute("""
                SELECT id, serial_number, model, purchase_date as created_at, status, user_id,
                       location, warranty_end
                FROM devices 
                ORDER BY purchase_date DESC
            """)
        
        devices = cursor.fetchall()
        cursor.close()
        
        # Format devices for frontend
        formatted_devices = []
        for device in devices:
            device_data = {
                'id': device['id'],
                'serial_number': device['serial_number'],
                'model': device['model'],
                'creation_date': device['created_at'].strftime('%d/%m/%Y') if device['created_at'] else '',
                'status': device['status'] if device['status'] else 'inactive'
            }
            
            # Add assignment info if not filtering for available only
            if not show_available_only:
                device_data.update({
                    'assigned': device['user_id'] is not None,
                    'location': device.get('location', ''),
                    'warranty_end': device['warranty_end'].strftime('%d/%m/%Y') if device.get('warranty_end') else ''
                })
            
            formatted_devices.append(device_data)
        
        return jsonify({'success': True, 'devices': formatted_devices}), 200
        
    except Exception as e:
        print(f"Error fetching devices: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/admin/stock/add', methods=['POST'])
def add_stock_device():
    """Add a new device to stock"""
    try:
        data = request.get_json()
        serial_number = data.get('serial_number', '').strip()
        model = data.get('model', '').strip()
        status = data.get('status', 'inactive')
        
        if not serial_number or not model:
            return jsonify({'success': False, 'message': 'Numéro de série et modèle requis'}), 400
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if serial number already exists
        cursor.execute("SELECT id FROM stock WHERE serial_number = %s", (serial_number,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'success': False, 'message': 'Ce numéro de série existe déjà'}), 400
        
        # Insert new device
        cursor.execute(
            "INSERT INTO stock (serial_number, model, status) VALUES (%s, %s, %s)",
            (serial_number, model, status)
        )
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'D-KIT ajouté au stock avec succès'}), 201
        
    except Exception as e:
        print(f"Error adding device to stock: {str(e)}")
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/api/admin/stock/<int:device_id>', methods=['GET'])
def get_stock_device(device_id):
    """Get a specific device from stock"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT id, serial_number, model, status, created_at 
            FROM stock 
            WHERE id = %s
        """, (device_id,))
        device = cursor.fetchone()
        cursor.close()
        
        if device:
            # Format device data
            formatted_device = {
                'id': device['id'],
                'serial_number': device['serial_number'],
                'model': device['model'],
                'status': device['status'],
                'creation_date': device['created_at'].strftime('%d/%m/%Y') if device['created_at'] else ''
            }
            return jsonify({'success': True, 'device': formatted_device}), 200
        else:
            return jsonify({'success': False, 'message': 'Device not found'}), 404
        
    except Exception as e:
        print(f"Error fetching stock device: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/admin/stock/<int:device_id>', methods=['PUT'])
def update_stock_device(device_id):
    """Update a device in stock"""
    try:
        data = request.get_json()
        serial_number = data.get('serial_number', '').strip()
        model = data.get('model', '').strip()
        status = data.get('status', 'inactive')
        
        if not serial_number or not model:
            return jsonify({'success': False, 'message': 'Numéro de série et modèle requis'}), 400
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if device exists
        cursor.execute("SELECT id FROM stock WHERE id = %s", (device_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'success': False, 'message': 'Dispositif introuvable'}), 404
        
        # Check if serial number is used by another device
        cursor.execute("SELECT id FROM stock WHERE serial_number = %s AND id != %s", (serial_number, device_id))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'success': False, 'message': 'Ce numéro de série est déjà utilisé'}), 400
        
        # Update device
        cursor.execute(
            "UPDATE stock SET serial_number = %s, model = %s, status = %s WHERE id = %s",
            (serial_number, model, status, device_id)
        )
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'D-KIT mis à jour avec succès'}), 200
        
    except Exception as e:
        print(f"Error updating device in stock: {str(e)}")
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/api/admin/stock/<int:device_id>', methods=['DELETE'])
def delete_stock_device(device_id):
    """Delete a device from stock"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if device exists
        cursor.execute("SELECT id FROM stock WHERE id = %s", (device_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'success': False, 'message': 'Dispositif introuvable'}), 404
        
        # Delete device
        cursor.execute("DELETE FROM stock WHERE id = %s", (device_id,))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'D-KIT supprimé du stock avec succès'}), 200
        
    except Exception as e:
        print(f"Error deleting device from stock: {str(e)}")
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/api/admin/stock/search', methods=['GET'])
def search_stock_devices():
    """Search devices in stock by serial number or model"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if not search_term:
            return jsonify({'success': False, 'message': 'Terme de recherche requis'}), 400
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT id, serial_number, model, created_at, status 
            FROM stock 
            WHERE serial_number LIKE %s OR model LIKE %s
            ORDER BY created_at DESC
        """, (f'%{search_term}%', f'%{search_term}%'))
        
        devices = cursor.fetchall()
        cursor.close()
        
        # Format devices for frontend
        formatted_devices = []
        for device in devices:
            formatted_devices.append({
                'id': device['id'],
                'serial_number': device['serial_number'],
                'model': device['model'],
                'creation_date': device['created_at'].strftime('%d/%m/%Y') if device['created_at'] else '',
                'status': device['status'] if device['status'] else 'inactive'
            })
        
        return jsonify({'success': True, 'devices': formatted_devices}), 200
        
    except Exception as e:
        print(f"Error searching stock devices: {str(e)}")
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

# Device Assignment API Endpoints
@app.route('/api/admin/devices/available', methods=['GET'])
def get_available_devices():
    """Get all available devices from stock table for assignment"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT id, serial_number, model, status, created_at 
            FROM stock 
            ORDER BY created_at DESC
        """)
        devices = cur.fetchall()
        cur.close()
        
        # Format devices for frontend
        formatted_devices = []
        for device in devices:
            formatted_devices.append({
                'id': device['id'],
                'serial_number': device['serial_number'],
                'model': device['model'],
                'status': device['status'] if device['status'] else 'available',
                'creation_date': device['created_at'].strftime('%d/%m/%Y') if device['created_at'] else ''
            })
        
        return jsonify({'success': True, 'devices': formatted_devices}), 200
        
    except Exception as e:
        print(f"Error fetching available devices: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/admin/clients', methods=['GET'])
def get_all_clients():
    """Get all users that can be assigned devices"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT id, first_name, last_name, email 
            FROM users 
            ORDER BY first_name, last_name
        """)
        users = cur.fetchall()
        cur.close()
        
        # Format users for frontend
        formatted_users = []
        for user in users:
            formatted_users.append({
                'id': user['id'],
                'name': f"{user['first_name']} {user['last_name']}",
                'email': user['email']
            })
        
        return jsonify({'success': True, 'clients': formatted_users}), 200
        
    except Exception as e:
        print(f"Error fetching clients: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/admin/devices/assigned', methods=['GET'])
def get_assigned_devices():
    """Get all devices assigned to clients from the devices table"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get assigned devices directly from devices table where user_id is not null
        cur.execute("""
            SELECT 
                d.id as device_id,
                d.user_id as client_id,
                d.serial_number,
                d.model,
                d.purchase_date as assignment_date,
                d.warranty_end as warranty_end_date,
                d.location,
                d.status,
                d.validated,
                CONCAT(u.first_name, ' ', u.last_name) as client_name,
                u.email as client_email
            FROM devices d
            JOIN users u ON d.user_id = u.id
            WHERE d.user_id IS NOT NULL
            ORDER BY d.purchase_date DESC
        """)
        assigned_devices = cur.fetchall()
        cur.close()
        
        # Format the data for frontend
        formatted_devices = []
        for device in assigned_devices:
            formatted_devices.append({
                'device_id': device['device_id'],
                'client_id': device['client_id'],
                'serial_number': device['serial_number'],
                'model': device['model'],
                'client_name': device['client_name'],
                'client_email': device['client_email'],
                'assignment_date': device['assignment_date'].isoformat() if device['assignment_date'] else None,
                'warranty_end_date': device['warranty_end_date'].isoformat() if device['warranty_end_date'] else None,
                'location': device['location'] if device['location'] else '',
                'status': device['status'],
                'validated': device['validated']
            })
        
        return jsonify({
            'success': True,
            'devices': formatted_devices
        })
        
    except Exception as e:
        print(f"Error fetching assigned devices: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Database error: {str(e)}',
            'devices': []
        }), 500

@app.route('/api/admin/devices/<int:device_id>/assign', methods=['POST'])
def assign_device_to_client(device_id):
    """Assign a device to a client by moving it from stock to devices table"""
    try:
        data = request.get_json()
        client_id = data.get('clientId')
        assignment_date = data.get('assignmentDate')
        warranty_end_date = data.get('warrantyEndDate')
        location = data.get('location', '')
        
        if not client_id:
            return jsonify({'success': False, 'message': 'Client ID is required'}), 400
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if device exists in stock table
        cur.execute("SELECT id, serial_number, model FROM stock WHERE id = %s", (device_id,))
        stock_device = cur.fetchone()
        if not stock_device:
            cur.close()
            return jsonify({'success': False, 'message': 'Device not found in stock'}), 404
        
        # Check if client exists
        cur.execute("SELECT id, first_name, last_name FROM users WHERE id = %s", (client_id,))
        client = cur.fetchone()
        if not client:
            cur.close()
            return jsonify({'success': False, 'message': 'Client not found'}), 404
        
        # Parse dates if provided
        assignment_dt = None
        warranty_end_dt = None
        
        if assignment_date:
            try:
                assignment_dt = datetime.fromisoformat(assignment_date.replace('Z', '+00:00'))
            except:
                assignment_dt = datetime.now()
        else:
            assignment_dt = datetime.now()
            
        # Set warranty to 1 year from assignment date for all devices
        warranty_end_dt = assignment_dt + timedelta(days=365)
        
        # Insert device into devices table
        cur.execute("""
            INSERT INTO devices (serial_number, user_id, model, purchase_date, warranty_end, location, status, validated)
            VALUES (%s, %s, %s, %s, %s, %s, 'active', 0)
        """, (stock_device['serial_number'], client_id, stock_device['model'], assignment_dt, warranty_end_dt, location))
        
        # Delete device from stock table
        cur.execute("DELETE FROM stock WHERE id = %s", (device_id,))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            'success': True,
            'message': f'Device {stock_device["serial_number"]} assigned to {client["first_name"]} {client["last_name"]} successfully and moved to devices table'
        })
        
    except Exception as e:
        print(f"Error assigning device: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/admin/devices/<int:device_id>/unassign', methods=['POST'])
def unassign_device_from_client(device_id):
    """Unassign a device from a client by updating the devices table"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if device is assigned
        cur.execute("""
            SELECT d.id, d.serial_number, d.user_id, CONCAT(u.first_name, ' ', u.last_name) as client_name
            FROM devices d
            LEFT JOIN users u ON d.user_id = u.id
            WHERE d.id = %s
        """, (device_id,))
        device = cur.fetchone()
        
        if not device:
            cur.close()
            return jsonify({'success': False, 'message': 'Device not found'}), 404
        
        if device['user_id'] is None:
            cur.close()
            return jsonify({'success': False, 'message': 'Device is not currently assigned'}), 404
        
        # Update devices table to unassign the device
        cur.execute("""
            UPDATE devices 
            SET user_id = NULL, 
                location = NULL, 
                status = 'inactive'
            WHERE id = %s
        """, (device_id,))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            'success': True,
            'message': f'Device {device["serial_number"]} unassigned from {device["client_name"]} successfully'
        })
        
    except Exception as e:
        print(f"Error unassigning device: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/admin/devices/<int:device_id>/assignment', methods=['GET'])
def get_device_assignment(device_id):
    """Get assignment details for a specific device from the devices table"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT 
                d.id as device_id,
                d.user_id as client_id,
                d.purchase_date as assignment_date,
                d.warranty_end as warranty_end_date,
                d.location,
                d.status,
                d.serial_number,
                d.model,
                CONCAT(u.first_name, ' ', u.last_name) as client_name,
                u.email as client_email
            FROM devices d
            LEFT JOIN users u ON d.user_id = u.id
            WHERE d.id = %s
        """, (device_id,))
        device = cur.fetchone()
        cur.close()
        
        if not device:
            return jsonify({'success': False, 'message': 'Device not found'}), 404
        
        if device['user_id'] is None:
            return jsonify({'success': False, 'message': 'Device is not assigned to any client'}), 404
        
        # Format the data for frontend
        formatted_assignment = {
            'device_id': device['device_id'],
            'client_id': device['client_id'],
            'serial_number': device['serial_number'],
            'model': device['model'],
            'client_name': device['client_name'],
            'client_email': device['client_email'],
            'assignment_date': device['assignment_date'].isoformat() if device['assignment_date'] else None,
            'warranty_end_date': device['warranty_end_date'].isoformat() if device['warranty_end_date'] else None,
            'location': device['location'] if device['location'] else '',
            'status': device['status']
        }
        
        return jsonify({
            'success': True,
            'device': formatted_assignment
        })
        
    except Exception as e:
        print(f"Error fetching device assignment: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/admin/devices/<int:device_id>/assignment', methods=['PUT'])
def update_device_assignment(device_id):
    """Update assignment details for a specific device in the devices table"""
    try:
        data = request.get_json()
        client_id = data.get('clientId')
        location = data.get('location', '')
        status = data.get('status', 'active')
        warranty_end_date = data.get('warrantyEndDate')
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if device exists and is assigned
        cur.execute("SELECT id, user_id FROM devices WHERE id = %s", (device_id,))
        device = cur.fetchone()
        if not device:
            cur.close()
            return jsonify({'success': False, 'message': 'Device not found'}), 404
            
        if device['user_id'] is None:
            cur.close()
            return jsonify({'success': False, 'message': 'Device is not assigned to any client'}), 404
        
        # Parse warranty end date if provided
        warranty_end_dt = None
        if warranty_end_date:
            try:
                warranty_end_dt = datetime.fromisoformat(warranty_end_date.replace('Z', '+00:00'))
            except:
                pass
        
        # Update device assignment in devices table
        update_fields = []
        update_values = []
        
        if client_id:
            update_fields.append("user_id = %s")
            update_values.append(client_id)
        
        if location is not None:
            update_fields.append("location = %s")
            update_values.append(location)
        
        if status:
            update_fields.append("status = %s")
            update_values.append(status)
        
        if warranty_end_dt:
            update_fields.append("warranty_end = %s")
            update_values.append(warranty_end_dt)
        
        if update_fields:
            update_values.append(device_id)
            query = f"UPDATE devices SET {', '.join(update_fields)} WHERE id = %s"
            cur.execute(query, update_values)
            mysql.connection.commit()
        
        cur.close()
        
        return jsonify({
            'success': True,
            'message': 'Device assignment updated successfully'
        })
        
    except Exception as e:
        print(f"Error updating device assignment: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/admin/devices/<int:device_id>/validate', methods=['POST'])
def validate_device(device_id):
    """Validate/Accept a device by setting validated = 1"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if device exists and is assigned
        cur.execute("""
            SELECT d.id, d.serial_number, d.user_id, d.validated,
                   CONCAT(u.first_name, ' ', u.last_name) as client_name
            FROM devices d
            LEFT JOIN users u ON d.user_id = u.id
            WHERE d.id = %s
        """, (device_id,))
        device = cur.fetchone()
        
        if not device:
            cur.close()
            return jsonify({'success': False, 'message': 'Device not found'}), 404
        
        if device['user_id'] is None:
            cur.close()
            return jsonify({'success': False, 'message': 'Device is not assigned to any client'}), 400
        
        if device['validated'] == 1:
            cur.close()
            return jsonify({'success': False, 'message': 'Device is already validated'}), 400
        
        # Update device to set validated = 1
        cur.execute("""
            UPDATE devices 
            SET validated = 1
            WHERE id = %s
        """, (device_id,))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            'success': True,
            'message': f'Device {device["serial_number"]} has been validated successfully'
        })
        
    except Exception as e:
        print(f"Error validating device: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

# Main execution block to run the app on localhost
if __name__ == '__main__':
    # Set debug=True for development to enable auto-reload and detailed error messages
    # Set host='0.0.0.0' to make the server publicly available on your local network
    # Default port is 5000, but you can change it if needed
    print("Starting the DWEE application server...")
    print("Access the application at: http://localhost:5000")
    app.run(host='localhost', port=5000, debug=True)

