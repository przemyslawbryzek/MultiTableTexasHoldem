import argparse
import sys
from server.network.server import Server

def main():
    server = Server()
    server.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poker server")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as a background daemon",
    )
    args = parser.parse_args()

    if args.daemon:
        try:
            import daemon
        except ImportError:
            print("python-daemon is not installed. Run: pip install python-daemon", file=sys.stderr)
            sys.exit(1)
        with daemon.DaemonContext():
            main()
    else:
        main()