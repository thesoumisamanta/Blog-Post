from flask import Flask, render_template, request, redirect, flash, send_from_directory
from flask_login import LoginManager, login_user, UserMixin, login_required, logout_user
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

client = MongoClient("mongodb://localhost:27017/")
db = client['Register']
register_collection = db['login_details']
post_collection = db['post_details']

UPLOAD_FOLDER = 'static'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


class User(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username

@login_manager.user_loader
def load_user(username):
    user = register_collection.find_one({'username': username})
    if user:
        return User(user['username'])
    return None

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/code')
def code():
    return render_template('code.html')

@app.route('/home')
def home():
    data = list(post_collection.find())
    return render_template('home.html', data=data)
@app.route('/read_more/<_id>', methods=['GET', 'POST'])
def read_more(_id):
    post = post_collection.find_one({"_id": ObjectId(_id)})
    if post and 'link' in post and post['link']:
        return redirect(post['link'])
    else:
        flash('Link not found or invalid post ID', 'danger')
        return redirect('/home')


@app.route('/tss')
def tss():
    return render_template('tss.html')

@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files['image']
        link = request.form['link']
        current_time = datetime.datetime.now()

        if image:
            image_filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(image_filename)
            image_url = 'static/' + image.filename
        else:
            image_url = None

        post_details = {
            'title': title,
            'content': content,
            'image': image_url,
            'link': link,
            'created_at': current_time
        }

        post_collection.insert_one(post_details)
        return redirect('/home')
    return render_template('post.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = register_collection.find_one({"username": username})

        if user and password == user['password']:
            user_obj = User(user['username'])
            login_user(user_obj)
            return redirect('/')
        else:
            flash("Invalid credentials", 'danger')
            return redirect('/login')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = register_collection.find_one({'username': username})
        if existing_user:
            flash("Username already exists", "danger")
            return redirect('/register')

        login_details = {
            'username': username,
            'email': email,
            'password': password
        }

        register_collection.insert_one(login_details)
        flash("You have been registered successfully", "success")
        return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
