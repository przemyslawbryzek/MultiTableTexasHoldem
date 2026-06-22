import argparse
import sys
import os
import logging
from logging.handlers import SysLogHandler
from server.network.server import Server


def main(port: int | None):
    logger = logging.getLogger("SysLogLogger")
    logger.setLevel(logging.INFO)
    logger_handler = SysLogHandler(address="/dev/log")
    pid = os.getpid()
    logger_handler.ident = f"texas-holdem[{pid}]: "
    logger.addHandler(logger_handler)
    try:
        if port is not None:
            server = Server(logger, port=port)
        else:
            server = Server(logger)
        server.run()
    except Exception:
        logger.exception("unhandled exception")
        sys.exit(1)


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
