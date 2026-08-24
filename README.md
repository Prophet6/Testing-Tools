# SSH / TCP mock

PC-side bench tool for Crestron modules. It speaks **SSH** or **raw TCP**, always bidirectional: lines you type are sent; incoming bytes print as `[RX]`.

Originally shipped inside [ssh-interface-v2](https://github.com/Prophet6/ssh-interface-v2). This repository is that `test-server` folder on its own.

New to this folder? Read `START-HERE.txt`, then follow the steps below.

This project is not affiliated with Crestron Electronics.

## What you get

| File | Purpose |
|------|---------|
| `mock.py` | The program |
| `requirements.txt` | Python package: Paramiko 3.x |
| `install-dependencies.bat` | One-time `pip install` |
| `start-ssh-server.bat` | **Crestron SSH Client test** — this PC is the SSH server |
| `start-tcp-client.bat` | Raw TCP client — use with SIMPL Windows **TCP/IP Server** or [TCP Server with Authentication](https://github.com/Prophet6/Crestron-Modules/tree/main/tcp-server-with-authentication) |
| `rotate-host-key.bat` | New host fingerprint for Accept_New_Key tests |
| `START-HERE.txt` | One-page cheat sheet |

## Before you begin

1. Windows 10 or 11 PC on the **same LAN** as the Crestron processor
2. **Python 3.9 or newer** from [python.org](https://www.python.org/downloads/)
3. Check **Add python.exe to PATH** on the installer
4. Administrator access (once) for a Windows Firewall rule
5. For SSH tests: [SSH Interface v2](https://github.com/Prophet6/ssh-interface-v2) on a **4-Series** processor

Typical bench:

```
┌──────────────────────┐                         ┌──────────────────────┐
│  Windows PC          │                         │  Crestron 4-Series   │
│  this mock           │                         │  RMC4 / CP4 / …      │
│                      │  SSH 2222  (Client test)│                      │
│  start-ssh-server ───┼◄────────────────────────┤  Client module       │
│                      │                         │                      │
│  start-tcp-client ───┼────────────────────────►┤  TCP/IP Server       │
│                      │  TCP (e.g. 5000)        │  (built-in or module)│
└──────────────────────┘                         └──────────────────────┘
```

## Install

1. Install Python 3.9+ with **Add to PATH**
2. Double-click `install-dependencies.bat` (once)
3. Allow inbound **TCP 2222** on the PC firewall for SSH server tests:

   ```powershell
   New-NetFirewallRule -DisplayName "SSH mock (2222)" `
     -Direction Inbound -Protocol TCP -LocalPort 2222 -Action Allow
   ```

## Crestron SSH Client test

The mock **listens**. The processor **connects out**.

1. Double-click **`start-ssh-server.bat`**
2. On the Client symbol:

   | Setting | Value |
   |---------|--------|
   | IP_Address$ | PC LAN IP (not 127.0.0.1) |
   | IP_Port | `2222` |
   | Username$ | `crestron` |
   | Password$ | `crestron` |
   | Accept_Any_Key | **Yes** on the first connect |
   | Connect | hold high |

Default user/password `crestron` / `crestron` are lab-only.

## Inbound TCP (processor listens)

1. Enable a TCP/IP Server (built-in symbol or TCP Server with Authentication), pick a port
2. Double-click **`start-tcp-client.bat`**
3. Enter the processor IP and that port

## Command line

```text
python mock.py ssh-server --port 2222 --user crestron --password crestron
python mock.py tcp-client --host 192.168.1.10 --port 5000
python mock.py ssh-server --rotate-key
```

## Security

Lab use. Do not expose port 2222 to an untrusted network. `host_key` is generated on first run and is gitignored.
