#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from datetime import datetime
from argparse import ArgumentParser


class Message:
    timestamp: float
    author: str
    content: str

    def __init__(self, author, content):
        self.timestamp = datetime.now().timestamp()
        self.author = author
        self.content = content

    def __str__(self):
        return f"{self.author}: {self.content}"


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def __str__(self):
        if self.login:
            return f"{self.login} ({self.host})"

        return f"{self.host}"

    @property
    def logged_in(self):
        return self.login is not None

    def _get_socket_name(self):
        sock = self.transport.get_extra_info('socket')
        return sock.getsockname()

    @property
    def host(self):
        host, _ = self._get_socket_name()
        return host

    @property
    def port(self):
        _, port = self._get_socket_name()
        return port

    def data_received(self, data: bytes):
        print(f"{self}: {data}")

        decoded = data.decode().strip()

        if self.logged_in:
            message = Message(self.login, decoded)
            self.send_message(message)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "")

                if self.server.verify_login(login):
                    self.login = login

                    print(f"Клиент {self.host} залогинился как {self.login}")

                    self.send_data(f"Привет, {self.login}!")
                    self.send_history(10)
                else:
                    self.send_data(f"Логин {login} занят, попробуйте другой.")
                    self.transport.close()
            else:
                self.send_data("Неправильный логин.")

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print(f"Пришел новый клиент {self}")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print(f"Клиент {self} вышел")

    def send_data(self, data: str, end: str = "\r\n"):
        data = data + end
        self.transport.write(data.encode())

    def send_message(self, message: Message):
        self.server.save_to_history(message)

        for user in [client for client in self.server.clients if client.logged_in]:
            user.send_data(str(message))

    def send_history(self, length: int = 0):
        if length <= 0:
            length = len(self.server.history)

        if length > len(self.server.history):
            length = len(self.server.history)

        for message in sorted(self.server.history, key=lambda msg: msg.timestamp)[-length:]:
            self.send_data(str(message))


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def verify_login(self, login: str):
        return not any(client.login == login for client in self.clients)

    def save_to_history(self, message: Message):
        self.history.append(message)

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self, host, port):
        loop = asyncio.get_running_loop()
        coroutine = await loop.create_server(self.build_protocol, host, port)

        print(f"Сервер {host}:{port} запущен ...")

        await coroutine.serve_forever()


def get_cmd_params():
    parser = ArgumentParser(add_help=False)

    parser.add_argument('--host', '-h', nargs="?", dest="host", type=str, default="127.0.0.1")
    parser.add_argument('--port', '-p', nargs="?", dest="port", type=int, default=8888)

    return parser.parse_args()


if __name__ == '__main__':
    params = get_cmd_params()

    process = Server()

    try:
        asyncio.run(process.start(params.host, params.port))
    except KeyboardInterrupt:
        print("Сервер остановлен вручную")
