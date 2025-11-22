from fedt.settings import logs_folder
from fedt.utils import setup_logger

import logging

logger = setup_logger(
    name="UNIFY_RESULTS",
    log_file="unify_results.log",
    level=logging.INFO
)

cpu_and_ram_folder = logs_folder / "cpu_ram"
strategies_cpu_and_ram_folder = [path for path in cpu_and_ram_folder.iterdir() if path.is_dir()]

logger.info(f"Pastas encontradas: {[strategy_path.name for strategy_path in strategies_cpu_and_ram_folder]}")

for strategy_path in strategies_cpu_and_ram_folder:
    logger.warning(f"Iniciando a conversão dos dados de cpu e ram para a estrátegia: {strategy_path.name}")
    