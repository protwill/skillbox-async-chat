#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


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
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")

                if self.server.verify_login(login):
                    self.login = login
                    self.send_data(f"Привет, {self.login}!\n")
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

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"

        for user in self.server.clients:
            user.send_data(message)


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def verify_login(self, login: str):
        return not any(client.login == login for client in self.clients)

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
