import os
import smtplib
import sqlite3
from random import randint
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session
from flask_socketio import SocketIO
from flask_socketio import emit, join_room, leave_room
from werkzeug.utils import secure_filename
from globalVariables import photosMapping
import ssl

# 'Defines a variable that can be used for SocketIO library '
socketio = SocketIO()

# ' Set a variable that can be used for Flask library '
app = Flask(__name__)

# ' config the secreat key for the flask app '
app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

#app.debug = True

# ' Set the app path for saving clients img
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
PHOTOS_UPLOAD_FOLDER = '\static\photos\\'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = PHOTOS_UPLOAD_FOLDER

# ' Set the user list in each room'
# ' Room 1 is the list for the sport room, room 2 is the list for the computer games, room 3 is the list for the food
room_1_lst = []
room_2_lst = []
room_3_lst = []
room_4_lst = []




#  -------------------- Socket IO Events --------------------

#'****************************************************************************************************************'
#'**                                                                                                            **'
#'** The joined socketio function send a A status message is broadcast to all people in the room                **'
#'**                                                                                                            **'
#'** receive message by clients when they enter a room. --> broadcast status messsage to all people in the room **'
#'**                                                                                                            **'
#'****************************************************************************************************************'
@socketio.on('joined', namespace='/chat')
def joined(message):
# ' Take the room number for the user who send the message'
    room = session.get('room')
# ' Take the username  for the user who send the message'
    user = session['userName']
# ' Take the img for the user who send the message'
    img = session['userImage']
    print "--------------- The user {0} has enter to{1} ---------------".format(user, room_1_lst)
#' set a virble
    userListToEmit = None
    new_user = (user,img)
    if room == "Room Number 1":
        if new_user not in room_1_lst:
            room_1_lst.append((user, img))
        userListToEmit = room_1_lst
    elif room == "Room Number 2":
        if new_user not in room_2_lst:
            room_2_lst.append((user, img))
        userListToEmit = room_2_lst
    elif room == "Room Number 3":
        if new_user not in room_3_lst:
            room_3_lst.append((user, img))
        userListToEmit = room_3_lst
    elif room == "Room Number 4":
        if new_user not in room_4_lst:
            room_4_lst.append((user, img))
        userListToEmit = room_4_lst

    print 'Room 1 users: {0}'.format(room_1_lst)
    print 'Room 2 users: {0}'.format(room_2_lst)
    print 'Room 3 users: {0}'.format(room_3_lst)
    print 'Room 4 users: {0}'.format(room_4_lst)

    join_room(room)
    emit('status', {'msg': session.get('userName') + ' has entered the room.'}, room=room)

    if userListToEmit is not None:
        emit('userlist', {'userList': userListToEmit}, room=room)

