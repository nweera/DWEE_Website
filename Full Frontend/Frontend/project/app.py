from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import uuid
import datetime
import MySQLdb.cursors
import secrets  # For generating secure tokens
from datetime import datetime, timedelta
from flask_login import LoginManager, current_user, login_required

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration - Updated for standalone MySQL
app.config['MYSQL_HOST'] = 'localhost'
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
                    
                    # Check if email exists
                    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
                    user = cursor.fetchone()
                    
                    if not user:
                        flash('Email not registered', 'error')
                    else:
                        # Check password
                        cursor.execute('SELECT * FROM users WHERE email = %s AND password_hash = %s', (email, password))
                        user = cursor.fetchone()
                        
                        if user:
                            session['loggedin'] = True
                            session['id'] = user['id']
                            session['email'] = user['email']
                            session['role_id'] = user['role_id']
                            session['first_name'] = user['first_name']
                            session['last_name'] = user['last_name']

                            # Check user role and redirect accordingly
                            # Fetch role name from roles table
                            cursor.execute("SELECT name FROM roles WHERE id = %s", (user['role_id'],))
                            role = cursor.fetchone()
                            if role and role['name'] == 'superadmin':
                                return redirect(url_for('superadmin_dashboard'))
                            elif role and role['name'] == 'sales':
                                return redirect(url_for('sales_rep_dashboard'))
                            else:
                                return redirect(url_for('user_dashboard'))
                        else:
                            flash('Incorrect email or password!', 'error')
                    
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
    # Fetch only confirmed appointments for dashboard
    cursor.execute("""
        SELECT a.*, d.serial_number 
        FROM appointments a
        JOIN devices d ON a.device_id = d.id
        WHERE a.user_id = %s
    """, (user_id,))
    appointments = cursor.fetchall()
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
        return render_template('user_dkits.html', user=user, devices=devices)
    else:
        return redirect(url_for('login_signup'))

@app.route('/user_calendar')
def user_calendar():
    if 'id' not in session:
        return redirect(url_for('login_signup'))
    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Fetch user info
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    # Fetch validated devices
    cursor.execute("SELECT * FROM devices WHERE user_id = %s AND validated = 1", (user_id,))
    validated_devices = cursor.fetchall()
    # Fetch appointments
    cursor.execute("""
        SELECT a.*, d.serial_number 
        FROM appointments a
        JOIN devices d ON a.device_id = d.id
        WHERE a.user_id = %s
    """, (user_id,))
    appointments = cursor.fetchall()
    cursor.close()
    return render_template('user_calendar.html', user=user, validated_devices=validated_devices, appointments=appointments)

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
        raison_sociale = request.form.get('raisonSociale', '').strip()
        matricule_fiscale = request.form.get('matriculeFiscale', '').strip()
        secteur_activite = request.form.get('secteurActivite', '').strip()
        motivation = request.form.get('motivation', '').strip()
        user_id = session['id']

        if secteur_activite == 'autre':
            secteur_activite = request.form.get('autreSecteur', '').strip()

        if not raison_sociale or not matricule_fiscale or not secteur_activite:
            flash("Tous les champs obligatoires doivent être remplis.", "error")
            return render_template('user_commercial-registration.html', dashboard_url=dashboard_url)

        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("""
                INSERT INTO commercial_registrations
                (user_id, raison_sociale, matricule_fiscale, secteur_activite, motivation)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, raison_sociale, matricule_fiscale, secteur_activite, motivation))
            mysql.connection.commit()
            cursor.close()
            flash("Votre demande d'inscription a été envoyée avec succès.", "success")
            return redirect(url_for('user_commercial_registration'))
        except Exception as e:
            flash(f"Erreur lors de l'envoi de la demande : {str(e)}", "error")
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
                    "INSERT INTO devices (user_id, serial_number, model, purchase_date, location, status, validated) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (session['id'], serial_number, model, purchase_date, location, status, 0)
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

    try:
        cursor.execute(
            "INSERT INTO appointments (user_id, device_id, datetime, type, status, notes) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, device['id'], datetime_str, 'urgent', 'scheduled', notes)
        )
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

#############################################################
#SALES DASHBOARD ROUTES
#############################################################

@app.route('/sales_rep_dashboard')
def sales_rep_dashboard():
    if 'loggedin' in session:
        # Sales rep dashboard logic
        return render_template('sales_rep_dashboard.html')
    else:
        return redirect(url_for('login_signup'))



#############################################################
#ADMIN DASHBOARD ROUTES 
#############################################################


@app.route('/radmin_dashboard')
def superadmin_dashboard():
    if 'loggedin' in session and session.get('role_id'):
        # Optionally, check if the role is actually superadmin here
        return render_template('admin_dashboard.html')
    else:
        return redirect(url_for('login_signup'))


@app.route('/admin/users')
def admin_user_management():
    return render_template('admin_userManagement.html')

@app.route('/admin/sales-representative')
def admin_sales_representative():
    return render_template('admin_salesRepresentative.html')

@app.route('/admin/appointments')
def admin_appointment():
    return render_template('admin_appointment.html')

@app.route('/admin/devices')
def admin_dkit_device_management():
    return render_template('admin_DKITDeviceManagement.html')

@app.route('/admin/reports')
def admin_reports_analytics():
    return render_template('admin_ReportsAnalytics.html')

@app.route('/admin/system')
def admin_system_configuration():
    return render_template('admin_SystemConfiguration.html')

@app.route('/admin/audit')
def admin_audit_logs():
    return render_template('admin_AuditLogs.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    # your dashboard logic
    return render_template('admin_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
