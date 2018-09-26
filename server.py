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
import hashlib

# region Server Initialization

# 'Defines a variable that can be used for SocketIO library '
socketio = SocketIO()

# ' Set a variable that can be used for Flask library '
app = Flask(__name__)

# ' config the secreat key for the flask app '
app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

app.debug = True

# ' Set the app path for saving clients img '
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
PHOTOS_UPLOAD_FOLDER = '\static\photos\\'
app.config['UPLOAD_FOLDER'] = PHOTOS_UPLOAD_FOLDER

# ' Defines authorized formats for uploading image files'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

# 'Set the server password salt for the hash function'
SERVER_SALT = '12345qwert!@#$%'

# ' Set the format for saving the date'
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# ' Set the user list in each room'
# ' Room 1 is the list for the sport room, room 2 is the list for the computer games, room 3 is the list for the food
room_1_lst = []
room_2_lst = []
room_3_lst = []
room_4_lst = []


# endregion





# region Socketio

#  -------------------- Socket IO Events --------------------

# '****************************************************************************************************************'
# '**                                                                                                            **'
# '** The joined socket io function send a A status message is broadcast to all the people in the room           **'
# '**                                                                                                            **'
# '** receive message by clients when they enter a room. --> broadcast status messsage to all people in the room **'
# '**                                                                                                            **'
# '****************************************************************************************************************'

@socketio.on('joined', namespace='/chat')
def joined(message):
    # ' Take the room number for the user who send the message'
    room = session.get('room')

    # ' Take the username  for the user who send the message'
    user = session['userName']

    # ' Take the img for the user who send the message'
    img = session['userImage']

    print "--------------- The user {0} has enter to{1} ---------------".format(user, room_1_lst)

    # ' set a virble to know the list to emit'
    userListToEmit = None

    # ' Defin new variable that save the new use info '
    new_user = (user, img)

    # 'chack the new user room's and add it to the room list
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

    # ' Print the user in the room after update
    print 'Room 1 users: {0}'.format(room_1_lst)
    print 'Room 2 users: {0}'.format(room_2_lst)
    print 'Room 3 users: {0}'.format(room_3_lst)
    print 'Room 4 users: {0}'.format(room_4_lst)

    # 'Add the new room soketio list the user
    join_room(room)
    # 'send a status message to evry user in the room'
    emit('status', {'msg': session.get('userName') + ' has entered the room.'}, room=room)

    if userListToEmit is not None:
        emit('userlist', {'userList': userListToEmit}, room=room)


# '***************************************************************************************'
# '**                                                                                   **'
# '** The left socket io function send a a status message when they leave a room.       **'
# '**                                                                                   **'
# '** receive message by clients when they are in the room.                             **'
# '**                                                                                   **'
# '***************************************************************************************'

@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    #'Get the user info'
    room = session.get('room')
    img = session['userImage']
    #'Remove theiser from the Soket io rooms list
    leave_room(room)
    '# Send a message to inform ather pepole in the room of the user Situation'
    emit('status', {'msg': session.get('userName') + ' has left the room.'}, room=room)

    '#remove the user of the room list'
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


# '***************************************************************************************'
# '**                                                                                   **'
# '** The text socket io function send a message to all users in the room.              **'
# '**                                                                                   **'
# '** receive message by clients --> all clients in the room list of soket io           **'
# '**                                                                                   **'
# '***************************************************************************************'

@socketio.on('text', namespace='/chat')
def text(message):
    '#get the user indo'
    room = session.get('room')
    messageFromClient = message['msg']
    userThatSentTheMessage = message['userName']
    photoOfTheUserThatSentTheMessage = message['userPhoto']
    print 'got message, messageFromClient: {0}, userThatSentTheMessage: {1}, photoOfTheUserThatSentTheMessage: {2}' \
        .format(messageFromClient, userThatSentTheMessage, photoOfTheUserThatSentTheMessage)
    '#Brodcastto all users in the room'
    emit('message', {
        'msg': messageFromClient,
        'userThatSentTheMessage': userThatSentTheMessage,
        'photoOfTheUserThatSentTheMessage': photoOfTheUserThatSentTheMessage,
    }, room=room)


