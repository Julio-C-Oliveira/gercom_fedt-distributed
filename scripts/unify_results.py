from fedt.settings import final_results_folder, results_folder, logs_folder
from fedt.utils import setup_logger, create_strategy_result_folder
from glob import glob
import json
from pathlib import Path
import os

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

def unify_network_csv_data():
    # Pegar as informações de inicio e fim do round e pegar os pacotes correspondentes à esse momento, 
    #   após isso, separar em servidor e cliente, e dividir pelo número de clientes.
    #   
    pass

def unify_cpu_and_ram_data():
    pass

# unify_clients_and_server_data()
unify_network_csv_data()