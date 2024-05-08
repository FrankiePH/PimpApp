from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from forms import LoginForm, RegisterForm
from models import User, db
import logging
# Create LoginManager instance
login_manager = LoginManager()

songQue = []

def clear_database():
    # Delete all records from the User table
    db.session.query(User).delete()
    # Delete all records from other tables if needed
    # db.session.query(OtherModel).delete()

def create_app():
    # Create the Flask application instance
    app = Flask(__name__)

    # Configure the application
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        #clear_database()
        db.create_all()

    return app

app = create_app()


# Create the database tables based on the models



@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if username == "Kanye West":
            flash("You lottle goofball")
            
        if user and user.check_password(password):
            login_user(user, force=True)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html', form=form)


@app.errorhandler(403)
def log_forbidden_error(e):
    app.logger.error(f"Forbidden access attempted by {request.remote_addr}")
    return "<h1>403 Error</h1><p>You do not have permission to access this resource.</p>", 403

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    all_users = User.query.all()
    print(all_users)
    
    # get a dict of user names and emails
    user_dict = {}
    for user in all_users:
        user_dict[user.username] = user.email

    # get the current users data in a dict
    current_user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'balance': current_user.balance
    }
    
    if current_user.is_admin:
        return render_template('dashboard.html', user=current_user, users=user_dict, admin=current_user.is_admin, current_user_data=current_user_data)
    else:
        return render_template('dashboard.html', user=current_user, current_user_data=current_user_data)

@login_manager.user_loader
def load_user(user_id):
    # Load the user from the database based on the user ID
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if username or email already exists in the database
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            # delete user
            db.session.delete(existing_user)
            db.session.commit()
            #flash('Username or email already exists.', 'error')
            #return redirect(url_for('register'))

        # Create a new user instance
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/submit_song', methods=['GET', 'POST'])
def submit_song():
    if request.method == 'POST':
        # get request json
        song = request.json
        songQue.append(song)
        print(f"Song: {song}")
    # go back to bashboard
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)