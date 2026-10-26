"""PRUEBA MANUAL (no forma parte de `unittest discover`): ejercita launch_activate_socket con launchctl REAL.

Carga en el dominio gui/<uid> un agente temporal (etiqueta local.homelab.ollama-node.manualtest, puerto alto,
config y `ollama` falso en un directorio temporal), manda una petición y lo descarga. NO toca
~/Library/LaunchAgents ni los agentes de producción. Requiere permiso del usuario:

    OLLAMA_NODE_MANUAL=1 python3 tests/manual_launchd_socket.py
"""
import json
import os
import plistlib
import shutil
import socket
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import ROOT, base_cfg, free_port, make_fake_ollama, tmpdir  # noqa: E402

LABEL = "local.homelab.ollama-node.manualtest"


def main():
    if os.environ.get("OLLAMA_NODE_MANUAL") != "1":
        sys.exit("prueba manual: ejecútala con OLLAMA_NODE_MANUAL=1 y con permiso del usuario")
    d = tmpdir()
    listen, internal = free_port(), free_port()
    cfg = base_cfg(ollama_bin=make_fake_ollama(d), internal_port=internal, listen_port=listen, idle_timeout=5,
                   allowed_cidrs=["127.0.0.1/32"], start_timeout=20)
    cfg_path = os.path.join(d, "config.json")
    json.dump(cfg, open(cfg_path, "w"))
    plist = {
        "Label": LABEL,
        "ProgramArguments": [sys.executable, os.path.join(ROOT, "ollama_node.py"), "--config", cfg_path, "proxy"],
        "Sockets": {"Listeners": {"SockServiceName": str(listen), "SockType": "stream", "SockFamily": "IPv4",
                                  "SockNodeName": "127.0.0.1"}},
        "StandardErrorPath": os.path.join(d, "proxy.log"),
        "StandardOutPath": os.path.join(d, "proxy.log"),
    }
    path = os.path.join(d, LABEL + ".plist")
    with open(path, "wb") as fh:
        plistlib.dump(plist, fh)
    domain = "gui/%d" % os.getuid()
    ok = False
    try:
        subprocess.check_call(["launchctl", "bootstrap", domain, path])
        # launchd ya escucha; el proxy aún no corre
        pre = subprocess.run(["pgrep", "-f", "ollama_node.py.*manualtest|%s" % cfg_path], stdout=subprocess.PIPE)
        print("proxy antes de la petición:", "corriendo" if pre.stdout.strip() else "no corre (esperado)")
        s = socket.create_connection(("127.0.0.1", listen), timeout=30)
        s.sendall(b"GET /api/version HTTP/1.0\r\n\r\n")
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        ok = b"9.9.9-fake" in data
        print("respuesta a través de launchd:", "OK" if ok else "FALLÓ", data[:120])
        print("esperando apagado por inactividad (5 s)...")
        time.sleep(8)
        print("log del proxy:\n" + open(plist["StandardErrorPath"]).read())
    finally:
        subprocess.call(["launchctl", "bootout", "%s/%s" % (domain, LABEL)])
        shutil.rmtree(d, ignore_errors=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
