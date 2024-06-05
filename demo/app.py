from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User, Itinerary, Log, Recommendation
from utils import find_team, recommend_itinerary
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///traveller_assistant.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']
        gender = request.form['gender']
        location = request.form['location']
        budget = request.form['budget']
        interests = request.form['interests']
        companion_requirements = request.form['companion_requirements']

        new_user = User(username=username, password=password, age=age, gender=gender, location=location,
                        budget=budget, interests=interests, companion_requirements=companion_requirements)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('profile'))
    return render_template('login.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = User.query.filter_by(id=session['user_id']).first()
    if request.method == 'POST':
        user.location = request.form['location']
        user.budget = request.form['budget']
        user.interests = request.form['interests']
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

@app.route('/itinerary', methods=['GET', 'POST'])
def itinerary():
    if request.method == 'POST':
        destination = request.form['destination']
        time = request.form['time']
        price = request.form['price']
        companion_requirements = request.form['companion_requirements']
        
        new_itinerary = Itinerary(user_id=session['user_id'], destination=destination, time=time,
                                  price=price, companion_requirements=companion_requirements)
        db.session.add(new_itinerary)
        db.session.commit()
        return redirect(url_for('recommendations'))
    return render_template('itinerary.html')

@app.route('/recommendations')
def recommendations():
    user = User.query.filter_by(id=session['user_id']).first()
    recommendations = find_team(user)
    return render_template('recommendations.html', recommendations=recommendations)

@app.route('/log', methods=['GET', 'POST'])
def log():
    if request.method == 'POST':
        content = request.form['content']
        new_log = Log(user_id=session['user_id'], content=content)
        db.session.add(new_log)
        db.session.commit()
        return redirect(url_for('log'))
    user_logs = Log.query.filter_by(user_id=session['user_id']).all()
    return render_template('log.html', logs=user_logs)

@app.route('/routes')
def routes():
    # This would contain logic for interacting with map APIs to display routes
    return "Routes feature coming soon!"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
