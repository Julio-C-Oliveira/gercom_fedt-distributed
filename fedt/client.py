from fedt.settings import server_ip, server_port, number_of_rounds, client_timeout, client_debug

import grpc
from fedt import fedT_pb2
from fedt import fedT_pb2_grpc

import pickle
import tempfile

from sklearn.ensemble import RandomForestRegressor
from client_utils import HouseClient

from fedt import utils
from fedt.utils import format_time

import time

import argparse

import logging

import gc # pra controlar diretamente o garbage collector do python.

##########################################################################
# To-DO:
# [x] Tempo de treinamento das árvores.
# [x] Tempo de avaliação do modelo, global vs local.
# [x] Tempo de duração de um round.

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

        dataset = utils.load_house_client()

        for round in range(number_of_rounds):

            round_start_time = time.time()

            logger.warning(f"Round: {round}")

            request_settings = fedT_pb2.Request_Server()
            request_settings.client_ID = ID
            server_reply_settings = stub.get_server_settings(request_settings)
            trees_by_client = server_reply_settings.trees_by_client
            server_round = getattr(server_reply_settings, "current_round", None)

            logger.debug(f"Trees by client: {trees_by_client}.")

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

            # [New]: Removendo as árvores serializadas.
            del server_trees_serialised
            gc.collect()

            server_model = RandomForestRegressor(
                n_estimators=trees_by_client,
                max_depth=3,
                warm_start=True
            )

            server_model.fit(dataset[0], dataset[1])
            server_model.estimators_ = server_trees_deserialise

            fit_start_time = time.time()
            client = HouseClient(trees_by_client, dataset, ID)
            fit_time = time.time() - fit_start_time
            
            (absolute_error, squared_error, (pearson_corr, p_value), best_trees) = client.evaluate(server_model)

            logger.info(f"\nAbsolute Error: {absolute_error:.3f}\nSquared Error: {squared_error:.3f}\nPearson: {pearson_corr:.3f}")

            serialise_trees = utils.serialise_several_trees(client.trees)
            client_serialise_trees_size = utils.get_size_of_many_serialised_models(serialise_trees)
            logger.debug(f"Serialise Model Size Local Model in MB: {client_serialise_trees_size/(1024**2)}")

            server_replies = stub.aggregate_trees(send_stream_trees(serialise_trees, ID))
            server_trees_serialised = []
            for reply in server_replies:
                server_trees_serialised.append(reply.serialised_tree)

            # [New]: Excluir as árvores serializadas após enviar.
            del serialise_trees
            gc.collect()

            logger.info("Modelo global recebido")

            request_end = fedT_pb2.Request_Server()
            request_end.client_ID = ID
            server_reply = stub.end_of_transmission(request_end)

            server_trees_deserialised = utils.deserialise_several_trees(server_trees_serialised)
            server_model.estimators_ = server_trees_deserialised

            server_serialise_trees_size = utils.get_size_of_many_serialised_models(server_trees_serialised)
            logger.debug(f"Serialise Model Size Server Model in MB: {server_serialise_trees_size/(1024**2)}")

            evaluate_start_time = time.time()
            (absolute_error, squared_error, (pearson_corr, p_value), best_trees) = client.evaluate(server_model)
            evaluate_time = time.time() - evaluate_start_time

            logger.info(f"\nAbsolute Error: {absolute_error:.3f}\nSquared Error: {squared_error:.3f}\nPearson: {pearson_corr:.3f}")

            round_time = time.time() - round_start_time

            # Teste de inferência com apenas 100 amostras
            start_inference_time = time.time()
            client.evaluate_inference_time(100)
            inference_time = time.time() - start_inference_time

            logger.debug(f"\nDuração do Round: {format_time(round_time)}\nTempo de treinamento: {format_time(fit_time)}\nTempo de avaliação: {format_time(evaluate_time)}\nTempo de inferência: {format_time(inference_time)}")

            # [New]: Excluindo as árvores serializadas e resetando o cliente:
            del server_model, client, server_trees_serialised, server_trees_deserialised
            gc.collect()
            
            time.sleep(15)


if __name__ == "__main__":
    run()