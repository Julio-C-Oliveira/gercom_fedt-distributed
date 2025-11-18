from fedt.settings import scripts_folder, server_ip, server_port, network_interface
from fedt.utils import create_specific_logs_folder, setup_logger

import subprocess

from pathlib import Path

import argparse

parse = argparse.ArgumentParser(description="Script para monitorar o consumo de ram e cpu.")
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

strategy = parse.parse_args().strategy
simulation_number = parse.parse_args().sim_number

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
arquivo_saida = logs_folder / f"captura_de_rede_{strategy}_{sim_number}.pcap"

def main():
    subprocess.run([
        script,
        interface,
        ip_alvo,
        porta,
        arquivo_saida
    ])

if __name__ == "__main__":
    main()
