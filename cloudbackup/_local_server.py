import socket
import webbrowser
from .defaults import REDIRECT_PORT


class LocalServer:
    @staticmethod
    def handle(url):
        """
        :param url: url that should be opened to let user give permissions
        :return: tuple(client_socket, response)
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("localhost", REDIRECT_PORT))
        server.listen()
        webbrowser.open(url)
        client, addr = server.accept()
        return client, client.recv(1024).decode()
