#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from datetime import datetime


class Message:
    timestamp: float
    author: str
    content: str

    def __init__(self, author, content):
        self.timestamp = datetime.now().timestamp()
        self.author = author
        self.content = content

    def __str__(self):
        return f"{self.author}: {self.content}\n"


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            message = Message(self.login, decoded)
            self.send_message(message)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")

                if self.server.verify_login(login):
                    self.login = login
                    self.send_data(f"Привет, {self.login}!\n")
                    self.send_history(10)
                else:
                    self.send_data(f"Логин {login} занят, попробуйте другой\n")
                    self.transport.close()
            else:
                self.send_data("Неправильный логин\n")

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_data(self, data: str):
        self.transport.write(data.encode())

    def send_message(self, message: Message):
        self.server.save_to_history(message)

        for user in self.server.clients:
            user.send_data(str(message))

    def send_history(self, history_len: int = 0):
        if history_len == 0:
            history_len = len(self.server.history)

        if history_len > len(self.server.history):
            history_len = len(self.server.history)

        for message in sorted(self.server.history, key=lambda msg: msg.timestamp)[-history_len:]:
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

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


if __name__ == '__main__':
    process = Server()

    try:
        asyncio.run(process.start())
    except KeyboardInterrupt:
        print("Сервер остановлен вручную")
