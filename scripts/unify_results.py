from fedt.settings import final_results_folder, results_folder, logs_folder
from fedt.utils import setup_logger, create_strategy_result_folder
from glob import glob
import json
from pathlib import Path
import os
import pandas as pd

import logging

logger = setup_logger(
    name="UNIFY_RESULTS",
    log_file="unify_results.log",
    level=logging.DEBUG
)

def unify_clients_and_server_data():
    strategies_folder = [path for path in results_folder.iterdir() if path.is_dir()]

    logger.warning(f"Pasta base: {results_folder}")
    logger.info(f"Estrátegias encontrados: {[strategy_folder.name for strategy_folder in strategies_folder]}")

    for strategy_folder in strategies_folder:
        final_strategy_results_folder = create_strategy_result_folder(final_results_folder, strategy_folder.name)

        targets_folder = [path for path in strategy_folder.iterdir() if path.is_dir()]
        logger.info(f"Targets encontrados: {[target.name for target in targets_folder]}")

        base_target_folder = targets_folder[0]
        additional_target_folders = targets_folder[1:]
        logger.warning(f"O {base_target_folder.name} vai ser utilizado como base para a unificação")
        logger.warning(f"Arquivos que serão unificados à base {[additional.name for additional in additional_target_folders]}")

        search_pattern = f"{strategy_folder.name}_{base_target_folder.name}_*.json"
        logger.debug(f"Padrão de busca de arquivos: {search_pattern}")
        base_target_files = base_target_folder.glob(search_pattern)

        for file_path in base_target_files:
            logger.info(file_path.name)
            
            simulation_number = (file_path.name).split("_")[-1].replace(".json", "")
            logger.debug(f"Número de simulação: {simulation_number}")

            with open(file_path, "r") as file:
                base_data = json.load(file)

            final_data = {base_target_folder.name : base_data}
            
            for target_folder in additional_target_folders:
                additional_file_path = (target_folder / f"{strategy_folder.name}_{target_folder.name}_{simulation_number}.json").resolve()
                logger.info(f"O arquivo {additional_file_path.name} será adicionado aos dados.")

                if os.path.exists(additional_file_path):
                    with open(additional_file_path, "r") as file:
                        final_data[target_folder.name] = json.load(file)
                else:
                    logger.error(f"O arquivo {additional_file_path} não existe")

            output_path = (final_strategy_results_folder / f"{strategy_folder.name}_{simulation_number}.json").resolve()
            with open(output_path, "w") as file:
                json.dump(final_data, file, indent=4)

            logger.warning(f"Resultado: {output_path}")
                
    logger.warning("Dados internos unificados")

def get_start_and_end_of_a_single_round(round, strategy_file):
    keys = strategy_file.keys()

    start_round_time = float('inf')
    end_round_time = float('-inf')
    for key in keys:
        if not "server" in key:
            if strategy_file[key][round]["round_start_time"] < start_round_time: start_round_time = strategy_file[key][round]["round_start_time"]
            if strategy_file[key][round]["round_end_time"] > end_round_time: end_round_time = strategy_file[key][round]["round_end_time"]

    return start_round_time, end_round_time

def get_start_and_end_round(number_of_rounds, strategy_file):
    time_dict = {}
    for round in range(number_of_rounds):
        round = str(round)
        time_dict[round] = {}
        time_dict[round]["round_start_time"], time_dict[round]["round_end_time"] = get_start_and_end_of_a_single_round(round, strategy_file)
    return time_dict

def add_network_traffic_on_results(result_data, time_dict, network_csv):
    IPs_dict = {
        "10.126.1.109" : (1, "server"),
        "10.126.1.169" : (20, "client")
    }
    users = result_data.keys()
    rounds = time_dict.keys()
    network_traffic = {}
    user_network_traffic = {}
    
    for round in rounds:
        network_traffic[round] = network_csv[
            (network_csv["frame.time_epoch"] >= time_dict[round]["round_start_time"]) &
            (network_csv["frame.time_epoch"] <= time_dict[round]["round_end_time"])
        ]

    for round in rounds:
        for user_IP in IPs_dict:
            user_send_data = network_traffic[round][network_traffic[round]["ip.src"] == user_IP].copy()
            user_receive_data = network_traffic[round][network_traffic[round]["ip.dst"] == user_IP].copy()
            user_send_data["frame.len"] /= IPs_dict[user_IP][0]
            user_receive_data["frame.len"] /= IPs_dict[user_IP][0]

            if IPs_dict[user_IP][1] not in user_network_traffic: user_network_traffic[IPs_dict[user_IP][1]] = {}
            if round not in user_network_traffic[IPs_dict[user_IP][1]]: user_network_traffic[IPs_dict[user_IP][1]][round] = {}

            user_network_traffic[IPs_dict[user_IP][1]][round]["send_data"] = user_send_data["frame.len"].tolist()
            user_network_traffic[IPs_dict[user_IP][1]][round]["receive_data"] = user_receive_data["frame.len"].tolist()

    for user in users:
        if user == "server": source = "server"
        else: source = "client"

        # Tenho que deixar isso mais responsivo no futuro, eliminando a tarefa de definir manualmente o mapeamento e me baseando no IPs_dict.

        for round in rounds:
            result_data[user][round]["send_data"] = user_network_traffic[source][round]["send_data"]
            result_data[user][round]["receive_data"] = user_network_traffic[source][round]["receive_data"]

    return result_data
    
