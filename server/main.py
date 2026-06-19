import daemon
from server.network.server import Server

if __name__ == "__main__":
    with daemon.DaemonContext():
        server = Server()
        server.run()
