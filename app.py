'''
app.py - server application
'''

from flask import Flask, render_template, request, abort, url_for, flash, session, make_response
from flask_socketio import SocketIO, emit

import secrets
import jwt
import datetime

import db
from login import check_password

# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
ALGORITHM = 'HS256'
JWT_SECRET = 'sEcRet'

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex() # secret key used to sign the session cookie 
app.config.update(                             # ref: https://flask.palletsprojects.com/en/2.3.x/security/#security-cookie
    SESSION_COOKIE_SECURE=True,                # https://testdriven.io/blog/flask-sessions/
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Strict',
)

socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# ref: [ jwt ] https://www.opensourceforu.com/2022/10/implementing-jwt-using-the-flask-framework/
def create_token(username):
    # [*] create jwt (during successful login/ signup)
    payload = {
        'sub': username,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        # change exp to seconds=15 for testing
    }
    encode = jwt.encode(payload=payload, key=JWT_SECRET, algorithm=ALGORITHM)
    return encode


# ref: [ jwt ] https://www.opensourceforu.com/2022/10/implementing-jwt-using-the-flask-framework/
def validate_token():
    # [*] validate jwt
    try:
        access_token = request.cookies.get("jwt_cookie")
        decode = jwt.decode(access_token, key=JWT_SECRET, algorithms=[ALGORITHM])
        return decode['sub']
    except Exception:
        return None
    

@app.route("/")
def index():
    # [*] GET::index page
    return render_template("index.jinja")

@app.route("/repo")
def repo():
    if request.args.get("username") is None: abort(404)
    username = request.args.get("username") 
    repolist = db.get_repolist(username)
    postlist = db.get_postlist(repolist)
    postlist.reverse()
    userlist = db.get_userlist()
    
    return render_template("repo.jinja", username=username, 
                                         repolist=repolist,
                                         postlist=postlist,
                                         userlist=userlist,
                                         session=session)


@app.route("/login")
def login():    
    # [*] GET::login page
    if 'logged_in' in session:
        session['logged_in'] = False
    return render_template("login.jinja")


# ref: [ flash ] https://geekpython.in/flash-messages-on-frontend-using-flask
@app.route("/login/user", methods=["POST"])
def login_user():
    # [*] POST::login button
    if not request.is_json: abort(404)

    username = request.json.get("username")
    password = request.json.get("password")
    user = db.get_user(username)
    # [failed]
    if user is None:
        flash('Error: User does not exist!', 'warning')
        return url_for('login')
    if not check_password(password, user.password):
        flash('Error: Password does not match!', 'danger')
        return url_for('login')
    # [passed]
    session['username'] = username
    session['access_token'] = create_token(username)
    session['logged_in'] = True
    
    flash('Login Successful', "success")
    return url_for('home', username=username)


@app.route("/signup")
def signup():
    # [*] GET::signup page
    if 'logged_in' in session:
        session['logged_in'] = False
    return render_template("signup.jinja")


# ref: [ flash ] https://geekpython.in/flash-messages-on-frontend-using-flask
@app.route("/signup/user", methods=["POST"])
def signup_user():
    # [*] POST::signup button
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")
    # [passed]
    if db.get_user(username) is None:
        db.insert_user(username, password)

        session['username'] = username
        session['access_token'] = create_token(username)
        session['logged_in'] = True

        flash('Signup Successful', "success")
        socketio.emit("sign-up", {'user': username,  'role': 'Student'})
        return url_for('home', username=username)
    # [failed]
    flash('Error: User already exists!', 'warning')
    return url_for('signup')


@app.errorhandler(404)
def page_not_found(_):
    # [*] GET: 404 handler
    return render_template('404.jinja'), 404

# ref: [  cookie   ] https://verdantfox.com/blog/cookies-with-the-flask-web-framework
#      [ http only ] https://stackoverflow.com/questions/73436354/flask-and-httponly-cookie
@app.route("/home")
def home():
    # [*] GET::home page - messaging app
    if request.args.get("username") is None: abort(404)

    username = request.args.get("username") 
    role = db.get_user(username).role
    friendlist = db.get_friendlist(username)
    grouplist = db.get_grouplist(username)

    # [put jwt in flask cookie]
    response = make_response(render_template("home.jinja", 
                                             username=username, 
                                             role=role,
                                             friendlist=friendlist, 
                                             grouplist=grouplist,
                                             session=session))
    # [first time after login/ signup only]
    if 'access_token' in session:
        response.set_cookie("jwt_cookie", session['access_token'], secure=True, httponly=True)
        session.pop('access_token', None)
    return response

@app.route("/rsa")
def rsa_failure():
    # [*] GET::re-login 
    # [rsa failure][sometimes] after login/ signup successful
    flash('rsa failure. sometimes this happen. re-login pls :D', 'warning')
    return url_for('login')

@app.route("/refresh")
def refresh():
    # [*] GET::re-login
    # [refresh][pbkdf2=null][unable to decrypt log key]
    flash('if you refresh, your pbkdf2 become null, for security reasons, you are here.', 'warning')
    return url_for('login')

@app.route("/reauthenticate")
def reauthenticate():
    # [*] GET::re-login
    # [reauthenticate][token dead][401 unathorized]
    flash('Session expired. Please authenticate again.', 'danger')
    return url_for('login')

# ref: [ run with cert ] https://lazypro.medium.com/socket-io-with-tls-f5a936a1976b
#      [  create cert  ] https://deliciousbrains.com/ssl-certificate-authority-for-local-https-development/
#      [    helper     ] ed #434
if __name__ == '__main__':
    # [*] HTTPS
    socketio.run(app, debug=True, ssl_context=('./certs/localhost.crt', './certs/localhost.key'))
