from flask import Flask, render_template, request, redirect, abort
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_login import LoginManager, UserMixin, login_manager, login_user, login_required, logout_user, current_user
from hashlib import sha256
import string, random
from datetime import datetime

#configuring flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dangal'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogs.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'

def slug_free(slug):
    if Blogs.query.filter_by(slug=slug).first() is None:
        return True
    return False

def slug_generator():
    while True:
        slug = ''.join((random.choice(string.ascii_lowercase) for x in range(10))) 
        if slug_free(slug):
            return slug

#database table for blogs
class Blogs(db.Model):
    #identifier for the blog
    slug = db.Column(db.String(11),primary_key=True)
    title = db.Column(db.String(100),nullable=False)
    subtitle = db.Column(db.String(200))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime)
    #foreign key for the user_id from user table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

#database table for users
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16),unique=True, nullable=False)
    email = db.Column(db.String(50),nullable=False)
    hashed_password = db.Column(db.String(100),nullable=False)
    blogs = db.relationship('Blogs', backref = 'user')

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/profile/<string:username>')
def profile(username):
    user = Users.query.filter_by(username=username).first()
    if user is None:
        abort('404')
    blogs = Blogs.query.filter_by(user=user).all()
    return render_template('profile.html',user=user,blogs=blogs, isloggedin = current_user.is_authenticated)

@app.route('/')
def index():
    blogs = Blogs.query.order_by(desc(Blogs.date)).all()
    return render_template('index.html', blogs=blogs, isloggedin = current_user.is_authenticated)

@app.route('/view/<string:slug>')
def view(slug):
    blog = Blogs.query.filter_by(slug=slug).first()
    uid = blog.user_id
    user = Users.query.filter_by(id=uid).first()
    print(user)
    return render_template('view.html',blog=blog, user=user, isloggedin = current_user.is_authenticated)

@app.route('/add', methods=['GET','POST'])
@login_required
def add():
    if request.method == 'POST':
        title=request.form['title']
        subtitle=request.form['subtitle']
        content=request.form['content']
        slug = slug_generator()
        user_id = current_user.id
        blog_post = Blogs(slug=slug,title=title, subtitle=subtitle,content=content,user_id=user_id,date = datetime.now())
        db.session.add(blog_post)
        db.session.commit()
        return redirect(url_for('view',slug=slug))
    return render_template('add.html', isloggedin = current_user.is_authenticated)

@app.route('/login', methods=['POST','GET'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['user']
        password = request.form['pass']
        hashed_password = sha256(password.encode('utf-8')).hexdigest()
        user = Users.query.filter_by(username=username).first()
        if user:
            if user.hashed_password ==hashed_password:
                login_user(user, remember=True)
                return redirect(url_for('add'))
            else:
                msg= 'incorrect username or password'
        else:
            msg = 'incorrect username or password'
    return render_template('login.html',msg=msg)

@app.route('/signup', methods=['GET','POST'])
def signup():
    msg = ""
    if request.method == "POST":
        username = request.form['user']
        password = request.form['pass']
        email = request.form['email']
        hashed_password = sha256(password.encode('utf-8')).hexdigest()
        user_free = Users.query.filter_by(username=username).first() is None
        if user_free:
            user = Users(username=username, email=email, hashed_password=hashed_password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            msg = "Username already exists"
    return render_template('signup.html',msg=msg)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True,port=80)

