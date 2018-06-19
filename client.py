from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import smtplib
from flask_socketio import SocketIO

from flask import session
from flask_socketio import emit, join_room, leave_room

socketio = SocketIO()


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
    emit('message', {
        'msg': '{0}: {1}'.format(session.get('userName'), messageFromClient),
        'userThatSentTheMessage': userThatSentTheMessage
    }, room=room)


@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    leave_room(room)
    emit('status', {'msg': session.get('userName') + ' has left the room.'}, room=room)


# -----------------------------------------------------------------------

# print(request.remote_addr)

def login(username, password):
    if username == 'Admin' and password == '123456':
        return True

    with sqlite3.connect("project2018.db") as conn:
        # conn.execute("INSERT INTO users (username,password) VALUES (0,0)");
        find = conn.execute("SELECT * FROM users WHERE username = '{0}' AND password = {1}".format(username, password))
        if len(find.fetchall()) > 0:
            return True
        return False
    return Flase


def send_restart_passmail(mailadd):
    content = "exemple of restart password"
    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login("yhserverproject2018@gmail.com", "yhserver2018")
    mail.sendmail('yhserverproject2018@gmail.com', mailadd, content)
    mail.close()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'
app.debug = True
ip_to_user = {}


#  -------------------- Routes --------------------

@app.route("/cheat", methods=['POST', 'GET'])
def index():
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
            return redirect(url_for('index'))
    return render_template('rooms.html')


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
                return redirect(url_for('index'))

    return render_template('login.html')


if __name__ == '__main__':
    socketio.init_app(app)

    socketio.run(app, host='0.0.0.0', port=5000)
    # app.run(host='0.0.0.0', port=5000)