# endregion

# region function

# **************************************************************************
# **                                                                      **
# ** The allowed_file function cheak if the file name is proper           **
# **                                                                      **
# ** receive the full filename --> return true if the file type is proper **
# **                                                                      **
# **************************************************************************

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# ********************************************************************************
# **                                                                            **
# ** The login function take a username and password and chack if they are good **
# **                                                                            **
# ** receive user and password --> return true if they are good                 **
# **                                                                            **
# ********************************************************************************

def login(username, password):

    '#chak the hush password for the given '
    hashedPassword = getHashedPassword(password)

    '#chak if the user info is in the db '
    with sqlite3.connect("project2018.db") as conn:
        # find = conn.execute("SELECT * FROM users WHERE username = '{0}' AND password = {1}".format(username, password))
        find = conn.execute(
            "SELECT * FROM reg_users WHERE username = '{0}' AND password = '{1}'".format(username, hashedPassword))
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

# *************************************************************************************************
# **                                                                                             **
# ** The register function take a username, password first and last name, email and selected img **
# **                                                                                             **
# ** return true if the user has been insert to the db or false                                 **
# **                                                                                             **
# *************************************************************************************************

def register(firstname, lastname, username, password, email, birth, img):
    '#Get the hushed password for the given one'
    hashedPassword = getHashedPassword(password)
    '#Build a table if not exists'
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
                         (firstname, lastname, username, hashedPassword, email, birth, img))
            return True
        except sqlite3.IntegrityError:
            return False

# *******************************************************************
# **                                                               **
# ** The getHashedPassword function take a password                 **
# **                                                               **
# ** return the hashed password with the server salt(static)       **
# **                                                               **
# *******************************************************************

def getHashedPassword(password):
    m = hashlib.md5()
    '#encript the given password with server salt(static)'
    m.update('{originalPassword}{salt}'.format(originalPassword=password, salt=SERVER_SALT))
    '#return the password with numbers and leters'
    return m.hexdigest()

# *******************************************************************
# **                                                               **
# ** The send_restart_passmail function take a user mail address   **
# **                                                               **
# ** return true if the email was sent and false otherwise         **
# **                                                               **
# *******************************************************************

def send_restart_passmail(mailadd):
    '#get the six digit code'
    sixdigt = generat_code(mailadd)
    '#cheack if the mail addres is in the db'
    if sixdigt == False:
        print "mail adres not corect"
        return False
    '#Get the content to sent in the email'
    content = "your six digit password for restart your password is " + str(sixdigt) + "Be aware of the code is valid for 24 hours"
    try:
        '#try to conevt to googel smtp server'
        mail = smtplib.SMTP('smtp.gmail.com', 587)
        mail.ehlo()
        mail.starttls()
        '#Try to login to gmaiserver wih the corent acount'
        mail.login("yhserverproject2018@gmail.com", "yhserver2018")
        '#Sends the email to the user address with the unique code'
        mail.sendmail('yhserverproject2018@gmail.com', mailadd, content)
        mail.close()
        return True
    except:
        return False

# *************************************************************************
# **                                                                     **
# ** The generat_code function take a user mail address                  **
# **                                                                     **
# ** Returns the unique code if the email is found and another is false  **
# **                                                                     **
# *************************************************************************

