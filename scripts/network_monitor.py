from fedt.settings import scripts_folder, server_ip, server_port, network_interface
from fedt.utils import create_specific_logs_folder, setup_logger

import subprocess

from pathlib import Path

import argparse

import logging

parse = argparse.ArgumentParser(description="Script para monitorar o tráfego da rede.")
parse.add_argument(
    "--strategy",
    type=str,
    default=None,
    help="É a estrátegia que está rodando no momento."
)
parse.add_argument(
    "--sim-number",
    type=int,
    default=None,
    help="É o número da simulação."
)
parse.add_argument(
    "--user",
    type=str,
    default=None,
    help="Quem está rodando."
)


args = parse.parse_args()
strategy = args.strategy
simulation_number = args.sim_number
user = args.user

logger = setup_logger(
    name="NETWORK",
    log_file="network.log",
    level=logging.INFO
)

logs_folder = create_specific_logs_folder(strategy, "network")

script = scripts_folder / "network_monitor" 
interface = network_interface
ip_alvo = server_ip
porta = server_port
arquivo_saida = logs_folder / f"{user}_{strategy}_{simulation_number}.pcap"

def main():
    net_proc = subprocess.Popen([
        script,
        interface,
        ip_alvo,
        porta,
        arquivo_saida
    ])

    print(net_proc.pid, flush=True)

if __name__ == "__main__":
    main()
