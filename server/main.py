import argparse
import sys
from server.network.server import Server


def main(port: int):
    if port is not None:
        server = Server(port=port)
    else:
        server = Server()
    server.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poker server")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as a background daemon",
    )
    parser.add_argument("-p", "--port", type=int, help="Specify custom port to bind to")
    args = parser.parse_args()

    if args.daemon:
        try:
            import daemon
        except ImportError:
            print(
                "python-daemon is not installed. Run: pip install python-daemon",
                file=sys.stderr,
            )
            sys.exit(1)
        with daemon.DaemonContext():
            main(args.port)
    else:
        main(args.port)
