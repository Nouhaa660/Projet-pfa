"""
Relay TCP Windows → Supabase (pour Docker Desktop).

Pourquoi : le conteneur Docker n'atteint souvent pas le pooler AWS,
alors que Windows oui. Docker se connecte à host.docker.internal:6543
et ce script relaie vers Supabase.

Usage (PowerShell admin recommandé) :
  py -3 docker_supabase_relay.py
"""

from __future__ import annotations

import select
import socket
import socketserver
import threading
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore


LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 6543


def load_target():
    secrets = tomllib.loads(Path(".streamlit/secrets.toml").read_text(encoding="utf-8"))
    host = secrets.get("SUPABASE_DB_HOST", "aws-0-eu-west-1.pooler.supabase.com")
    # Ne jamais relayer vers soi-même
    if host in {"host.docker.internal", "127.0.0.1", "localhost"}:
        host = "aws-0-eu-west-1.pooler.supabase.com"
    # Force pooler transaction port
    port = 6543
    return host, port


TARGET_HOST, TARGET_PORT = load_target()


class RelayHandler(socketserver.BaseRequestHandler):
    def handle(self):
        upstream = socket.create_connection((TARGET_HOST, TARGET_PORT), timeout=20)
        upstream.setblocking(False)
        self.request.setblocking(False)

        sockets = [self.request, upstream]
        try:
            while True:
                readable, _, errored = select.select(sockets, [], sockets, 60)
                if errored:
                    break
                if not readable:
                    break
                for sock in readable:
                    other = upstream if sock is self.request else self.request
                    data = sock.recv(65536)
                    if not data:
                        return
                    other.sendall(data)
        except OSError:
            return
        finally:
            try:
                upstream.close()
            except OSError:
                pass


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    print(f"Relay Docker → Supabase")
    print(f"  listen   {LISTEN_HOST}:{LISTEN_PORT}")
    print(f"  target   {TARGET_HOST}:{TARGET_PORT}")
    print("Laisse cette fenêtre ouverte, puis : docker compose up --build")
    with ThreadedTCPServer((LISTEN_HOST, LISTEN_PORT), RelayHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
