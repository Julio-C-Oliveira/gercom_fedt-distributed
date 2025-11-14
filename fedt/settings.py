import tomllib
from pathlib import Path

pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"

with open(pyproject_path, "rb") as file:
    config = tomllib.load(file)

base_path = (pyproject_path.parent / config["paths"]["base_path"]).resolve()

results_folder = (base_path / config["paths"]["results_folder"]).resolve()
logs_folder = (base_path / config["paths"]["logs_folder"]).resolve()
client_script_path = (base_path / config["paths"]["client_script_path"]).resolve()
dataset_path = (base_path / config["paths"]["dataset_path"]).resolve()

number_of_jobs = config["settings"]["number_of_jobs"]
number_of_clients = config["settings"]["number_of_clients"]
number_of_rounds = config["settings"]["number_of_rounds"]
imported_aggregation_strategy = config["settings"]["aggregation_strategy"]

many_simulations = config["settings"]["sequence"]["many_simulations"]
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