def generat_code(mailadd):
    '#generat random code'
    sixdigt = randint(100000, 1000000)
    '#insert the code and the date to the db '
    with sqlite3.connect("project2018.db") as conn:
        # find = conn.execute("SELECT * FROM users WHERE username = '{0}' AND password = {1}".format(username, password))
        sqls = "SELECT username, email FROM reg_users WHERE email = '{0}'".format(mailadd)
        find = conn.execute(sqls)
        result = find.fetchall()
        if len(result) > 0:
            with sqlite3.connect("project2018.db") as conn:
                conn.execute('''CREATE TABLE IF NOT EXISTS restart_password_cods
                                (username  TEXT    NOT NULL,
                                 email     TEXT    NOT NULL,
                                 reset     int     NOT NULL,
                                 created   TEXT    NOT NULL);''')
                conn.execute("INSERT INTO restart_password_cods VALUES (?, ?, ?, ?);",
                             (result[0][0], result[0][1], sixdigt, datetime.datetime.now().strftime(DATE_TIME_FORMAT)))
                print "sixd digit 2 "
                print sixdigt
                return sixdigt
        return False

# *************************************************************************
# **                                                                     **
# ** The validation function take al neded user date                     **
# **                                                                     **
# ** Returns true if all information is by definition and false if not   **
# **                                                                     **
# *************************************************************************

def validation(username, password, passwordrpt, FirstName, LastName, bday, email):
        pas = True

        '# Checks if the username is more than 5 characters'
        if len(username) < 5:
            flash("Username must be at least 5 characters long", 'category2')
            pas = False

        '#Checks if the username exists in the system'
        with sqlite3.connect("project2018.db") as conn:
            find = conn.execute(
                "SELECT * FROM reg_users WHERE username = '{0}'".format(username))
            userData = find.fetchall()
        if len(userData) > 0:
            flash("That username is already taken.", 'category2')
            pas = False

        '#Checks whether email exists in the system'
        with sqlite3.connect("project2018.db") as conn:
            find = conn.execute(
                "SELECT * FROM reg_users WHERE email = '{0}'".format(email))
            userData = find.fetchall()

        if len(userData) > 0:
            print 1
            flash("There is an account under this mail. If you forget the password, you can reset it on the login page",
                  'category2')
            pas = False

        '#Checks if the password is at least 8 characters long'
        if len(password) < 7:
            print 2
            flash("Password must be at least 8 characters long", 'category2')
            pas = False

        '#Checks whether the password is the same as the password for the second time'
        if password != passwordrpt:
            print 3
            flash("Passwords do not match", 'category2')
            pas = False

        '#Checks if there is a letter within the password'
        password_atleast_one_uppper = any(i.isupper() for i in password)
        password_atleast_one_lower = any(i.islower() for i in password)

        if not (password_atleast_one_uppper and password_atleast_one_lower):
            print 4
            flash("Passwords must contain at least one upper and one lower character", 'category2')
            pas = False

        '#Checks if there is a number within the password'
        string_with_number = any(i.isdigit() for i in password)

        if string_with_number != True:
            print 5
            flash("Passwords must contain numbers", 'category2')
            pas = False

        '#Checks if you have used at least 14 years of age'
        year = bday[:bday.index('-')]
        bday = bday[bday.index('-') + 1:]
        month = bday[:bday.index('-')]
        day = bday[bday.index('-') + 1:]
        now = datetime.datetime.now()

        if int(now.year) - int(year) < 14:
            send_eror = True
            print 6
            if send_eror:
                flash("Minimum enrollment age is 14 ", 'category2')
                pas = False
                send_eror = False
            if int(now.month) - int(month) <= 0:
                print 7
                if send_eror:
                    flash("Minimum enrollment age is 14 ", 'category2')
                    pas = False
                    send_eror = False
                if int(now.day) - int(day) < 0:
                    print 8
                    if send_eror:
                        flash("Minimum enrollment age is 14", 'category2')
                        pas = False
                        send_eror = False
            else:
                flash("Minimum enrollment age is 14 ", 'category2')
                pas = False
                send_eror = False

        '#Checks if the first name is more than 1 characters'
        if len(FirstName) < 1:
            print 9
            flash("The length of the first name must be at least 2 characters long ", 'category2')
            pas = False

        '#Checks whether the first name contains numbers'
        FirstName_with_number = any(i.isdigit() for i in FirstName)

        if FirstName_with_number:
            print 10
            flash("The first name can contain only letters ", 'category2')
            pas = False

        '#Checks if the last name is more than 1 characters'
        if len(LastName) < 1:
            print 11
            flash("The length of the last name must be at least 2 characters long  ", 'category2')
            pas = False

        '#Checks whether the last name contains numbers'
        LastName_with_number = any(i.isdigit() for i in LastName)

        if LastName_with_number:
            print 12
            flash("The last name can contain only letters", 'category2')
            pas = False

        '#Checks if there is any problem with the registration details'
        if pas != True:
            flash("There are some issues with registry details. In order to register you need to fix them", 'category1')

        return pas


