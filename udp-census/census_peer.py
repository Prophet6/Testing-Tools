"""
PC peer for UDP Census v1.0.

This PC listens on the census port. A ?POLL from another machine gets one
or more unicast !HERE replies, so a single RMC4 collector can fill a table.
Type poll to broadcast ?POLL and print the replies, so an answer-only RMC4
can be checked from here.

Wire format, ASCII:
  ?POLL
  !HERE,MAC,UID,Data

Commands: poll, peers N, window S, help, quit.
"""

from __future__ import print_function

import argparse
import socket
import sys
import threading
import time

POLL = "?POLL"
HERE = "!HERE,"
MAX_PEERS = 8


def local_ipv4s():
    found = set(["127.0.0.1"])
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        found.add(sock.getsockname()[0])
        sock.close()
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.add(info[4][0])
    except Exception:
        pass
    return found


def primary_lan_ip(addrs):
    for ip in sorted(addrs):
        if ip != "127.0.0.1" and not ip.startswith("169.254."):
            return ip
    return "127.0.0.1"


def clean(text):
    if not text:
        return ""
    nul = text.find("\0")
    if nul >= 0:
        text = text[:nul]
    return text.strip()


def is_poll(text):
    return text == POLL or text.startswith(POLL)


def split_here(text):
    rest = text[len(HERE):]
    comma1 = rest.find(",")
    if comma1 < 0:
        return rest, "", ""
    mac = rest[:comma1]
    after = rest[comma1 + 1:]
    comma2 = after.find(",")
    if comma2 < 0:
        return mac, after, ""
    return mac, after[:comma2], after[comma2 + 1:]


def peer_fields(index):
    mac = "AA:BB:CC:DD:EE:{0:02X}".format(index)
    uid = "pc-{0}".format(index)
    return mac, uid, "bench"


def here_packet(index):
    mac, uid, data = peer_fields(index)
    return "{0}{1},{2},{3}".format(HERE, mac, uid, data)


