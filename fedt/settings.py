import tomllib
from pathlib import Path
import importlib.resources as res

base_path = ""
base_path = Path(base_path).resolve()

config_path = (base_path / "fedt/config.toml").resolve()

with open(config_path, "rb") as file:
    config = tomllib.load(file)

results_folder = (base_path / config["paths"]["results_folder"]).resolve()
logs_folder = (base_path / config["paths"]["logs_folder"]).resolve()
scripts_folder = (base_path / config["paths"]["scripts_path"]).resolve()
client_script_path = (base_path / config["paths"]["client_script_path"]).resolve()
dataset_path = (base_path / config["paths"]["dataset_path"]).resolve()

number_of_jobs = config["settings"]["number_of_jobs"]
number_of_clients = config["settings"]["number_of_clients"]
number_of_rounds = config["settings"]["number_of_rounds"]
imported_aggregation_strategy = config["settings"]["aggregation_strategy"]

number_of_simulations = config["settings"]["sequence"]["number_of_simulations"]
aggregation_strategies = config["settings"]["sequence"]["aggregation_strategies"]

client_timeout = config["settings"]["client"]["timeout"]
client_debug = config["settings"]["client"]["debug"]

server_config = config["settings"]["server"]
server_ip = config["settings"]["server"]["IP"]
server_port = config["settings"]["server"]["port"]
validate_dataset_size = config["settings"]["server"]["validate_dataset_size"]

train_test_split_size = config["dataset"]["train_test_split_size"]
percentage_value_of_samples_per_client = config["dataset"]["percentage_value_of_samples_per_client"]

network_interface = config["scripts"]["network_interface"]