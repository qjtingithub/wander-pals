# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    budget = db.Column(db.String(120), nullable=False)
    interests = db.Column(db.String(500), nullable=False)
    companion_requirements = db.Column(db.String(120))  # 新增字段

class Itinerary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    destination = db.Column(db.String(120), nullable=False)
    time = db.Column(db.String(120), nullable=False)
    price = db.Column(db.String(120), nullable=False)
    companion_requirements = db.Column(db.String(500), nullable=False)
    user = db.relationship('User', backref=db.backref('itineraries', lazy=True))

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 添加时间戳字段
    user = db.relationship('User', backref=db.backref('logs', lazy=True))

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recommended_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('recommendations', lazy=True))
    recommended_user = db.relationship('User', foreign_keys=[recommended_user_id], backref=db.backref('recommended_to', lazy=True))

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    itinerary = db.relationship('Itinerary', backref=db.backref('teams', lazy=True))
    creator = db.relationship('User', backref=db.backref('created_teams', lazy=True))
    members = db.relationship('User', secondary='team_members', backref=db.backref('teams', lazy=True))

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_invitations')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_invitations')

