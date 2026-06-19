import sys
import pygame
from shared import discovery
from shared.enums import MessageType
from client.network.client import Client

if __name__ == "__main__":
    match len(sys.argv):
        case 1:
            sock = discovery.join_membership()
            host = discovery.probe_request(sock)
            if host:
                client = Client(host)
            else:
                print(
                    "failed to discover server on the local network, trying localhost..."
                )
                client = Client()
        case 2:
            client = Client(sys.argv[1])
        case 3:
            client = Client(sys.argv[1], int(sys.argv[2]))
        case _:
            print(f"usage: {sys.argv[0]} [HOST] [PORT]", file=sys.stderr)
            sys.exit(1)
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    running = True
    while running:
        msg = client.poll()
        if msg:
            # TODO: handle server message
            pass
        for event in pygame.event.get():
            # TODO: handle events
            if event.type == pygame.QUIT:
                running = False
        # TODO: render game
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
