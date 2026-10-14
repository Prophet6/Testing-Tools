"""
File server for Remote File Sync v1.0.

This PC listens. The 4-Series processor connects out.

  HTTP   port 8080   HEAD, GET, PUT
  HTTPS  port 8443   same, self-signed certificate
  FTP    port 2121   RETR, STOR, passive data ports 2122-2130

All three protocols share one folder. Check, Retrieve, and Overwrite
on the module are HEAD/GET/PUT or FTP RETR/STOR against that folder.

User and password may be empty, or crestron / crestron.
A different password is rejected. Ctrl+C stops the servers.
Commands on this console: list, reset, quit.
"""

from __future__ import print_function

import argparse
import base64
import datetime
import ipaddress
import logging
import os
import ssl
import sys
import threading
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = os.path.join(HERE, "files")
CERTS = os.path.join(HERE, "certs")
CERT_PATH = os.path.join(CERTS, "server.crt")
KEY_PATH = os.path.join(CERTS, "server.key")

HTTP_PORT = 8080
HTTPS_PORT = 8443
FTP_PORT = 2121
PASSIVE_PORTS = range(2122, 2131)
USER = "crestron"
PASSWORD = "crestron"
LARGE_BYTES = 300 * 1024
MAX_PUT = 2 * 1024 * 1024

PRESENT_JSON = """{
  "digitals": [0, 1, 0, 1],
  "analogs": [8, 16, 32, 64],
  "serials": ["Room A", "Scene 1", "", ""]
}
"""

PRINT_LOCK = threading.Lock()
FILE_LOCK = threading.Lock()
LAN_IP = "127.0.0.1"


def log(msg):
    with PRINT_LOCK:
        print(msg, flush=True)
        try:
            handle = open(os.path.join(HERE, "bench.log"), "a")
            try:
                handle.write(msg + "\n")
            finally:
                handle.close()
        except Exception:
            pass


def local_ipv4():
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "127.0.0.1"


def safe_path(url_path):
    path = url_path.split("?", 1)[0].replace("\\", "/")
    while path.startswith("/"):
        path = path[1:]
    parts = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            return None
        parts.append(part)
    if not parts:
        return ""
    full = os.path.abspath(os.path.join(FILES, *parts))
    root = os.path.abspath(FILES)
    if os.path.normcase(full) == os.path.normcase(root):
        return ""
    prefix = os.path.normcase(root) + os.sep
    if not os.path.normcase(full).startswith(prefix):
        return None
    return full


def seed_files():
    os.makedirs(FILES, exist_ok=True)
    with FILE_LOCK:
        present = os.path.join(FILES, "present.json")
        with open(present, "w", newline="\n") as handle:
            handle.write(PRESENT_JSON)
        large = os.path.join(FILES, "large.bin")
        with open(large, "wb") as handle:
            handle.write(b"X" * LARGE_BYTES)
        missing = os.path.join(FILES, "missing.json")
        if os.path.isfile(missing):
            os.remove(missing)


def list_files():
    with FILE_LOCK:
        names = sorted(os.listdir(FILES))
        lines = []
        for name in names:
            path = os.path.join(FILES, name)
            if os.path.isfile(path):
                lines.append("{0}  {1} bytes".format(name, os.path.getsize(path)))
        return lines


def ensure_cert(lan_ip):
    os.makedirs(CERTS, exist_ok=True)
    if os.path.isfile(CERT_PATH) and os.path.isfile(KEY_PATH):
        return
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "testing-tools")])
    now = datetime.datetime.now(datetime.timezone.utc)
    end = now + datetime.timedelta(days=825)
    alt_names = [
        x509.DNSName("testing-tools"),
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    ]
    try:
        alt_names.append(x509.IPAddress(ipaddress.ip_address(lan_ip)))
    except ValueError:
        pass
    builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .add_extension(x509.SubjectAlternativeName(alt_names), critical=False)
    )
    if hasattr(builder, "not_valid_before_utc"):
        builder = builder.not_valid_before_utc(now).not_valid_after_utc(end)
    else:
        naive_now = now.replace(tzinfo=None)
        naive_end = end.replace(tzinfo=None)
        builder = builder.not_valid_before(naive_now).not_valid_after(naive_end)
    cert = builder.sign(key, hashes.SHA256())
    key_bytes = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    cert_bytes = cert.public_bytes(serialization.Encoding.PEM)
    with open(KEY_PATH, "wb") as handle:
        handle.write(key_bytes)
    with open(CERT_PATH, "wb") as handle:
        handle.write(cert_bytes)
    log("Wrote self-signed certificate: {0}".format(CERT_PATH))


def index_body():
    lines = [
        "Remote File Sync bench",
        "present.json  known small file",
        "missing.json  not on disk until Overwrite creates it",
        "large.bin     300 KB, Retrieve must refuse",
        "",
    ]
    lines.extend(list_files())
    text = "\n".join(lines) + "\n"
    return text.encode("utf-8")


class FileHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    server_version = "Testing-Tools"

    def log_message(self, fmt, *args):
        return

    def _authorized(self):
        header = self.headers.get("Authorization")
        if not header:
            return True
        parts = header.split(" ", 1)
        if len(parts) != 2 or parts[0] != "Basic":
            return False
        try:
            raw = base64.b64decode(parts[1]).decode("utf-8")
        except Exception:
            return False
        user, sep, password = raw.partition(":")
        if sep != ":":
            return False
        return user == USER and password == PASSWORD

    def _reject(self):
        body = b"unauthorized\n"
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Testing-Tools"')
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self._respond(head_only=True)

    def do_GET(self):
        self._respond(head_only=False)

    def do_PUT(self):
        label = "HTTPS" if self.server.secure else "HTTP"
        if not self._authorized():
            log("[{0}] PUT {1} -> 401".format(label, self.path))
            self._reject()
            return
        target = safe_path(self.path)
        if target is None or target == "":
            log("[{0}] PUT {1} -> 400".format(label, self.path))
            self.send_error(400)
            return
        length_text = self.headers.get("Content-Length")
        if length_text is None:
            log("[{0}] PUT {1} -> 411".format(label, self.path))
            self.send_error(411)
            return
        try:
            length = int(length_text)
        except ValueError:
            self.send_error(400)
            return
        if length < 0 or length > MAX_PUT:
            log("[{0}] PUT {1} -> 413".format(label, self.path))
            self.send_error(413)
            return
        data = self.rfile.read(length)
        folder = os.path.dirname(target)
        with FILE_LOCK:
            os.makedirs(folder, exist_ok=True)
            with open(target, "wb") as handle:
                handle.write(data)
        log("[{0}] PUT {1} -> 200 ({2} bytes)".format(label, self.path, len(data)))
        body = b"saved\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _respond(self, head_only):
        label = "HTTPS" if self.server.secure else "HTTP"
        verb = "HEAD" if head_only else "GET"
        if not self._authorized():
            log("[{0}] {1} {2} -> 401".format(label, verb, self.path))
            self._reject()
            return
        target = safe_path(self.path)
        if target is None:
            log("[{0}] {1} {2} -> 400".format(label, verb, self.path))
            self.send_error(400)
            return
        if target == "":
            body = index_body()
            content_type = "text/plain"
        else:
            with FILE_LOCK:
                if not os.path.isfile(target):
                    log("[{0}] {1} {2} -> 404".format(label, verb, self.path))
                    body = b"not found\n"
                    self.send_response(404)
                    self.send_header("Content-Type", "text/plain")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    # Crestron HttpClient reads an error body even on HEAD.
                    # A Content-Length with no bytes becomes "Unexpected end of response".
                    self.wfile.write(body)
                    return
                with open(target, "rb") as handle:
                    body = handle.read()
            content_type = "application/octet-stream"
            if target.endswith(".json"):
                content_type = "application/json"
        log("[{0}] {1} {2} -> 200 ({3} bytes)".format(label, verb, self.path, len(body)))
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)


class SecureMarker(ThreadingHTTPServer):
    secure = False
    ssl_context = None

    def __init__(self, address, handler, secure):
        self.secure = secure
        ThreadingHTTPServer.__init__(self, address, handler)

    def get_request(self):
        sock, addr = ThreadingHTTPServer.get_request(self)
        if not self.secure:
            return sock, addr
        log("[HTTPS] TCP from {0}:{1}".format(addr[0], addr[1]))
        try:
            secured = self.ssl_context.wrap_socket(sock, server_side=True)
        except Exception as ex:
            log("[HTTPS] handshake failed from {0}: {1}".format(addr[0], ex))
            try:
                sock.close()
            except Exception:
                pass
            raise
        version = ""
        try:
            version = secured.version() or ""
        except Exception:
            version = ""
        log("[HTTPS] TLS {0} from {1}".format(version, addr[0]))
        return secured, addr


def make_ftp(lan_ip):
    warnings.filterwarnings("ignore", message="write permissions assigned to anonymous user")
    from pyftpdlib.log import config_logging
    config_logging(level=logging.ERROR)
    from pyftpdlib.authorizers import DummyAuthorizer
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.servers import FTPServer

    authorizer = DummyAuthorizer()
    authorizer.add_user(USER, PASSWORD, FILES, perm="elradfmw")
    authorizer.add_anonymous(FILES, perm="elradfmw")

    class LoggingFTPHandler(FTPHandler):
        def log_cmd(self, cmd, arg, respcode, respstr):
            shown = "" if arg is None else str(arg)
            if str(cmd).upper() == "PASS":
                shown = "****"
            else:
                prefix = os.path.normcase(FILES) + os.sep
                if os.path.normcase(shown).startswith(prefix):
                    shown = shown[len(FILES):].lstrip("\\/")
            log("[FTP] {0} {1} -> {2}".format(cmd, shown, respcode))

    LoggingFTPHandler.authorizer = authorizer
    LoggingFTPHandler.passive_ports = PASSIVE_PORTS
    LoggingFTPHandler.masquerade_address = lan_ip
    LoggingFTPHandler.permit_foreign_addresses = True
    return FTPServer(("0.0.0.0", FTP_PORT), LoggingFTPHandler)


