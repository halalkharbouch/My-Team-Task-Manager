# Imports
from flask import Flask, render_template, url_for, session, request, redirect
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import sqlalchemy.exc
from sqlalchemy.orm import relationship, sessionmaker
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from functools import wraps
import random
import os


#Setting Up Avatar
folder_path = './static/images/lg'
avatar_list = os.listdir(folder_path)


# Initialising Flask
app = Flask(__name__)

# Flask Configurations
app.config["SECRET_KEY"] = os.environ.get("secret_key")

# DB configurations (sqlalchemy)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///halal_tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Setup loging manager
login_manager = LoginManager()
login_manager.init_app(app)

#Setting Up Jinja Env
app.jinja_env.autoescape = False

# Creating engine and session
engine = create_engine("sqlite:///halal_tasks.db")
Session = sessionmaker(bind=engine)
session = Session()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Configure Tables
## Team Association Table
team_association = db.Table(
    'team_association',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('team_member_id', db.Integer, db.ForeignKey('users.id'))
)



## Task Association Table
task_association = db.Table('task_association',
                            db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                            db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'))
                            )


## User Table
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(250), nullable=False)
    last_name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    avatar_location = db.Column(db.String(250))

    tasks = db.relationship('Task', secondary=task_association, backref='users')

    authored_tasks = db.relationship('Task', backref='author')

    task_list_authored = db.relationship('Checklist', backref='author')

    checklist_tasks_assigned = db.relationship('Checklist', backref='assigned_to')

    # Define the one-to-many relationship between users and notifications
    notifications_sent = db.relationship('Notification', foreign_keys='Notification.send_by', back_populates='sender',
                                         lazy='joined')
    notifications_received = db.relationship('Notification', foreign_keys='Notification.send_to',
                                             back_populates='recipient', lazy='joined')


    comments = db.relationship("Comment", backref="comment_author")
    comments_reply = db.relationship("Reply", backref="reply_author")

    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    invites = db.relationship('User')


    teams = db.relationship(
        'User',
        secondary=team_association,
        primaryjoin=id == team_association.c.user_id,
        secondaryjoin=id == team_association.c.team_member_id,
        backref=db.backref('team_members', lazy='dynamic'),
        lazy='dynamic')

## COmment Table
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    comment_text = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))


    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))

    replies = db.relationship("Reply", backref="parent_comment")

## Reply Table
class Reply(db.Model):
    __tablename__ = 'replies'
    id = db.Column(db.Integer, primary_key=True)
    reply_text = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))


    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'))


## Task Table
## Tasks Table
class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    task_description = db.Column(db.Text, nullable=False)
    task_type = db.Column(db.String(250))
    due_date = db.Column(db.String(250))
    task_status = db.Column(db.String(250))

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))



    task_attachements_loc = db.Column(db.String(250))

    task_checklists = db.relationship("Checklist", backref="parent_task")


    task_comments = db.relationship("Comment", backref="parent_task")

## Checklist Table
class Checklist(db.Model):
    __tablename__ = 'checklists'
    id = db.Column(db.Integer, primary_key=True)
    checklist_desc = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.String(250))
    status = db.Column(db.String(250))

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))


    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"))


## Notifications Table
class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    notificationtext = db.Column(db.Text, nullable=False)
    send_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign key linking to User for sender
    send_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign key linking to User for recipient

    # Define relationships to User for sender and recipient
    sender = db.relationship('User', foreign_keys=[send_by], back_populates='notifications_sent', lazy='joined')
    recipient = db.relationship('User', foreign_keys=[send_to], back_populates='notifications_received', lazy='joined')





# Create database
with app.app_context():
    db.create_all()


# -------------------------- All Functions ---------------------------


# Home Route (login or dashboard)
@app.route('/')
def login_or_dashboard():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


# Login Route
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        print(user)
        if request.form.get('password') == user.password:
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('ui-elements/auth-signin.html')


# Sign up Route
@app.route('/signup', methods=["POST", "GET"])
def signup():
    if request.method == 'POST':

        new_user = User(first_name=request.form.get("first_name"),
                            last_name=request.form.get("last_name"),
                            email=request.form.get("email"),
                            password=request.form.get("password"),
                            avatar_location=random.choice(avatar_list)
                            )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))

    return render_template('ui-elements/auth-signup.html')


# Logout Route
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


# Dashboard Route
@login_required
@app.route('/dashboard')
def dashboard():
    return render_template('projects.html')


