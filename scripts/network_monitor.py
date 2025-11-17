from fedt.settings import logs_folder, scripts_folder, server_ip, server_port, network_interface

import subprocess

from pathlib import Path

script = scripts_folder / "network_monitor" 
interface = network_interface
ip_alvo = server_ip
porta = server_port
arquivo_saida = logs_folder / "captura_de_rede.pcap"

subprocess.run([
    script,
    interface,
    ip_alvo,
    porta,
    arquivo_saida
])