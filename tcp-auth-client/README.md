# TCP Auth Client

Python client for [TCP Server with Authentication](https://github.com/Prophet6/Crestron-Modules/tree/main/tcp-server-with-authentication).

From the Testing-Tools root:

```powershell
.\start-tcp-auth-client.bat
```

Or:

```powershell
python tcp_auth_client.py --host <processor-ip> --port 50001
python tcp_auth_client.py --host <processor-ip> --port 50001 --tls --user user --password pass --send "hello"
```

`--tls` does not verify the processor certificate (`ssl self` lab certs).
