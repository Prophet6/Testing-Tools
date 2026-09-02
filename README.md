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

`mock.py` is the SSH / raw-TCP program. Type a line and press Enter to send; incoming bytes print as `[RX]`.

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
└──────────────────────┘                         └──────────────────────┘
```

## Before you begin

1. Windows 10 or 11 PC on the **same LAN** as the processor
2. **Python 3.9+** from [python.org](https://www.python.org/downloads/) — check **Add python.exe to PATH**
3. Double-click `install-dependencies.bat` (once; needed for SSH)
4. Firewall: **right-click `allow-firewall.bat` → Run as administrator** (once). That opens inbound TCP **23**, **2222**, and **5000**. Without this, the processor never reaches the mock — Windows Firewall is on by default and Python does not get an allow rule.

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
2. Double-click **`start-tcp-client.bat`** (plain TCP, often port `5000`)
3. Or **`start-tcp-auth-client.bat`** for AUTH / TLS (default port `50001`)

## Command line

```text
python mock.py tcp-server --port 23
python mock.py ssh-server --port 2222 --user crestron --password crestron
python mock.py tcp-client --host 192.168.1.10 --port 5000
python tcp-auth-client/tcp_auth_client.py --host 192.168.1.10 --port 50001 --tls --user user --password pass
python mock.py ssh-server --rotate-key
```

## Security

Lab use. Do not expose these listen ports to an untrusted network. `host_key` is generated on first SSH start and is gitignored.

## License

MIT. See `LICENSE`.