class CensusPeer(object):
    def __init__(self, port, peers, window, answer_local=False):
        self.port = port
        self.peers = peers
        self.window = window
        self.answer_local = answer_local
        self.local_ips = local_ipv4s()
        self.sock = None
        self.stop = threading.Event()
        self.ready = threading.Event()
        self.lock = threading.Lock()
        self.collecting = False
        self.rows = {}
        self.thread = None
        self.noted_own_poll = False

    def open(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            sock.bind(("0.0.0.0", self.port))
        except OSError as exc:
            print("ERROR: Could not bind UDP 0.0.0.0:{0}".format(self.port))
            print("  {0}".format(exc))
            print("Close start-udp.bat if it is already using this port.")
            sys.exit(1)
        self.port = sock.getsockname()[1]
        sock.settimeout(0.2)
        self.sock = sock
        self.thread = threading.Thread(target=self._recv, name="census-recv")
        self.thread.daemon = True
        self.thread.start()
        self.ready.wait(2)

    def close(self):
        self.stop.set()
        sock = self.sock
        self.sock = None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        if self.thread is not None:
            self.thread.join(1)

    def set_peers(self, count):
        if count < 1:
            count = 1
        if count > MAX_PEERS:
            count = MAX_PEERS
        with self.lock:
            self.peers = count
        print("Answering with {0} peer(s).".format(count))
        self._print_identities()

    def set_window(self, seconds):
        if seconds < 0.5:
            seconds = 0.5
        if seconds > 30:
            seconds = 30
        with self.lock:
            self.window = seconds
        print("Poll window is {0}s.".format(seconds))

    def send_poll(self):
        with self.lock:
            window = self.window
            self.rows = {}
            self.collecting = True
        try:
            self.sock.sendto(POLL.encode("ascii"), ("255.255.255.255", self.port))
        except OSError as exc:
            with self.lock:
                self.collecting = False
            print("[send failed] {0}".format(exc))
            return
        print("[TX] ?POLL -> 255.255.255.255:{0}".format(self.port))
        print("Waiting {0}s for !HERE replies.".format(window))
        time.sleep(window)
        with self.lock:
            self.collecting = False
            rows = list(self.rows.values())
        rows.sort(key=lambda row: (row[1], row[0]))
        if not rows:
            print("No !HERE replies.")
            print("On the RMC4: Census_Enable high, Census_Discover low, Census_Enable_FB high.")
            print("Same subnet, same port. Leave the v2 beacon off.")
            print("If this PC should receive polls, run allow-firewall.bat as administrator.")
            return
        print("Answers ({0}):".format(len(rows)))
        for index, row in enumerate(rows, 1):
            ip, mac, uid, data = row
            print("  {0}  {1}  {2}  {3}  {4}".format(index, ip, mac, uid, data))

    def handle_line(self, line):
        text = line.strip()
        if text == "":
            return
        parts = text.split()
        cmd = parts[0].lower()
        if cmd in ("quit", "exit"):
            self.stop.set()
            return
        if cmd == "help":
            print("poll          broadcast ?POLL and print replies")
            print("peers N       how many fake processors to answer as (1-{0})".format(MAX_PEERS))
            print("window S      seconds to wait after poll (0.5-30)")
            print("quit")
            return
        if cmd == "poll":
            self.send_poll()
            return
        if cmd == "peers" and len(parts) == 2:
            try:
                self.set_peers(int(parts[1]))
            except ValueError:
                print("peers needs a number, for example: peers 2")
            return
        if cmd == "window" and len(parts) == 2:
            try:
                self.set_window(float(parts[1]))
            except ValueError:
                print("window needs seconds, for example: window 3")
            return
        print("Unknown command. Type help.")

    def _print_identities(self):
        with self.lock:
            count = self.peers
        for index in range(1, count + 1):
            mac, uid, data = peer_fields(index)
            print("  peer {0}: {1},{2},{3}".format(index, mac, uid, data))

    def _recv(self):
        sock = self.sock
        self.ready.set()
        while not self.stop.is_set():
            try:
                chunk, addr = sock.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                break
            if not chunk:
                continue
            text = clean(chunk.decode("ascii", "replace"))
            if text == "":
                continue
            ip = addr[0]
            port = addr[1] if addr[1] else self.port
            print("[RX {0}:{1}] {2}".format(ip, port, text))
            if is_poll(text):
                if not self.answer_local and ip in self.local_ips:
                    if not self.noted_own_poll:
                        self.noted_own_poll = True
                        print("A ?POLL from this PC is not answered.")
                    continue
                self._answer(ip, port)
            elif text.startswith(HERE):
                self._note_here(ip, text)

    def _answer(self, ip, port):
        if not self.answer_local and ip in self.local_ips:
            return
        with self.lock:
            count = self.peers
            sock = self.sock
        if sock is None:
            return
        for index in range(1, count + 1):
            packet = here_packet(index)
            try:
                sock.sendto(packet.encode("ascii"), (ip, port))
            except OSError as exc:
                print("[send failed] {0}".format(exc))
                return
            print("[TX] {0} -> {1}:{2}".format(packet, ip, port))

    def _note_here(self, ip, text):
        mac, uid, data = split_here(text)
        key = uid if uid else mac if mac else ip
        with self.lock:
            if not self.collecting:
                return
            self.rows[key] = (ip, mac, uid, data)


def run_check():
    peer = CensusPeer(0, 2, 1.0, answer_local=True)
    peer.open()
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(2)
    try:
        client.sendto(b"hello", ("127.0.0.1", peer.port))
        try:
            unexpected, _addr = client.recvfrom(512)
        except socket.timeout:
            unexpected = None
        if unexpected is not None:
            print("CHECK FAIL: answered a non-poll")
            return 1
        client.sendto(POLL.encode("ascii"), ("127.0.0.1", peer.port))
        got = []
        for _index in range(2):
            data, _addr = client.recvfrom(512)
            got.append(data.decode("ascii"))
    except socket.timeout:
        print("CHECK FAIL: timed out waiting for !HERE")
        return 1
    finally:
        client.close()
        peer.close()
    expected = [here_packet(1), here_packet(2)]
    if sorted(got) != sorted(expected):
        print("CHECK FAIL: {0}".format(got))
        return 1
    mac, uid, data = split_here(here_packet(1))
    if mac != "AA:BB:CC:DD:EE:01" or uid != "pc-1" or data != "bench":
        print("CHECK FAIL: split")
        return 1
    print("CHECK OK {0}".format(", ".join(sorted(got))))
    return 0


def serve(port, peers, window):
    peer = CensusPeer(port, peers, window)
    peer.open()
    lan = primary_lan_ip(peer.local_ips)
    print("UDP Census peer listening on 0.0.0.0:{0}".format(peer.port))
    print("This PC LAN IP : {0}".format(lan))
    print("Answering ?POLL from other machines. This PC does not answer itself.")
    peer._print_identities()
    print("")
    print("RMC4: UDP Census v1.0 only. Leave UDP Broadcast and Receive v2.0 off.")
    print("  Collector:   Census_Enable and Census_Discover high. This PC shows up as a row.")
    print("  Answer-only: Census_Enable high, Census_Discover low. Type poll here.")
    print("Commands: poll, peers N, window S, help, quit. Ctrl+C to stop.")
    print("Windows Firewall blocks inbound UDP until allow-firewall.bat has been run as administrator.")
    try:
        while not peer.stop.is_set():
            line = sys.stdin.readline()
            if line == "":
                break
            peer.handle_line(line)
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        peer.close()


def main():
    parser = argparse.ArgumentParser(description="PC peer for Crestron UDP Census v1.0")
    parser.add_argument("--port", type=int, default=50001)
    parser.add_argument("--peers", type=int, default=1)
    parser.add_argument("--window", type=float, default=3.0)
    parser.add_argument("--check", action="store_true", help="Answer a local ?POLL and exit")
    args = parser.parse_args()
    if args.check:
        sys.exit(run_check())
    if args.peers < 1 or args.peers > MAX_PEERS:
        print("peers must be 1-{0}".format(MAX_PEERS))
        sys.exit(1)
    if args.window < 0.5 or args.window > 30:
        print("window must be 0.5-30 seconds")
        sys.exit(1)
    serve(args.port, args.peers, args.window)


if __name__ == "__main__":
    main()
