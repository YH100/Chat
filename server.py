from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import smtplib
from flask_socketio import SocketIO
from flask import session
from flask_socketio import emit, join_room, leave_room

socketio = SocketIO()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'
app.debug = True
ip_to_user = {}


# print(request.remote_addr)

#  -------------------- Socket IO Events --------------------
@socketio.on('joined', namespace='/chat')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    join_room(room)
    emit('status', {'msg': session.get('userName') + ' has entered the room.'}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    room = session.get('room')
    messageFromClient = message['msg']
    userThatSentTheMessage = message['userName']
    print 'got message, messageFromClient: {0}, userThatSentTheMessage: {1}'.format(messageFromClient, userThatSentTheMessage)
    emit('message', {
        'msg': messageFromClient,
        'userThatSentTheMessage': userThatSentTheMessage
    }, room=room)


@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    leave_room(room)
    emit('status', {'msg': session.get('userName') + ' has left the room.'}, room=room)


#  -------------------- Socket IO Events --------------------

def login(username, password):
    if username == 'Admin' and password == '123456':
        return True
    with sqlite3.connect("project2018.db") as conn:
        # find = conn.execute("SELECT * FROM users WHERE username = '{0}' AND password = {1}".format(username, password))
        find = conn.execute(
            "SELECT * FROM reg_users WHERE username = '{0}' AND password = {1}".format(username, password))
        if len(find.fetchall()) > 0:
            return True
        return False
    return Flase


def register(firstname, lastname, username, password, email, birth, img):
    num = 1
    with sqlite3.connect("project2018.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS reg_users
                 (ID INT PRIMARY KEY    ,
                 firstname       TEXT    NOT NULL,
                 lastname        TEXT     NOT NULL,
                 username        TEXT    NOT NULL UNIQUE,
                 password        INT     NOT NULL,
                 email           TEXT    NOT NULL,
                 birtthday       TEXT    NOT NULL UNIQUE,
                img             TEXT    NOT NULL);''')
        try:
            conn.execute("INSERT INTO reg_users VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                         (num, firstname, lastname, username, password, email, birth, img))
            return True

        except:
            return False


def send_restart_passmail(mailadd):
    content = "exemple of restart password"
    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login("yhserverproject2018@gmail.com", "yhserver2018")
    mail.sendmail('yhserverproject2018@gmail.com', mailadd, content)
    mail.close()


#  -------------------- Routes --------------------
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
                session['userName'] = user
                session['room'] = 'Default Room'
                return redirect(url_for('rooms'))
    return render_template('login.html')


@app.route("/cheat", methods=['POST', 'GET'])
def chat():
    msg = request.form
    print msg
    return render_template('cheatroom.html')


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
        username = request.form['username']
        print userform
        FirstName = request.form['FirstName']
        LastName = request.form['LastName']
        bday = request.form['bday']
        LastName = request.form['LastName']
        email = request.form['email']
        password = request.form['psw']
        img = request.form['img']
        reg = register(FirstName, LastName, username, password, email, bday, img)
        print "tr" + str(reg)
        if (reg):
            return redirect(url_for('rooms'))
        return redirect(url_for('login_root'))


# -------------------- Routes --------------------

if __name__ == '__main__':
    socketio.init_app(app)

    socketio.run(app, host='0.0.0.0', port=5000)
    # app.run(host='0.0.0.0', port=5000)