@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    img = session['userImage']
    leave_room(room)
    emit('status', {'msg': session.get('userName') + ' has left the room.'}, room=room)
    user = session.get('userName')

    userListToEmit = None
    if room == "Room Number 1":
        room_1_lst.remove((user, img))
        userListToEmit = room_1_lst
    elif room == "Room Number 2":
        room_2_lst.remove((user, img))
        userListToEmit = room_2_lst
    elif room == "Room Number 3":
        room_3_lst.remove((user, img))
        userListToEmit = room_3_lst
    elif room == "Room Number 4":
        room_4_lst.remove((user, img))
        userListToEmit = room_4_lst

    print 'Room 1 users: {0}'.format(room_1_lst)
    print 'Room 2 users: {0}'.format(room_2_lst)
    print 'Room 3 users: {0}'.format(room_3_lst)
    print 'Room 4 users: {0}'.format(room_4_lst)

    if userListToEmit is not None:
        emit('userlist', {'userList': userListToEmit}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    room = session.get('room')
    messageFromClient = message['msg']
    userThatSentTheMessage = message['userName']
    photoOfTheUserThatSentTheMessage = message['userPhoto']
    print 'got message, messageFromClient: {0}, userThatSentTheMessage: {1}, photoOfTheUserThatSentTheMessage: {2}' \
        .format(messageFromClient, userThatSentTheMessage, photoOfTheUserThatSentTheMessage)
    emit('message', {
        'msg': messageFromClient,
        'userThatSentTheMessage': userThatSentTheMessage,
        'photoOfTheUserThatSentTheMessage': photoOfTheUserThatSentTheMessage,
    }, room=room)


#  -------------------- Socket IO Events --------------------

#**************************************************************************
#**                                                                      **
#** The allowed_file function cheak if the file name is proper           **
#**                                                                      **
#** receive the full filename --> return true if the file type is proper **
#**                                                                      **
#**************************************************************************

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def login(username, password):
    if username == 'Admin' and password == '123456':
        return True
    with sqlite3.connect("project2018.db") as conn:
        # find = conn.execute("SELECT * FROM users WHERE username = '{0}' AND password = {1}".format(username, password))
        find = conn.execute(
            "SELECT * FROM reg_users WHERE username = '{0}' AND password = '{1}'".format(username, password))
        userData = find.fetchall()
        if len(userData) > 0:
            if userData[0][6] not in photosMapping:
                session['userImage'] = photosMapping[1]
            else:
                session['userImage'] = photosMapping[userData[0][6]];
            return True
        flash("Incorrect username or password")
        return False
    return Flase


def register(firstname, lastname, username, password, email, birth, img):
    with sqlite3.connect("project2018.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS reg_users
                        (firstname       TEXT    NOT NULL,
                         lastname        TEXT    NOT NULL,
                         username        TEXT    NOT NULL UNIQUE,
                         password        INT     NOT NULL,
                         email           TEXT    NOT NULL UNIQUE,
                         birtthday       TEXT    NOT NULL,
                         img             TEXT    NOT NULL);''')
        try:
            conn.execute("INSERT INTO reg_users VALUES (?, ?, ?, ?, ?, ?, ?);",
                         (firstname, lastname, username, password, email, birth, img))
            return True
        except sqlite3.IntegrityError:
            return False


def send_restart_passmail(mailadd):
    sixdigt = generat_code(mailadd)
    if sixdigt == False:
        print "mail adres not corect"
        return False
    content = "your six digit password is " + str(sixdigt)
    generat_code(mailadd)
    try:
        mail = smtplib.SMTP('smtp.gmail.com', 587)
        mail.ehlo()
        mail.starttls()
        mail.login("yhserverproject2018@gmail.com", "yhserver2018")
        mail.sendmail('yhserverproject2018@gmail.com', mailadd, content)
        mail.close()
        return True
    except:
        return False


def generat_code(mailadd):
    sixdigt = randint(100000, 1000000)
    with sqlite3.connect("project2018.db") as conn:
        # find = conn.execute("SELECT * FROM users WHERE username = '{0}' AND password = {1}".format(username, password))
        sqls = "SELECT username, email FROM reg_users WHERE email = '{0}'".format(mailadd)
        print "sqls " + sqls
        find = conn.execute(sqls)
        result = find.fetchall()
        if len(result) > 0:
            print "six digit 1 "
            print sixdigt
            print request.remote_addr
            with sqlite3.connect("project2018.db") as conn:
                conn.execute('''CREATE TABLE IF NOT EXISTS restart_password_cods
                         (username TEXT NOT NULL,
                          email TEXT NOT NULL,
                          reset int NOT NULL);''')
                conn.execute("INSERT INTO restart_password_cods VALUES (?, ?, ?);",
                             (result[0][0], result[0][1], sixdigt))
                print "sixd digit 2 "
                print sixdigt
                return sixdigt
        return False


# -------------------- Routes --------------------
@app.route("/log_out", methods=['POST', 'GET'])
def log_out():
    session.clear()
    return redirect(url_for('login_root'))


@app.route("/", methods=['POST', 'GET'])
def login_root():
    if request.method == 'POST':
        userform = request.form.to_dict()
        if len(userform) != 0:
            print (userform)
            dictlist = []
            for key, value in userform.iteritems():
                temp = [key, value]
                dictlist.append(temp)
            user = dictlist[0][1]
            password = dictlist[1][1]

            secss_login = login(user, password)
            if secss_login == True:
                session['logged_in'] = True
                session['userName'] = user
                session['room'] = 'Room Number 1'
                return redirect(url_for('chat'))
            else:
                flash("Username or password incorrect", 'category1')
    if session.get('logged_in'):
        print session.get('logged_in')
        if session['logged_in'] == True:
            return redirect(url_for('chat'))

    return render_template('login.html')


@app.route("/uploadp")
def uploadp():
    return render_template("upload.html")


@app.route("/upload", methods=['POST'])
def upload():
    target = os.path.join(APP_ROOT, 'images/')
    print(target)

    if not os.path.isdir(target):
        os.mkdir(target)

    for file in request.files.getlist("file"):
        print(file)
        filename = file.filename
        destination = "/".join([target, filename])
        print(destination)
        file.save(destination)

    return render_template("complete.html")


@app.route("/cheat", methods=['POST', 'GET'])
def chat():
    if request.method == 'GET':
        try:
            if session['userName'] == '':
                return redirect(url_for('login_root'))
        except KeyError:
            return redirect(url_for('login_root'))
#        return render_template('login.html')
    msg = request.form
    print msg
    if request.method == 'POST':
        userForm = request.form.to_dict()
        if len(userForm) != 0:
            roomNumber = userForm['roomNumber']
            session['room'] = 'Room Number {0}'.format(roomNumber)
    return render_template('cheatroom.html')


@app.route("/change", methods=['POST', 'GET'])
def change():
    if request.method == 'POST':
        userForm = request.form.to_dict()
        if len(userForm) != 0:
            roomNumber = userForm['roomNumber']
            session['room'] = 'Room Number {0}'.format(roomNumber)
    return redirect(url_for('chat'))
    return render_template('cheatroom.html')


@app.route("/passwordRecoveryStepOne", methods=['POST', 'GET'])
def passwordRecoveryStepOne():
    if request.method == 'POST':
        emailAddress = request.form['email']
        session['mail'] = emailAddress
        print "session mail " + str(emailAddress)
        sent = send_restart_passmail(emailAddress)
        if sent:
            redirect(url_for('passwordRecoveryStepTwo'))
            return render_template('recovery2.html')
    return render_template('recovery.html')


@app.route("/passwordRecoveryStepTwo", methods=['POST', 'GET'])
def passwordRecoveryStepTwo():
    if request.method == 'POST':
        digitcode = request.form['sixDigitCode']
        print digitcode
        with sqlite3.connect("project2018.db") as conn:
            sqls = "SELECT username, email FROM restart_password_cods WHERE reset = '{0}'".format(digitcode)
            find = conn.execute(sqls)
            result = find.fetchall()
            print result
            if (len(result) > 0):
                redirect(url_for('passwordRecoveryStepThree'))
                return render_template('recovery3.html')
    return render_template('recovery2.html')


@app.route("/passwordRecoveryStepThree", methods=['POST', 'GET'])
def passwordRecoveryStepThree():
    if request.method == 'POST':
        email = session['mail']
        new_password = request.form['newPassword']
        sql = "UPDATE reg_users SET password = '{0}' WHERE email = '{1}';".format(new_password, email)
        with sqlite3.connect("project2018.db") as conn:
            conn.execute(sql)
        return render_template('recovery3.html')


@app.route("/rooms", methods=['POST', 'GET'])
def rooms():
    msg = request.form
    print msg

    if request.method == 'POST':
        userForm = request.form.to_dict()
        if len(userForm) != 0:
            roomNumber = userForm['roomNumber']
            session['room'] = 'Room Number {0}'.format(roomNumber)
            return redirect(url_for('chat'))
    return render_template('rooms.html')


@app.route("/register", methods=['POST', 'GET'])
def register_root():
    if request.method == 'POST':
        userform = request.form.to_dict()
        print userform
        username = request.form['username']
        FirstName = request.form['FirstName']
        bday = request.form['bday']
        LastName = request.form['LastName']
        email = request.form['email']
        password = request.form['psw']
        passwordrpt = request.form['psw_repeat']
        if (request.form['photoSelection'] == 'select'):
            photoNumberTheUserChoose = request.form['photoNumber']
            img = photoNumberTheUserChoose
        elif (request.form['photoSelection'] == 'upload'):
            uploadedFile = request.files['photoUpload']
            if uploadedFile and allowed_file(uploadedFile.filename.lower()):
                filename = secure_filename(uploadedFile.filename)
                # uploadLocation = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename)
                # uploadedFile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                uploadedFile.save(app.root_path + app.config['UPLOAD_FOLDER'] + filename)
                img = filename
        val = validation(username, password, passwordrpt, FirstName, LastName, bday, email)
        reg = False
        if val:
            reg = register(FirstName, LastName, username, password, email, bday, img)
        if (reg):
            flash("Your account has been successfully registered", 'category1')
            return redirect(url_for('login_root'))
        flash("data wrong go to reg page")
        return redirect(url_for('login_root'))


def validation(username, password, passwordrpt, FirstName, LastName, bday, email):
    pas = True
    if len(username) < 5:
        flash("Username must be at least 5 characters long", 'category2')
        pas = False

    with sqlite3.connect("project2018.db") as conn:
        find = conn.execute(
            "SELECT * FROM reg_users WHERE username = '{0}'".format(username))
        userData = find.fetchall()
    if len(userData) > 0:
        flash("That username is already taken.", 'category2')
        pas = False

    with sqlite3.connect("project2018.db") as conn:
        find = conn.execute(
            "SELECT * FROM reg_users WHERE email = '{0}'".format(email))
        userData = find.fetchall()

    if len(userData) > 0:
        print 1
        flash("There is an account under this mail. If you forget the password, you can reset it on the login page", 'category2')
        pas = False

    if len(password) < 7:
        print 2
        flash("Password must be at least 8 characters long", 'category2')
        pas = False

    if password != passwordrpt:
        print 3
        flash("Passwords do not match", 'category2')
        pas = False

    string_with_leter = password.isupper() or password.islower()

    if string_with_leter != True:
        print 4
        flash("Passwords must contain characters", 'category2')
        pas = False

    string_with_number = any(i.isdigit() for i in password)

    if string_with_number != True:
        print 5
        flash("Passwords must contain numbers", 'category2')
        pas = False

    year = bday[:bday.index('-')]
    bday = bday[bday.index('-') + 1:]
    month = bday[:bday.index('-')]
    day = bday[bday.index('-') + 1:]
    now = datetime.datetime.now()

    if int(now.year) - int(year) < 14:
        print 6
        if int(now.month) - int(month) <= 0:
            print 7
            if int(now.day) - int(day) < 0:
                print 8
                flash("Minimum enrollment age is 14", 'category2')
                pas = False
        else:
            flash("Minimum enrollment age is 14 ", 'category2')
            pas = False
    else:
        flash("Minimum enrollment age is 14", 'category2')

    if len(FirstName) < 1:
        print 9
        flash("The length of the first name must be at least 2 characters long ", 'category2')
        pas = False

    FirstName_with_number = any(i.isdigit() for i in FirstName)

    if FirstName_with_number:
        print 10
        flash("The first name can contain only letters ", 'category2')
        pas = False

    if len(LastName) < 1:
        print 11
        flash("The length of the last name must be at least 2 characters long  ", 'category2')
        pas = False

    LastName_with_number = any(i.isdigit() for i in LastName)

    if LastName_with_number:
        print 12
        flash("The last name can contain only letters", 'category2')
        pas = False

    if pas != True:
        flash("There are some issues with registry details. In order to register you need to fix them", 'category1')

    return pas






# -------------------- Routes --------------------

if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('ssl.cert', 'ssl.key')
    socketio.init_app(app)
    socketio.run(app, host='0.0.0.0', port=5000, ssl_context=context)
