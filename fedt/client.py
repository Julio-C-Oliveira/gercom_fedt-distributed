from fedt.settings import server_ip, server_port, number_of_rounds, client_timeout, client_debug

import grpc
from fedt import fedT_pb2
from fedt import fedT_pb2_grpc

import pickle
import tempfile

from sklearn.ensemble import RandomForestRegressor
from client_utils import HouseClient
import utils

import time

import argparse

import logging

##########################################################################
# Argumentos e configuração de logging:
##########################################################################
parse = argparse.ArgumentParser(description="FedT")
parse.add_argument(
    "--client-id",
    required=True,
    type=int,
    help="Client ID"
)

ID = parse.parse_args().client_id

log_level = logging.DEBUG if client_debug else logging.INFO

logger = utils.setup_logger(
    name=f"Client {ID}",
    log_file=f"fedt_client_{ID}.log",
    level=log_level
)

##########################################################################
# Funções auxiliares:
##########################################################################
def send_stream_trees(serialise_trees:bytes, client_ID:int):
    """
    ### Função:
    Enviar as árvores para o servidor de forma isolada por stream,
    enviar todas as árvores só de uma vez ocasiona vários erros devido ao tamanho do modelo.
    ### Args:
    - Serialise Trees: Lista de árvores em formato de bytes.
    - Client ID: O Identificador do cliente.
    ### Returns:
    - Message: Um objeto que contém a árvore e o ID do cliente.
    """
    message = fedT_pb2.Forest_CLient()
    message.client_ID = client_ID
    for tree in serialise_trees:
        message.serialised_tree = tree
        yield message 

##########################################################################
# Client:
##########################################################################
def run():
    with grpc.insecure_channel(f"{server_ip}:{server_port}") as channel:
        stub = fedT_pb2_grpc.FedTStub(channel)

        for round in range(number_of_rounds):

            request_settings = fedT_pb2.Request_Server()
            request_settings.client_ID = ID
            server_reply_settings = stub.get_server_settings(request_settings)
            trees_by_client = server_reply_settings.trees_by_client
            server_round = getattr(server_reply_settings, "current_round", None)

            logger.warning(f"Trees by client: {trees_by_client}, round: {round}")

            wait_start = time.time()
            while server_round is not None and server_round < round:
                logger.info(f"Servidor no round {server_round}, esperando atingir round {round}...")

                time.sleep(5)

                server_reply_settings = stub.get_server_settings(request_settings)
                server_round = server_reply_settings.current_round
                trees_by_client = server_reply_settings.trees_by_client
                if time.time() - wait_start > client_timeout:
                    raise RuntimeError(f"[Client {ID}] Timeout esperando servidor avançar do round {server_round} para {round}")

            request_model = fedT_pb2.Request_Server()
            request_model.client_ID = ID
            server_replies = stub.get_server_model(request_model)
            server_trees_serialised = []
            for server_reply in server_replies:
                server_trees_serialised.append(server_reply.serialised_tree)

            server_trees_deserialise = utils.deserialise_several_trees(server_trees_serialised)

            server_model = RandomForestRegressor(warm_start=True)
            data_valid, label_valid = utils.load_dataset_for_server()
            server_model.fit(data_valid, label_valid)
            server_model.estimators_ = server_trees_deserialise

            client = HouseClient(trees_by_client, ID)
            (absolute_error, squared_error, (pearson_corr, p_value), best_trees) = client.evaluate(server_model)

            logger.info(f"\nAbsolute Error: {absolute_error:.3f}\nSquared Error: {squared_error:.3f}\nPearson: {pearson_corr:.3f}")

            serialise_trees = utils.serialise_several_trees(client.trees)

            server_replies = stub.aggregate_trees(send_stream_trees(serialise_trees, ID))
            server_trees_serialised = []
            for reply in server_replies:
                server_trees_serialised.append(reply.serialised_tree)

            logger.info("Modelo global recebido")

            request_end = fedT_pb2.Request_Server()
            request_end.client_ID = ID
            server_reply = stub.end_of_transmission(request_end)

            server_trees_deserialised = utils.deserialise_several_trees(server_trees_serialised)
            server_model.estimators_ = server_trees_deserialised
            (absolute_error, squared_error, (pearson_corr, p_value), best_trees) = client.evaluate(server_model)

            logger.info(f"\nAbsolute Error: {absolute_error:.3f}\nSquared Error: {squared_error:.3f}\nPearson: {pearson_corr:.3f}")

            time.sleep(15)


if __name__ == "__main__":
    run()