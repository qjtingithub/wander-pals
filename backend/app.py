from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
from models import db, User, Itinerary, Log, Recommendation, Team, Invitation
from utils import find_team, recommend_itinerary
from flask_sqlalchemy import SQLAlchemy
import os
import requests

# 前端路径配置
app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")

# 数据库路径配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/traveller_assistant.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form['user_id']
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']
        gender = request.form['gender']
        location = request.form['location']
        budget = request.form['budget']
        interests = request.form['interests']
        companion_requirements = request.form['companion_requirements']

        existing_user = User.query.get(user_id)
        if existing_user:
            flash('用户ID已存在，请选择其他用户ID。')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在，请选择其他用户名。')
            return redirect(url_for('register'))

        new_user = User(id=user_id, username=username, password=password, age=age, gender=gender, location=location,
                        budget=budget, interests=interests, companion_requirements=companion_requirements)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        
        user = User.query.filter_by(id=user_id, password=password).first()
        if user:
            session['user_id'] = user.id  # 在 session 中存储用户 ID
            return redirect(url_for('profile'))
        else:
            flash('无效的用户ID或密码')
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

@app.route('/create_team', methods=['GET', 'POST'])
def create_team():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    if request.method == 'POST':
        team_name = request.form['team_name']
        destination = request.form['destination']
        time = request.form['time']
        price = request.form['price']
        companion_requirements = request.form['companion_requirements']

        new_team = Team(name=team_name, destination=destination, time=time,
                        price=price, companion_requirements=companion_requirements, creator_id=user_id)
        db.session.add(new_team)
        db.session.commit()

        # 将创建者添加为团队成员
        user = User.query.get(user_id)
        new_team.members.append(user)
        db.session.commit()

        flash('团队创建成功！')
        return redirect(url_for('team_invitation', team_id=new_team.id))

    return render_template('create_team.html')

@app.route('/team_invitation/<int:team_id>')
def team_invitation(team_id):
    team = Team.query.get_or_404(team_id)
    current_user_id = session.get('user_id')
    users = User.query.filter(User.id != current_user_id).all()
    return render_template('team_invitation.html', team_id=team.id, users=users)

@app.route('/send_invitations', methods=['POST'])
def send_invitations():
    team_id = request.form['team_id']
    user_id = request.form['user_id']

    team = Team.query.get_or_404(team_id)
    user = User.query.get_or_404(user_id)
    inviter_id = session['user_id']

    if user not in team.members:
        invitation = Invitation(team_id=team_id, inviter_id=inviter_id, invitee_id=user_id)
        db.session.add(invitation)
        db.session.commit()
        flash(f'已向 {user.username} 发送邀请！')
    else:
        flash(f'{user.username} 已经是团队成员！')

    return redirect(url_for('team_invitation', team_id=team_id))


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

# 地理编码
def get_coordinates(location, api_key):
    geocode_url = f'https://restapi.amap.com/v3/geocode/geo?key={api_key}&address={location}'
    response = requests.get(geocode_url, timeout=5)
    response.raise_for_status()
    return response.json()

@app.route('/routes')
def routes():
    user_id = session.get('user_id')
    location = '北京天安门'
    latitude = 39.90923  # 默认纬度（天安门广场）
    longitude = 116.397428  # 默认经度（天安门广场）
    success = 1

    if user_id:
        user = User.query.get(user_id)
        if user and user.location:
            location = user.location
            api_key = 'bb473ee6868451fd16466294cf236a05'
            try:
                data = get_coordinates(location, api_key)
                if data['status'] == '1' and data['geocodes']:
                    geocode = data['geocodes'][0]
                    longitude, latitude = map(float, geocode['location'].split(','))
            except requests.exceptions.RequestException as e:
                print(f"Error fetching geocode: {e}")
                location = user.location
                success = 0
    
    return render_template('routes.html', location=location, latitude=latitude, longitude=longitude, success=success)

@app.route('/invitations')
def invitations():
    user_id = session['user_id']
    received_invitations = Invitation.query.filter_by(receiver_id=user_id).all()
    sent_invitations = Invitation.query.filter_by(sender_id=user_id).all()
    return render_template('invitations.html', received_invitations=received_invitations, sent_invitations=sent_invitations)

# @app.route('/respond_invitation/<int:invitation_id>/<string:response>', methods=['POST'])
# def respond_invitation(invitation_id, response):
#     invitation = Invitation.query.get(invitation_id)
#     if invitation and invitation.receiver_id == session['user_id']:
#         invitation.status = response
#         db.session.commit()
#     return redirect(url_for('invitations'))

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

@app.route('/log/delete/<int:log_id>', methods=['POST'])
def delete_log(log_id):
    log = Log.query.get(log_id)
    if log and log.user_id == session['user_id']:
        db.session.delete(log)
        db.session.commit()
    return redirect(url_for('log'))

@app.route('/log/edit/<int:log_id>', methods=['GET', 'POST'])
def edit_log(log_id):
    log = Log.query.get(log_id)
    if request.method == 'POST':
        if log and log.user_id == session['user_id']:
            log.content = request.form['content']
            db.session.commit()
            return redirect(url_for('log'))
    return render_template('edit_log.html', log=log)

@app.route('/manage_invitations')
def manage_invitations():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    sent_invitations = Invitation.query.filter_by(inviter_id=user_id).all()
    received_invitations = Invitation.query.filter_by(invitee_id=user_id).all()
    return render_template('manage_invitations.html', sent_invitations=sent_invitations, received_invitations=received_invitations)


@app.route('/respond_invitation/<int:invitation_id>/<string:response>', methods=['POST'])
def respond_invitation(invitation_id, response):
    invitation = Invitation.query.get_or_404(invitation_id)
    if invitation.invitee_id != session.get('user_id'):
        flash('你无权操作此邀请。')
        return redirect(url_for('manage_invitations'))

    if response == 'accept':
        invitation.status = 'accepted'
        # 添加到团队成员
        team = Team.query.get(invitation.team_id)
        user = User.query.get(invitation.invitee_id)
        if user not in team.members:
            team.members.append(user)
        flash('你已接受邀请。')
    elif response == 'reject':
        invitation.status = 'rejected'
        flash('你已拒绝邀请。')

    db.session.commit()
    return redirect(url_for('manage_invitations'))

@app.route('/my_teams')
def my_teams():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    teams = user.teams
    return render_template('my_teams.html', teams=teams)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="10.243.58.126", port="8080", debug=True)

