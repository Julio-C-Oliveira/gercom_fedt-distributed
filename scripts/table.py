from fedt.settings import final_results_folder
from glob import glob
import numpy as np
import logging
import json
from fedt.utils import setup_logger

logger = setup_logger(
    name="TABLE",
    log_file="table.log",
    level=logging.DEBUG
)

def all_clients_mean_and_std(target_metric):
    logger.warning(f"Gráfico: {target_metric}")
    strategies_folder = [path for path in final_results_folder.iterdir() if path.is_dir()]
    logger.info(f"Estrátegias encontrados: {[strategy_folder.name for strategy_folder in strategies_folder]}")

    all_values = []

    for strategy_folder in strategies_folder:
        strategy_name = strategy_folder.name
        search_pattern = f"{strategy_name}_*.json"
        logger.debug(f"Padrão de busca de arquivos: {search_pattern}")
        files_path = strategy_folder.glob(search_pattern)

        for file_path in files_path:
            with open(file_path, "r") as file:
                base_data = json.load(file)

            for user, user_data in base_data.items():
                if user == "server":
                    continue
                    
                for str_round in user_data.keys():
                    all_values.append(user_data[str_round][target_metric])

    all_values = np.array(all_values)
    mean = np.mean(all_values)
    std = np.std(all_values)

    logger.info(f"{target_metric} geral: média {mean} desvio de {std}")

def all_clients_mean_and_std_per_tree(target_metric):
    logger.warning(f"Gráfico: {target_metric}")
    strategies_folder = [path for path in final_results_folder.iterdir() if path.is_dir()]
    logger.info(f"Estrátegias encontrados: {[strategy_folder.name for strategy_folder in strategies_folder]}")

    all_values = []

    for strategy_folder in strategies_folder:
        strategy_name = strategy_folder.name
        search_pattern = f"{strategy_name}_*.json"
        logger.debug(f"Padrão de busca de arquivos: {search_pattern}")
        files_path = strategy_folder.glob(search_pattern)

        for file_path in files_path:
            with open(file_path, "r") as file:
                base_data = json.load(file)

            for user, user_data in base_data.items():
                if user == "server":
                    continue
                    
                for str_round in user_data.keys():
                    all_values.append(user_data[str_round][target_metric] / user_data[str_round]["trees_by_client"])
                    # if (int(str_round)+1) % 10 == 0:
                    #     logger.debug(f"Round: {str_round}, {user_data[str_round]["trees_by_client"]} árvores por cliente.")

    all_values = np.array(all_values)
    mean = np.mean(all_values)
    std = np.std(all_values)

    logger.info(f"{target_metric} por árvore: média {mean} desvio de {std}")

all_clients_mean_and_std_per_tree(
    target_metric="inference_time",
)
all_clients_mean_and_std_per_tree(
    target_metric="fit_time",
)
all_clients_mean_and_std(
    target_metric="inference_time"
)

# No round 39 foram 48 árvores por cliente.