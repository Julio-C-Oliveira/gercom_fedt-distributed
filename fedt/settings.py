import tomllib
from pathlib import Path

pyproject_path = "/home/julio/Documentos/gercom_fedt-distributed/pyproject.toml"

with open(pyproject_path, "rb") as file:
    config = tomllib.load(file)

results_folder = config["paths"]["results_folder"]
dataset_path = config["paths"]["dataset_path"]
client_script_path = config["paths"]["client_script_path"]

number_of_jobs = config["settings"]["number_of_jobs"]
number_of_clients = config["settings"]["number_of_clients"]
number_of_rounds = config["settings"]["number_of_rounds"]
aggregation_strategy = config["settings"]["aggregation_strategy"]

client_timeout = config["settings"]["client"]["timeout"]
client_debug = config["settings"]["client"]["debug"]

server_config = config["settings"]["server"]
server_ip = config["settings"]["server"]["IP"]
server_port = config["settings"]["server"]["port"]
validate_dataset_size = config["settings"]["server"]["validate_dataset_size"]

train_test_split_size = config["dataset"]["train_test_split_size"]
percentage_value_of_samples_per_client = config["dataset"]["percentage_value_of_samples_per_client"]