def valpassword(password):
    pas = True
    # Checks if the password is at least 8 characters long'
    if len(password) < 7:
        print 2
        flash("Password must be at least 8 characters long", 'category1')
        pas = False

    '#Checks if there is a letter within the password'
    password_atleast_one_uppper = any(i.isupper() for i in password)
    password_atleast_one_lower = any(i.islower() for i in password)

    if not (password_atleast_one_uppper and password_atleast_one_lower):
        print 4
        flash("Passwords must contain at least one upper and one lower character", 'category1')
        pas = False

    '#Checks if there is a number within the password'
    string_with_number = any(i.isdigit() for i in password)

    if string_with_number != True:
        print 5
        flash("Passwords must contain numbers", 'category1')
        pas = False
    return pas
# endregion

# region Routes

# -------------------- Routes --------------------

# *************************************************************************
# **                                                                     **
# ** The log_out route function allows a user to log out of their account**
# **                                                                     **
# ** Returns the login page                                              **
# **                                                                     **
# *************************************************************************

@app.route("/log_out", methods=['POST', 'GET'])
def log_out():
    '#Deletes all session variables'
    session.clear()
    return redirect(url_for('login_root'))

# *************************************************************************************************************
# **                                                                                                         **
# ** The login_root route function allows a user to log in  their account or sign up or reset their password **
# **                                                                                                         **
# ** Returns the page according to the action taken                                                          **
# **                                                                                                         **
# *************************************************************************************************************

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

# *************************************************************************************************************
# **                                                                                                         **
# ** The chat route function allows a user to get the source of the HTML page for chat page                  **
# **                                                                                                         **
# ** Returns the html chat page code                                                                         **
# **                                                                                                         **
# *************************************************************************************************************
@app.route("/cheat", methods = ['POST', 'GET'])
def chat():

    if request.method == 'GET':

        try:
            '#Checks whether the user is logged into his account'
            if session['userName'] == '':
                '#If not return them to the login page'
                return redirect(url_for('login_root'))

        except KeyError:
            return redirect(url_for('login_root'))

    if request.method == 'POST':
        '#Takes the message content'
        userForm = request.form.to_dict()
        print userForm
        '#Checks that it is not empty'
        if len(userForm) != 0:
            roomNumber = userForm['roomNumber']
            session['room'] = 'Room Number {0}'.format(roomNumber)
            print roomNumber
    return render_template('cheatroom.html')

# *************************************************************************************************************
# **                                                                                                         **
# ** The change route function allows a user to change the room                                              **
# **                                                                                                         **
# ** Returns the new room                                                                                    **
# **                                                                                                         **
# *************************************************************************************************************

@app.route("/change", methods=['POST', 'GET'])
def change():
    if request.method == 'POST':
        userForm = request.form.to_dict()
        if len(userForm) != 0:
            roomNumber = userForm['roomNumber']
            session['room'] = 'Room Number {0}'.format(roomNumber)
    return redirect(url_for('chat'))
    return render_template('cheatroom.html')


# *************************************************************************************************************
# **                                                                                                         **
# ** The passwordRecoveryStepOne route function allows a user to reset the password                          **
# **                                                                                                         **
# ** Returns the secend step in recovery                                                                     **
# **                                                                                                         **
# *************************************************************************************************************

