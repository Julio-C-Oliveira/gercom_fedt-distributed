import psutil
import time
import json

from fedt.utils import create_specific_logs_folder, setup_logger

from pathlib import Path

import logging

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
    name="CPU_RAM",
    log_file="cpu_ram.log",
    level=logging.INFO
)

logs_folder = create_specific_logs_folder(strategy, "cpu_ram")

# Lista de padrões a monitorar
TARGET_STRINGS = ["--client-id", "fedt run server", "fedt run many-server"]
LOG_FILE = logs_folder / f"cpu_and_ram_{strategy}_{simulation_number}.json"
CHECK_INTERVAL = 0.5
SAVE_INTERVAL = 50

def get_process_cmd(proc):
    """Retorna o comando completo de um processo como string (ou None se inacessível)."""
    try:
        cmdline = proc.info.get('cmdline')
        if not cmdline:
            return None
        return " ".join(cmdline)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None

def find_target_processes(targets):
    """Retorna um dicionário {target_string: [Process, ...]} para cada target encontrado."""
    matches = {t: [] for t in targets}
    for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
        cmd = get_process_cmd(proc)
        if not cmd:
            continue
        for t in targets:
            if t in cmd:
                matches[t].append(proc)
                break
    return matches

def main():
    logger.info(f"Aguardando processos com {TARGET_STRINGS} no comando...")

    # Espera até que pelo menos um processo apareça
    processes = {}
    while not any(processes.values()):
        processes = find_target_processes(TARGET_STRINGS)
        if not any(processes.values()):
            time.sleep(CHECK_INTERVAL)

    # Estrutura dos dados: {target: {pid: [metricas...]}}
    data = {t: {} for t in TARGET_STRINGS}
    iteration_count = 0

    active_pids = [p.pid for plist in processes.values() for p in plist]
    logger.warning(f"Processos encontrados: {active_pids}")

    while any(processes.values()):
        for target, plist in list(processes.items()):
            for proc in list(plist):
                try:
                    if not proc.is_running():
                        plist.remove(proc)
                        continue

                    pid = proc.pid
                    cpu = proc.cpu_percent(interval=None)
                    mem = proc.memory_info().rss / (1024 * 1024)
                    threads = proc.num_threads()
                    timestamp = time.time()

                    if pid not in data[target]:
                        data[target][pid] = []

                    data[target][pid].append({
                        "timestamp": timestamp,
                        "cpu_percent": cpu,
                        "memory_mb": mem,
                        "num_threads": threads
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    if proc in plist:
                        plist.remove(proc)

        # Detecta novos processos
        current_pids = {p.pid for plist in processes.values() for p in plist}
        new_matches = find_target_processes(TARGET_STRINGS)

        for target, new_list in new_matches.items():
            for new_proc in new_list:
                if new_proc.pid not in current_pids:
                    processes[target].append(new_proc)
                    logger.warning(f"Novo processo detectado ({target}): PID {new_proc.pid}")

        iteration_count += 1

        # Salva JSON apenas a cada SAVE_INTERVAL iterações
        if iteration_count % SAVE_INTERVAL == 0:
            with open(LOG_FILE, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"JSON atualizado ({iteration_count} iterações).")

        time.sleep(CHECK_INTERVAL)

    # Salvamento final
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

    logger.info("Todos os processos finalizados. Monitoramento encerrado.")
    logger.info(f"Resultados salvos em '{LOG_FILE}'")

if __name__ == "__main__":
    main()