def unify_network_csv_data():
    number_of_rounds = 40

    network_csv_folder = (logs_folder / "network_csv").resolve()

    strategies_folder = [path for path in network_csv_folder.iterdir() if path.is_dir()]
    logger.info(f"Estrátegias encontradas: {[strategy_folder.name for strategy_folder in strategies_folder]}")

    for strategy_folder in strategies_folder:
        search_pattern = f"*_{strategy_folder.name}_*.csv"
        logger.debug(f"Padrão de busca de arquivos: {search_pattern}")
        files_path = strategy_folder.glob(search_pattern)

        for path in files_path:
            logger.info(path)
            network_csv = pd.read_csv(path)

            simulation_number = int((path.name).split("_")[-1].replace(".csv", ""))
            logger.debug(f"Número da simulação: {simulation_number}")

            strategy_result_file_path = (final_results_folder / strategy_folder.name / f"{strategy_folder.name}_{simulation_number+1}.json").resolve()
            with open(strategy_result_file_path, "r") as result_file:
                result_data = json.load(result_file)

            time_dict = get_start_and_end_round(number_of_rounds, result_data)
            result_data = add_network_traffic_on_results(result_data, time_dict, network_csv)

            with open(strategy_result_file_path, "w") as result_file:
                json.dump(result_data, result_file, separators=(",", ":"))

            logger.warning(f"Network traffic adicionado ao {strategy_result_file_path.name}")

    logger.warning(f"Network traffic foi totalmente adicionado.")

def add_cpu_and_ram_on_results(result_data, time_dict, cpu_and_ram_json, user_type):
    cores_dict = {
        "server" : 4,
        "client" : 12
    }
    users = result_data.keys()
    rounds = time_dict.keys()
    cpu_and_ram = {}
    
    for round in rounds:
        if user_type == "server":
            server_pid = cpu_and_ram_json.keys()[0]

            start_round_time = time_dict[round]["round_start_time"]
            end_round_time = time_dict[round]["round_end_time"]

            cpu_and_ram[round] = [
                frame for frame in cpu_and_ram_json[server_pid]
                if start_round_time <= frame["timestamp"] <= end_round_time
            ]
            
        elif user_type == "client":
            pass

   # for round in rounds:
   #     network_traffic[round] = network_csv[
   #         (network_csv["frame.time_epoch"] >= time_dict[round]["round_start_time"]) &
  #          (network_csv["frame.time_epoch"] <= time_dict[round]["round_end_time"])
 #       ]

def unify_cpu_and_ram_data():
    number_of_rounds = 40

    cpu_ram_folder = (logs_folder / "cpu_ram").resolve()

    strategies_folder = [path for path in cpu_ram_folder.iterdir() if path.is_dir()]
    logger.info(f"Estrátegias encontradas: {[strategy_folder.name for strategy_folder in strategies_folder]}")

    for strategy_folder in strategies_folder:
        search_pattern = f"cpu_and_ram_*_{strategy_folder.name}_*.json"
        logger.debug(f"Padrão de busca de arquivos: {search_pattern}")
        files_path = strategy_folder.glob(search_pattern)

        for path in files_path:
            logger.info(path)
            with open(path, "r") as file:
                cpu_and_ram_json = json.load(file)
            
            simulation_number = int((path.name).split("_")[-1].replace(".json", ""))
            logger.debug(f"Número da simulação: {simulation_number}")

            strategy_result_file_path = (final_results_folder / strategy_folder.name / f"{strategy_folder.name}_{simulation_number+1}.json").resolve()
            with open(strategy_result_file_path, "r") as result_file:
                result_data = json.load(result_file)

            time_dict = get_start_and_end_round(number_of_rounds, result_data)
            user_type = "server" if "server" in path.name else "client"
            add_cpu_and_ram_on_results(result_data, time_dict, cpu_and_ram_json, user_type)
            


# unify_clients_and_server_data()
# unify_network_csv_data()
unify_cpu_and_ram_data()