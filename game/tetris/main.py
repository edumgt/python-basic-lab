#!/usr/bin/env python3

import argparse

from server import LobbyServer
from tet import TetrisRoomClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Tetris single executable launcher")
    parser.add_argument("--server", action="store_true", help="run lobby server mode")
    parser.add_argument("--host", default="0.0.0.0", help="server bind host")
    parser.add_argument("--port", type=int, default=9009, help="server bind port")
    args = parser.parse_args()

    if args.server:
        LobbyServer(args.host, args.port).run()
    else:
        TetrisRoomClient().run()


if __name__ == "__main__":
    main()
