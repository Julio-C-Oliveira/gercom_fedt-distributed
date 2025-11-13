import argparse

import time

from fedt.server import run_server
from fedt.run_clients import run_clients

import subprocess

def run_server_and_clients():
    print("Iniciando servidor...")
    server_proc = subprocess.Popen(["fedt", "run", "server"])

    time.sleep(3)  

    print("Iniciando clientes...")
    clients_proc = subprocess.Popen(["fedt", "run", "clients"])

    server_proc.wait()
    clients_proc.wait()

def main():
    parser = argparse.ArgumentParser(
        description="fedt: Federated Learning for Decision Trees"
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcomandos")

    # Subcomando principal: run
    run_parser = subparsers.add_parser("run", help="Roda a simulação")
    run_subparsers = run_parser.add_subparsers(dest="target", help="")

    # Subcomando: run server
    run_server_parser = run_subparsers.add_parser("server", help="Roda o servidor")
    run_server_parser.set_defaults(func=run_server)

    # Subcomando: run clients
    run_clients_parser = run_subparsers.add_parser("clients", help="Roda os clientes")
    run_clients_parser.set_defaults(func=run_clients)

    # Define o comportamento padrão de "run" sem subcomando
    run_parser.set_defaults(func=run_server_and_clients)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()