def banner(lan_ip):
    log("")
    log("Remote File Sync bench")
    log("This PC LAN IP : {0}".format(lan_ip))
    log("Use this IP on the processor, not 127.0.0.1.")
    log("Local_Path example: /user/present.json")
    log("Remote_User / Remote_Password: empty, or {0} / {1}".format(USER, PASSWORD))
    log("")
    log("HTTP   http://{0}:{1}/present.json".format(lan_ip, HTTP_PORT))
    log("HTTPS  https://{0}:{1}/present.json".format(lan_ip, HTTPS_PORT))
    log("       Allow_Insecure_TLS high. The certificate is self-signed.")
    log("FTP    ftp://{0}:{1}/present.json".format(lan_ip, FTP_PORT))
    log("")
    log("Missing file:  replace present.json with missing.json")
    log("Too big:       replace present.json with large.bin (300 KB)")
    log("Check, Retrieve, and Overwrite share this folder on all three protocols.")
    log("")
    log("Windows Firewall blocks these ports until you allow them.")
    log("Right-click allow-firewall.bat and Run as administrator (once).")
    log("Commands: list, reset, quit. Ctrl+C also stops.")
    log("")


def console(stop):
    while not stop.is_set():
        line = sys.stdin.readline()
        if line == "":
            stop.set()
            return
        cmd = line.strip().lower()
        if cmd == "":
            continue
        if cmd == "list":
            for row in list_files():
                log(row)
        elif cmd == "reset":
            seed_files()
            log("Restored present.json and large.bin. Removed missing.json.")
        elif cmd in ("quit", "exit"):
            stop.set()
            return
        else:
            log("Commands: list, reset, quit")


def serve(detach):
    global LAN_IP
    LAN_IP = local_ipv4()
    seed_files()
    try:
        ensure_cert(LAN_IP)
    except ImportError:
        log("ERROR: cryptography is not installed.")
        log("Double-click install-dependencies.bat, then start this again.")
        return 1
    try:
        ftp_server = make_ftp(LAN_IP)
    except ImportError:
        log("ERROR: pyftpdlib is not installed.")
        log("Double-click install-dependencies.bat, then start this again.")
        return 1

    try:
        httpd = SecureMarker(("0.0.0.0", HTTP_PORT), FileHandler, False)
        httpsd = SecureMarker(("0.0.0.0", HTTPS_PORT), FileHandler, True)
    except OSError as ex:
        log("ERROR: could not listen: {0}".format(ex))
        log("Close the program that already has the port, then start again.")
        return 1

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # TLS 1.3 is rejected by the 4-Series client. Some firmware still opens
    # the handshake at TLS 1.0, so accept 1.0 through 1.2.
    context.minimum_version = ssl.TLSVersion.TLSv1
    context.maximum_version = ssl.TLSVersion.TLSv1_2
    try:
        context.set_ciphers(
            "ECDHE-RSA-AES128-GCM-SHA256:"
            "ECDHE-RSA-AES256-GCM-SHA384:"
            "ECDHE-RSA-AES128-SHA:"
            "ECDHE-RSA-AES256-SHA:"
            "AES128-SHA:"
            "AES256-SHA:"
            "@SECLEVEL=0"
        )
    except Exception:
        pass
    context.load_cert_chain(CERT_PATH, KEY_PATH)
    httpsd.ssl_context = context

    http_thread = threading.Thread(target=httpd.serve_forever, name="http", daemon=True)
    https_thread = threading.Thread(target=httpsd.serve_forever, name="https", daemon=True)
    ftp_thread = threading.Thread(target=ftp_server.serve_forever, name="ftp", daemon=True)
    http_thread.start()
    https_thread.start()
    ftp_thread.start()

    banner(LAN_IP)
    stop = threading.Event()
    try:
        if detach or not sys.stdin.isatty():
            while not stop.wait(0.5):
                pass
        else:
            console(stop)
    except KeyboardInterrupt:
        stop.set()
    log("Stopping.")

    def shut(server):
        try:
            server.shutdown()
        except Exception as ex:
            log("HTTP shutdown: {0}".format(ex))

    closers = [
        threading.Thread(target=shut, args=(httpd,)),
        threading.Thread(target=shut, args=(httpsd,)),
    ]
    for closer in closers:
        closer.daemon = True
        closer.start()
    for closer in closers:
        closer.join(3)
    try:
        ftp_server.close_all()
    except Exception as ex:
        log("FTP shutdown: {0}".format(ex))
    httpd.server_close()
    httpsd.server_close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--detach", action="store_true")
    args = parser.parse_args()
    sys.exit(serve(args.detach))
