import ssl
import socket
import sys


def create():
    try:
        global host
        global port
        global sock

        host = '0.0.0.0'

        port = input('Enter port to listen on: ')

        try:
            port = int(port)
            if not port or port < 1001 or port > 65534:
                raise ValueError()
        except ValueError:
            create()

        sock = ssl.wrap_socket(sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                               keyfile='server.key',
                               certfile='server.crt',
                               server_side=True)

    except socket.error as e:
        print('Error creating socket: {}'.format(e))


def bind():
    try:
        print('Binding socket at port {}'.format(port))
        sock.bind((host, port))
        sock.listen(1)
    except socket.error as e:
        print('Error binding socket: {}'.format(e))
        print('Retrying...')
        bind()


def accept():
    global conn
    global addr
    global hostname

    try:
        conn, addr = sock.accept()
        print('Opened session for {}:{}\n'.format(addr[0], addr[1]))
        hostname = conn.recv(1024)
        interact()

    except socket.error as e:
        print('Error accepting socket: {}'.format(e))


def interact():
    while True:
        command = input('{}@{}$ '.format(addr[0], hostname))

        if command == 'quit_server':
            conn.close()
            sock.close()
            sys.exit()

        conn.send(command.encode())
        result = conn.recv(65536)

        if result != hostname:
            print(result)


create()
bind()
accept()