# My Boards Route
@app.route('/my-boards', methods=['POST', 'GET'])
def my_boards():

    current_page = 'my_boards'
    all_tasks = Task.query.all()
    all_checklists = Checklist.query.all()
    if request.method == 'POST':
        if 'add_task' in request.form:
            new_task = Task(task_description=request.form.get('task_description'),
                            task_type=request.form.get('task_type'),
                            due_date=request.form.get('due_date'),
                            task_status='new',
                            author=current_user
                            )
            db.session.add(new_task)
            current_user.tasks.append(new_task)



            db.session.commit()
            return redirect(url_for('my_boards'))
        elif 'add_checklist' in request.form:
            parent_task = Task.query.get(request.args.get('task_id'))
            assigned_to = User.query.get(request.form.get('assigned_to'))
            new_checklist = Checklist(checklist_desc=request.form.get('checklist_desc'),
                                      due_date=request.form.get('due_date'),
                                      assigned_to=assigned_to,
                                      parent_task=parent_task,
                                      status='inprogress')
            db.session.add(new_checklist)

            db.session.commit()
            return redirect(url_for('my_boards'))
        elif 'invite_member' in request.form:
            email = request.form.get('_email')
            receiver = User.query.filter_by(email=email).first()
            receiver.invites.append(current_user)

            new_notification = Notification(notificationtext="Sent you a team invite request",
                                            sender=current_user,
                                            recipient=receiver)

            db.session.add(new_notification)

            print(current_user.email)
            print(receiver.first_name)
            db.session.commit()
        elif 'accept_request' in request.form:
            requester = User.query.get(request.args.get('requester_id'))

            new_notification = Notification(notificationtext="Accepted your request",
                                            sender=current_user,
                                            recipient=requester)

            db.session.add(new_notification)

            current_user.teams.append(requester)
            requester.teams.append(current_user)
            current_user.invites.remove(requester)


            db.session.commit()
        elif 'reject_request' in request.form:
            requester = User.query.get(request.args.get('requester_id'))
            current_user.invites.remove(requester)

            new_notification = Notification(notificationtext="Rejected request",
                                            sender=current_user,
                                            recipient=requester)

            db.session.add(new_notification)

            db.session.commit()
        elif 'save_edited_checklist' in request.form:
            checklist = Checklist.query.get(request.args.get('checklist_id'))
            checklist.checklist_desc = request.form.get('checklist_desc')
            checklist.status = request.form.get('status')
            assigned_to = User.query.get(request.form.get('assigned_to'))
            checklist.assigned_to = assigned_to
            checklist.due_date = request.form.get('due_date')
            db.session.commit()
        elif 'add_comment' in request.form:
            parent_task = Task.query.get(request.args.get('task_id'))
            new_comment = Comment(comment_text=request.form.get('comment_text'),
                                  comment_author=current_user,
                                  parent_task=parent_task)
            db.session.add(new_comment)
            author = User.query.get(parent_task.author.id)
            new_notification = Notification(notificationtext=f"Added a new comment: {new_comment.comment_text} on {parent_task.task_description}",
                                            sender=current_user,
                                            recipient=author)

            db.session.add(new_notification)

            db.session.commit()
        elif 'add_reply' in request.form:
            parent_comment = Comment.query.get(request.args.get('comment_id'))
            new_reply = Reply(reply_text=request.form.get('reply_text'),
                              reply_author=current_user,
                              parent_comment=parent_comment)
            db.session.add(new_reply)
            parent_comment.replies.append(new_reply)
            author = User.query.get(parent_comment.comment_author.id)
            new_notification = Notification(notificationtext=f"Replied {new_reply.reply_text} to your comment",
                                            sender=current_user,
                                            recipient=author)

            db.session.add(new_notification)

            db.session.commit()
        elif 'move_to_inprogress' in request.form:
            task = Task.query.get(request.args.get('task_id'))
            task.task_status = 'inprogress'
            db.session.commit()
        elif 'move_to_completed' in request.form:
            task = Task.query.get(request.args.get('task_id'))
            task.task_status = 'completed'
            db.session.commit()
        elif 'reopen_task' in request.form:
            task = Task.query.get(request.args.get('task_id'))
            task.task_status = 'inprogress'
            db.session.commit()
        elif 'add_user_to_task' in request.form:
            user_to_add = User.query.get(request.args.get('user'))
            task = Task.query.get(request.args.get('task_id'))
            print(task.task_description, task.id)

            new_notification = Notification(notificationtext=f"Added You to a task: {task.task_description}",
                                            sender=current_user,
                                            recipient=user_to_add)

            db.session.add(new_notification)

            user_to_add.tasks.append(task)
            db.session.commit()
        elif 'delete_user_from_task' in request.form:
            user = User.query.get(request.args.get('user_id'))
            task = Task.query.get(request.args.get('task_id'))
            user.tasks.remove(task)
            db.session.commit()
        elif 'delete_task' in request.form:
            task = Task.query.get(request.args.get("task_id"))
            print(task)
            db.session.delete(task)
            db.session.commit()
            return redirect(url_for('dashboard'))
    return render_template('projects.html', current_page=current_page, all_tasks=all_tasks, all_checklists=all_checklists)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)