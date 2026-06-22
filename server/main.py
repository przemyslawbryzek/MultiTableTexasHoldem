import argparse
import sys
import pathlib
import os
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
        dir = pathlib.Path(__file__).parent.resolve()
        log = open(os.path.join(dir, "server.log"), "w+")
        with daemon.DaemonContext(stdout=log, stderr=log):
            main(args.port)
    else:
        main(args.port)