@app.route("/passwordRecoveryStepOne", methods = ['POST', 'GET'])
def passwordRecoveryStepOne():

    if request.method == 'POST':
        '#Sets a session variable that stores the email address'
        emailAddress = request.form['email']
        session['mail'] = emailAddress
        print "session mail " + str(emailAddress)
        sent = send_restart_passmail(emailAddress)
        if sent:
            redirect(url_for('passwordRecoveryStepTwo'))
            return render_template('recovery2.html')
    return render_template('recovery.html')

# *************************************************************************************************************
# **                                                                                                         **
# ** The passwordRecoveryStepTwo route function allows a user to enter the sux digit password                **
# **                                                                                                         **
# ** Returns the third step if the code is good                                                              **
# **                                                                                                         **
# *************************************************************************************************************
@app.route("/passwordRecoveryStepTwo", methods=['POST', 'GET'])
def passwordRecoveryStepTwo():

    if request.method == 'POST':
        digitcode = request.form['sixDigitCode']
        print digitcode
        '#Checks if such code exists under the given email'
        with sqlite3.connect("project2018.db") as conn:
            sqls = "SELECT username, email, created FROM restart_password_cods WHERE reset = '{0}'".format(digitcode)
            find = conn.execute(sqls)
            result = find.fetchall()
            print result
            if (len(result) > 0) :
                '#Takes the time the code goes into the system and checks if it has not been 24 hours'
                resetPasswordCreatedDateTimeString = result[0][2]
                resetPasswordCreatedDateTime = datetime.datetime.strptime(resetPasswordCreatedDateTimeString,
                                                                          DATE_TIME_FORMAT)
                if (datetime.datetime.now() - resetPasswordCreatedDateTime).days < 1:
                    redirect(url_for('passwordRecoveryStepThree'))
                    return render_template('recovery3.html')
                else:
                    flash("Password is no longer valid Please try a different password or restart the process", 'category1')
            else:
                flash("The Password does not match the email", 'category1')
    return render_template('recovery2.html')

# *************************************************************************************************************
# **                                                                                                         **
# ** The passwordRecoveryStepThree route function allows a user to enter the new password                    **
# **                                                                                                         **
# ** Returns the login page                                                                                  **
# **                                                                                                         **
# *************************************************************************************************************
@app.route("/passwordRecoveryStepThree", methods=['POST', 'GET'])
def passwordRecoveryStepThree():
    if request.method == 'POST':
        email = session['mail']
        '#Gets the new user password'
        new_password = request.form['newPassword']
        '#Updating the new password in the database'
        val = valpassword(new_password)
        if val:
            hashedPassword = getHashedPassword(new_password)
            sql = "UPDATE reg_users SET password = '{0}' WHERE email = '{1}';".format(hashedPassword, email)
            with sqlite3.connect("project2018.db") as conn:
                conn.execute(sql)
            print "************************************************************************************restart*********************************"
        return render_template('recovery3.html')

# *************************************************************************************************************
# **                                                                                                         **
# ** The passwordRecoveryStepThree route function allows a user to enter the new password                    **
# **                                                                                                         **
# ** Returns the login page                                                                                  **
# **                                                                                                         **
# *************************************************************************************************************

@app.route("/register", methods=['POST', 'GET'])
def register_root():
    if request.method == 'POST':
        userform = request.form.to_dict()
        print userform
        '#Takes the necessary data for user registration'
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
                uploadedFile.save(app.root_path + app.config['UPLOAD_FOLDER'] + filename)
                img = filename
        '#Checks that all data meet the requirements'
        val = validation(username, password, passwordrpt, FirstName, LastName, bday, email)
        reg = False
        if val:
            reg = register(FirstName, LastName, username, password, email, bday, img)
        if (reg):
            flash("Your account has been successfully registered", 'category1')
            return redirect(url_for('login_root'))
        flash("data wrong go to reg page")
        return redirect(url_for('login_root'))


# endregion




# -------------------- Routes --------------------

if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('ssl.cert', 'ssl.key')
    socketio.init_app(app)
    socketio.run(app, host='0.0.0.0', port=5000, ssl_context=context)
