
from flask import Flask, render_template, url_for, request,redirect,flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user,login_required, current_user,UserMixin,logout_user



class Base(DeclarativeBase):
  pass






login_manager = LoginManager()


db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todolist2.db"
app.config['SECRET_KEY'] = 'purvanchal'
db.init_app(app)
login_manager.init_app(app)
bootstrap = Bootstrap5(app)

class User(UserMixin,db.Model):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    user_tasks = relationship('Tasklist', back_populates='user_info')


class Tasklist(db.Model):
    __tablename__ = 'tasklist'
    id:Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String)

    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('user.id'))
    user_info = relationship('User', back_populates='user_tasks')
    task_info = relationship('Tasks', back_populates='tasklist_info')


class Tasks(db.Model):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    task_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('tasklist.id'))
    tasklist_info = relationship('Tasklist', back_populates='task_info')


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User,user_id)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed = generate_password_hash(password, 'pbkdf2:sha256',8)

        new_user = User(
            username = username,
            email = email,
            password = hashed
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(user=new_user)
        return redirect(url_for('homepage'))

    return render_template('register.html')

@app.route('/login', methods = ["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()

        if user:
            if check_password_hash(user.password,password):
                login_user(user)
                return redirect(url_for('homepage'))


    return render_template('login.html')

@login_required
@app.route('/home')
def homepage():
    tasklists = Tasklist.query.filter_by(user_id=current_user.id).all()
    return render_template('homepage.html', tasklists=tasklists)


@login_required
@app.route('/newtasklist', methods=["GET", "POST"])
def new_tasklist():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form.get("description", "")

        new_tasklist = Tasklist(name=name, description=description, user_id=current_user.id)
        db.session.add(new_tasklist)
        db.session.commit()

        return redirect(url_for('view_tasklist', tasklist_id=new_tasklist.id))

    return render_template('new_tasklist.html')

@login_required
@app.route('/tasklist/<int:tasklist_id>', methods=["GET", "POST"])
def view_tasklist(tasklist_id):
    tasklist = Tasklist.query.get_or_404(tasklist_id)

    if request.method == "POST":
        task_name = request.form["task_name"]
        due_date = request.form["due_date"]

        new_task = Tasks(task=task_name, date=due_date, tasklist_info=tasklist)
        db.session.add(new_task)
        db.session.commit()

    tasks = Tasks.query.filter_by(task_id=tasklist_id).all()
    return render_template('tasklist.html', tasklist=tasklist, tasks=tasks)


@login_required
@app.route('/tasks/<int:task_id>/complete', methods=["POST"])
def complete_task(task_id):
    task = db.session.execute(db.select(Tasks).where(Tasks.id == task_id)).scalar()

    # Get the completed status from the form
    print(request.form['checkbox1'])
    new_status = request.form['checkbox1']== 'true'
    print(new_status)
    # Only update if the status has changed
    if task.completed != new_status:
        task.completed = new_status
        db.session.commit()

    return redirect(url_for('view_tasklist', tasklist_id=task.task_id))

@login_required
@app.route('/logout')
def logout():
    logout_user()
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

