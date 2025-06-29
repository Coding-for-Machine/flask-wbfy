import os
import pty
import select
import subprocess
import threading

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

clients = {}

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on('connect')
def on_connect():
    print('Client connected:', threading.get_ident())

    # PTY (pseudo-terminal) yaratish
    pid, fd = pty.fork()
    if pid == 0:
        # Child process: bash ni ishga tushirish
        os.execvp("bash", ["bash"])
    else:
        # Parent process: fayl deskriptori saqlanadi
        clients[threading.get_ident()] = fd

        def read_from_terminal():
            while True:
                try:
                    data = os.read(fd, 1024).decode()
                    socketio.emit('terminal_output', data)
                except OSError:
                    break

        thread = threading.Thread(target=read_from_terminal)
        thread.daemon = True
        thread.start()

@socketio.on('terminal_input')
def on_terminal_input(data):
    fd = clients.get(threading.get_ident())
    if fd:
        os.write(fd, data.encode())

@socketio.on('disconnect')
def on_disconnect():
    fd = clients.pop(threading.get_ident(), None)
    if fd:
        os.close(fd)
    print('Client disconnected:', threading.get_ident())

if __name__ == '__main__':
    socketio.run(app, debug=True)
