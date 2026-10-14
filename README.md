# Testing-Tools

PC-side bench tools for [Crestron-Modules](https://github.com/Prophet6/Crestron-Modules). This is the default repo for tools we build.

Formerly **ssh-tcp-mock**. GitHub redirects the old name here.

This project is not affiliated with Crestron Electronics.

## Tools

| Launch | Direction | Tests |
|--------|-----------|--------|
| `start-tcp-server.bat` | This PC **listens** (raw TCP, port **23**) | [TCP Client (Dynamic IP)](https://github.com/Prophet6/Crestron-Modules/tree/main/dynamic-tcp-client) |
| `start-ssh-server.bat` | This PC **listens** (SSH, port **2222**) | [SSH Interface Client v2](https://github.com/Prophet6/Crestron-Modules/tree/main/ssh-interface-v2) |
| `start-tcp-client.bat` | This PC **dials out** (raw TCP) | Built-in SIMPL **TCP/IP Server** |
| `start-tcp-auth-client.bat` | This PC **dials out** (plain or TLS + AUTH) | [TCP Server with Authentication](https://github.com/Prophet6/Crestron-Modules/tree/main/tcp-server-with-authentication) |
| `start-udp.bat` | This PC **listens and sends** UDP (port **50001**) | Built-in **UDP/IP Communications** or **UDP Broadcast and Receive** |
| `start-remote-file-sync.bat` | This PC **listens** (HTTP **8080**, HTTPS **8443**, FTP **2121**) | [Remote File Sync v1.0](https://github.com/Prophet6/Crestron-Modules/tree/main/remote-file-sync) |

`mock.py` is the SSH / raw-TCP / UDP program. Type a line and press Enter to send; incoming bytes print as `[RX]`.

## Typical bench

```
┌──────────────────────┐                         ┌──────────────────────┐
│  Windows PC          │                         │  Crestron 4-Series   │
│  Testing-Tools       │                         │  RMC4 / CP4 / …      │
│                      │  TCP 23                 │                      │
│  start-tcp-server ───┼◄────────────────────────┤  TCP Client          │
│                      │                         │  (Dynamic IP)        │
│                      │  SSH 2222               │                      │
│  start-ssh-server ───┼◄────────────────────────┤  SSH Client          │
│                      │                         │                      │
│  start-tcp-client ───┼────────────────────────►┤  TCP/IP Server       │
│  start-tcp-auth-… ───┼────────────────────────►┤  TCP Server + AUTH   │
│                      │  UDP 50001              │                      │
│  start-udp ──────────┼◄──────────────────────►┤  UDP / UDP Broadcast │
└──────────────────────┘                         └──────────────────────┘
```

## Before you begin

1. Windows 10 or 11 PC on the **same LAN** as the processor
2. **Python 3.9+** from [python.org](https://www.python.org/downloads/) — check **Add python.exe to PATH**
3. Double-click `install-dependencies.bat` (once; needed for SSH)
4. Firewall: **right-click `allow-firewall.bat` → Run as administrator** (once). That opens inbound TCP **23**, **2222**, **5000**, **8080**, **8443**, **2121**, **2122-2130**, and UDP **50001**. Without this, the processor never reaches the mock — Windows Firewall is on by default and Python does not get an allow rule.

New to this folder? Read `START-HERE.txt`.

## TCP Client (Dynamic IP)

The mock **listens**. The processor **connects out**.

1. Double-click **`start-tcp-server.bat`**
2. Note the **LAN IP** it prints (not `127.0.0.1`)
3. On the TCP Client (Dynamic IP) symbol:

   | Pin / parameter | Value |
   |-----------------|--------|
   | Address$ | PC LAN IP |
   | Port | `23` |
   | Connect | hold high |

4. Type in the PC window to send to `RX$`. Data you send on `TX$` appears as `[RX]`.

## SSH Client

1. Double-click **`start-ssh-server.bat`**
2. On the SSH Interface Client:

   | Setting | Value |
   |---------|--------|
   | IP_Address$ | PC LAN IP |
   | IP_Port | `2222` |
   | Username$ / Password$ | `crestron` / `crestron` |
   | Accept_Any_Key | **Yes** on first connect |
   | Connect | hold high |

Lab credentials only. `rotate-host-key.bat` then restart the SSH server to test **Accept_New_Key**.

## Crestron TCP Server (processor listens)

1. Enable a TCP/IP Server (built-in or TCP Server with Authentication), note its port
2. Built-in symbol: **IP-NET Address = `0.0.0.0`** (blank will not listen) and hold **Enable** high
3. Double-click **`start-tcp-client.bat`** (plain TCP, often port `5000`)
4. Or **`start-tcp-auth-client.bat`** for AUTH / TLS (default port `50001`)

`Connection refused` (WinError 10061) means the processor is reachable but nothing is listening on that port. The PC client is working; fix Enable / port / IP-NET on the program. If the processor should connect *to this PC*, use `start-tcp-server.bat` instead.

## UDP / UDP Broadcast

This PC **listens** on the port and **sends** datagrams (broadcast or unicast). UDP has no connect handshake, so a send always "succeeds" locally.

1. Hold **Enable** high on the processor UDP symbol. Port default **50001**.
2. Right-click **`allow-firewall.bat` → Run as administrator** if you have not since adding UDP.
3. Double-click **`start-udp.bat`**
4. Port = `50001`. Send to = `255.255.255.255` (broadcast) or the processor IP (unicast, e.g. `192.168.86.200`)
5. Type in the PC window to send. Processor `TX$` / broadcast payloads appear as `[RX]`.

UDP Broadcast and Receive (`MAC,UID,DATA`) example:

```text
AA:BB:CC:DD:EE:FF,bench,hello
```

## Remote File Sync

This PC **listens**. The processor **connects out**. One folder is served over HTTP, HTTPS, and FTP, so Check, Retrieve, and Overwrite can be tried on each protocol against the same file.

1. Double-click **`install-dependencies.bat`** once (adds `pyftpdlib` and `cryptography`).
2. Right-click **`allow-firewall.bat` → Run as administrator** if you have not since these ports were added.
3. Double-click **`start-remote-file-sync.bat`**.
4. On Remote File Sync v1.0, set `Local_Path` to `/user/present.json`. Leave the user and password empty, or set both to `crestron`.

| Protocol | Remote_URL | Extra |
|----------|------------|--------|
| HTTP | `http://<LAN IP>:8080/present.json` | |
| HTTPS | `https://<LAN IP>:8443/present.json` | `Allow_Insecure_TLS` high. The certificate is self-signed, so verification on must fail. |
| FTP | `ftp://<LAN IP>:2121/present.json` | |

`<LAN IP>` is the address the window prints. Do not use `127.0.0.1`.

| Module pulse | File in the URL | What you should see |
|--------------|-----------------|---------------------|
| Check | `present.json` | `Remote_Exists_FB` high. The processor file is unchanged. |
| Check | `missing.json` | `Remote_Exists_FB` low. |
| Retrieve | `present.json` | Processor file replaced. `Retrieved` pulses. The console shows GET or RETR. |
| Retrieve | `missing.json` | Processor file kept. Console shows 404 or 550. |
| Retrieve | `large.bin` | Refused. Feedback says the file is larger than 256 KB. |
| Overwrite | `present.json` | Console shows PUT or STOR. `reset` on this PC restores the original file. |

`present.json` is a small File Reader JSON file. `reset` on the console restores it and deletes `missing.json`. `list` prints names and sizes. An Overwrite of `missing.json` creates that file until `reset`.

## Command line

```text
python mock.py tcp-server --port 23
python mock.py ssh-server --port 2222 --user crestron --password crestron
python mock.py tcp-client --host 192.168.1.10 --port 5000
python tcp-auth-client/tcp_auth_client.py --host 192.168.1.10 --port 50001 --tls --user user --password pass
python mock.py udp --host 255.255.255.255 --port 50001
python mock.py udp --host 192.168.1.10 --port 50001
python remote-file-sync\server.py
python mock.py ssh-server --rotate-key
```

## Security

Lab use. Do not expose these listen ports to an untrusted network. `host_key` is generated on first SSH start and is gitignored.

## License

MIT. See `LICENSE`.
