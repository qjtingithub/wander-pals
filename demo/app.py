from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User, Itinerary, Log, Recommendation, Team, Invitation
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
            session['recommendation_index'] = 0  # Initialize recommendation index
            return redirect(url_for('profile'))
    return render_template('login.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.filter_by(id=user_id).first()
        if request.method == 'POST':
            user.location = request.form['location']
            user.budget = request.form['budget']
            user.interests = request.form['interests']
            db.session.commit()
            return redirect(url_for('profile'))
        return render_template('profile.html', user=user)
    else:
        # 如果用户未登录，则重定向到登录页面
        return redirect(url_for('login'))

@app.route('/create_itinerary', methods=['GET', 'POST'])
def create_itinerary():
    if request.method == 'POST':
        destination = request.form['destination']
        time = request.form['time']
        price = request.form['price']
        companion_requirements = request.form['companion_requirements']
        
        new_itinerary = Itinerary(user_id=session['user_id'], destination=destination, time=time,
                                  price=price, companion_requirements=companion_requirements)
        db.session.add(new_itinerary)
        db.session.commit()

        return redirect(url_for('recommendations'))  # Redirect to recommendations
    return render_template('create_itinerary.html')

@app.route('/create_team', methods=['GET', 'POST'])
def create_team():
    if request.method == 'POST':
        create_team = request.form.get('create_team')
        if create_team == 'yes':
            return redirect(url_for('recommendations'))
        else:
            return redirect(url_for('profile'))
    return render_template('create_team.html')

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    user = User.query.filter_by(id=session['user_id']).first()
    recommendations = find_team(user)
    current_recommendation = None
    score = 0

    if recommendations:
        current_recommendation, score = recommendations[0]

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'next':
            recommendations.pop(0)  # 删除当前推荐的用户
            if recommendations:
                current_recommendation, score = recommendations[0]
            else:
                current_recommendation = None
        elif action == 'invite':
            if current_recommendation:
                invite_user(current_recommendation.id)  # 使用 current_recommendation 获取用户对象
            # 处理邀请逻辑
            pass

    return render_template('recommendations.html', recommendation=current_recommendation, score=score)

@app.route('/exit_team_creation', methods=['POST'])
def exit_team_creation():
    return redirect(url_for('profile'))

@app.route('/recommend_teams', methods=['GET', 'POST'])
def recommend_teams():
    user = User.query.filter_by(id=session['user_id']).first()
    itinerary = Itinerary.query.filter_by(user_id=user.id).first()
    
    if not itinerary:
        return redirect(url_for('create_itinerary'))
    
    recommended_teams = find_teams(itinerary)
    
    if 'team_index' not in session:
        session['team_index'] = 0
    
    index = session['team_index']
    
    if index >= len(recommended_teams):
        return "No more teams available."
    
    team = recommended_teams[index]
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'next':
            session['team_index'] += 1
            return redirect(url_for('recommend_teams'))
        elif action == 'request_join':
            # 请求加入团队逻辑
            request_join_team(team)
            session['team_index'] += 1
            return redirect(url_for('recommend_teams'))
    
    return render_template('recommend_teams.html', team=team)

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

@app.route('/send_invitation/<int:user_id>', methods=['POST'])
def send_invitation(user_id):
    sender_id = session['user_id']
    invitation = Invitation(sender_id=sender_id, receiver_id=user_id, status='pending')
    db.session.add(invitation)
    db.session.commit()
    return redirect(url_for('recommendations'))

@app.route('/invitations')
def invitations():
    user_id = session['user_id']
    received_invitations = Invitation.query.filter_by(receiver_id=user_id).all()
    sent_invitations = Invitation.query.filter_by(sender_id=user_id).all()
    return render_template('invitations.html', received_invitations=received_invitations, sent_invitations=sent_invitations)

@app.route('/respond_invitation/<int:invitation_id>/<string:response>', methods=['POST'])
def respond_invitation(invitation_id, response):
    invitation = Invitation.query.get(invitation_id)
    if invitation and invitation.receiver_id == session['user_id']:
        invitation.status = response
        db.session.commit()
    return redirect(url_for('invitations'))

def invite_user(user_id):
    sender_id = session['user_id']
    invitation = Invitation(sender_id=sender_id, receiver_id=user_id, status='pending')
    db.session.add(invitation)
    db.session.commit()

def find_teams(itinerary):
    # 推荐团队的逻辑
    return []

def request_join_team(team):
    # 请求加入团队的逻辑
    pass

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('recommendation_index', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
