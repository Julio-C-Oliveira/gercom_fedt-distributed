from fedt.settings import server_config, number_of_jobs, number_of_clients, aggregation_strategy

from concurrent import futures
import threading
import time
import datetime

from fedt import utils
from fedt.fedforest import FedForest

import grpc
from fedt import fedT_pb2
from fedt import fedT_pb2_grpc

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

import logging

import gc # pra controlar diretamente o garbage collector do python.

##########################################################################
# Configuração de logging:
##########################################################################
log_level = logging.DEBUG if server_config["debug"] else logging.INFO

logger = utils.setup_logger(
    name="SERVER",
    log_file="fedt_server.log",
    level=log_level
)

##########################################################################
# Funções auxiliares:
##########################################################################
def add_end_time(runtime_clients, ID, end_time):
    """
    Adiciona o tempo de término na lista de clientes em execução.
    """
    for i, (client_id, start_time) in enumerate(runtime_clients):
        if client_id == ID:
            runtime_clients[i] = (client_id, (start_time, end_time))
            break
    return runtime_clients

def sum_runtime(runtime_list):
    """Soma tempos de execução em segundos."""
    return sum(runtime_list)

def average_runtime(runtime_clients):
    """Calcula o tempo médio de execução."""
    runtime_list = [(end - start) for (_, (start, end)) in runtime_clients]
    runtime_sum = sum_runtime(runtime_list)
    runtime_average = runtime_sum / number_of_clients
    return runtime_average

##########################################################################
# Server:
##########################################################################

class FedT(fedT_pb2_grpc.FedTServicer):
    def __init__(self) -> None:
        super().__init__()
        self.round = 0

        self.model = RandomForestRegressor(n_estimators=self.get_number_of_trees_per_client())

        # [New]: Reduzindo pra um, tenho que limitar a profundidade à 3 também.
        # self.model = RandomForestRegressor(n_estimators=1)

        data_train, label_train = utils.load_dataset_for_server()
        utils.set_initial_params(self.model, data_train, label_train)

        self.global_trees = self.model.estimators_
        self.strategy = FedForest(self.model)

        # Variaveis de sincronização:
        self.lock = threading.Lock()
        self.round_condition = threading.Condition(self.lock)

        self.clientes_conectados = []
        self.clientes_esperados = number_of_clients
        self.clientes_respondidos = 0

        self.trees_warehouse = []
        
        self.aggregation_realised = 0

        self.runtime_clients = []
        self.runtime_average = 0
    
    def get_number_of_trees_per_client(self):
        return self.round * server_config["increase_of_trees_per_round"] + server_config["number_of_trees_in_start"]

    def aggregate_strategy(self, best_forests: list[RandomForestRegressor], threshold=server_config["pearson_threshold"]):
        match aggregation_strategy:
            case 'random':
                self.model.estimators_ = self.strategy.aggregate_fit_random_trees_strategy(best_forests)
            case 'best_trees':
                self.model.estimators_ = self.strategy.aggregate_fit_best_trees_strategy(best_forests)
            case 'threshold':
                self.model.estimators_ = self.strategy.aggregate_fit_best_trees_threshold_strategy(best_forests, threshold)
            case 'best_forests':
                self.model.estimators_ = self.strategy.aggregate_fit_best_forest_strategy(best_forests)
            case _:
                self.model.estimators_ = self.strategy.aggregate_fit_random_trees_strategy(best_forests)

    def aggregate_trees(self, request_iterator, context):
        """
        ### Função:
        Criar uma nova floresta com as árvores escolhidas, o critério de seleção depende do modod escolhido.
        ### Args:
        - Request: Mensagem do cliente, contém as árvores dele e o ID.
        - Context: Variável padrão da função gerada pelo gRPC.
        ### Returns:
        - Server Message: Contém as árvores selecionadas.
        """
        client_serialised_trees = []
        client_ID = None

        logger.info(f"Recebendo as árvores dos clientes, Round: {self.round}, Árvores por Cliente: {self.get_number_of_trees_per_client()}")

        for request in request_iterator:
            client_ID = request.client_ID
            client_serialised_trees.append(request.serialised_tree)
                
        client_trees = utils.deserialise_several_trees(client_serialised_trees)

        with self.round_condition:
            self.trees_warehouse.append((client_ID, client_trees))

            if client_ID not in self.clientes_conectados:
                self.clientes_conectados.append(client_ID)

            logger.debug(f"O cliente {client_ID} enviou {len(client_trees)} árvores.")

            start_wait = time.time()

            while len(self.clientes_conectados) < self.clientes_esperados:
                logger.info(f"Aguardando clientes ({len(self.clientes_conectados)}/{self.clientes_esperados})...")

                remaining = server_config["timeout"] - (time.time() - start_wait)

                if remaining <= 0:
                    logger.warning(f"Timeout esperando clientes para round {self.round}. Clientes recebidos: {len(self.clientes_conectados)}/{self.clientes_esperados}")
                    break

                self.round_condition.wait(timeout=remaining)

            if self.aggregation_realised == 0:
                self.aggregation_realised = 1
                # extrai floresta apenas das tuplas recebidas
                forests = [trees for (_, trees) in self.trees_warehouse]
                logger.warning(f"\nIniciando agregação do round {self.round}\nAgregação iniciada pelo cliente {client_ID}\nClientes: {len(self.clientes_conectados)}")
                try:
                    self.aggregate_strategy(forests)
                    logger.info(f"Agregação finalizada para round {self.round}.")
                except Exception as e:
                    logger.critical(f"Falha na agregação: {e}")
                finally:
                    self.aggregation_realised = 0
                    self.round_condition.notify_all()

            else:
                while self.aggregation_realised != 0:
                    self.round_condition.wait(timeout=5)

        serialised_global_trees = utils.serialise_several_trees(self.model.estimators_)
        number_of_trees = len(serialised_global_trees)
        number_of_sended_trees = 0

        server_reply = fedT_pb2.Forest_Server()
        for tree in serialised_global_trees:
            number_of_sended_trees += 1
            if number_of_sended_trees % server_config["print_every_trees_sent"] == 0:
                logger.info(f"Client ID: {client_ID}. Àrvore {number_of_sended_trees} de {number_of_trees} enviada.")
            server_reply.serialised_tree = tree
            yield server_reply

    def end_of_transmission(self, request, context):
        """
        ### Função:
        Avisar ao servidor que o processo já foi concluído e resetar o estado do server.
        ### Args:
        - Request: Mensagem de requisição que foi enviada pelo cliente, com o client ID.
        - Context: Variável padrão da função gerada pelo gRPC.
        ### Returns:
        - Server Message: Ok, confirmação de que a mensagem foi recebida.
        """
        end_time = time.time()
        self.runtime_clients = add_end_time(self.runtime_clients, request.client_ID, end_time)
        self.clientes_respondidos += 1

        logger.info(f"O cliente {request.client_ID} finalizou round. Clientes respondidos: {self.clientes_respondidos}/{number_of_clients}")

        if self.clientes_respondidos == number_of_clients:
            logger.info("Todos os clientes finalizaram.")

            for i in self.runtime_clients:
                logger.debug(f"Client ID: {i[0]} → tempo de execução: {time.strftime('%H:%M:%S', time.gmtime(i[1][1] - i[1][0]))}")

            logger.info(f"Tempo de Execução Médio: {time.strftime('%H:%M:%S', time.gmtime(average_runtime(self.runtime_clients)))}")
            time.sleep(5)
            self.reset_server()

            logger.warning(f"Round {self.round} finalizado")
            self.round += 1
            logger.warning(f"Round {self.round} iniciado")

        answer = fedT_pb2.OK()
        answer.ok = 1
        return answer
    
    def get_server_model(self, request, context):
        """
        ### Função:
        Obter as árvores que compõe o modelo de floresta do servidor.
        ### Args:
        - Request: Mensagem de requisição que foi enviada pelo cliente, com o client ID.
        - Context: Variável padrão da função gerada pelo gRPC.
        ### Returns:
        - Server Message: Árvores serializadas em bytes.
        """
        start_time = time.time()
        self.runtime_clients.append([request.client_ID, start_time])

        logger.info(f"Client ID: {request.client_ID}, requisitando o modelo do servidor.")

        trees = utils.get_model_parameters(self.model)
        serialised_trees = utils.serialise_several_trees(trees)
        server_message = fedT_pb2.Forest_Server()
        for serialise_tree in serialised_trees:
            server_message.serialised_tree = serialise_tree
            yield server_message
    
    def get_server_settings(self, request, context):
        """
        ### Função:
        Obter os parâmetros do ambiente.
        ### Args:
        - Request: Mensagem de requisição que foi enviada pelo cliente, com o client ID.
        - Context: Variável padrão da função gerada pelo gRPC.
        ### Returns:
        - Server Message: Contém o trees by client, váriavel que define o número de árvores por cliente.
        """
        logger.debug(f"Client ID: {request.client_ID}, solicitando as configurações.")
        server_reply = fedT_pb2.Server_Settings()
        server_reply.trees_by_client = self.get_number_of_trees_per_client()
        server_reply.current_round = self.round
        return server_reply
    
    def reset_server(self):
        """
        ### Função:
        Resetar o server, todas as váriaveis retornarão ao seu valor inicial.
        ### Args:
        - None
        ### Returns:
        - None
        """
        logger.warning("Resetando estado do servidor...")

        # [New]: Liberando os dados utilizados anteriormente.
        # del self.model, self.global_trees, self.strategy
        # gc.collect()

        self.model = RandomForestRegressor(n_estimators=self.get_number_of_trees_per_client())
        data_train, label_train = utils.load_dataset_for_server()
        utils.set_initial_params(self.model, data_train, label_train)

        self.global_trees = self.model.estimators_
        self.strategy = FedForest(self.model)

        self.clientes_conectados = []
        self.clientes_esperados = number_of_clients
        self.clientes_respondidos = 0
        self.trees_warehouse = []
        self.aggregation_realised = 0

        self.runtime_clients = []
        self.runtime_average = 0
    
def run_server():
    logger.info("Servidor inicializando...")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=number_of_jobs))
    fedT_pb2_grpc.add_FedTServicer_to_server(FedT(), server)
    server.add_insecure_port(f"{server_config["IP"]}:{server_config["port"]}")
    server.start()

    logger.info(f"Servidor ativo - {server_config['IP']}:{server_config['port']}")

    server.wait_for_termination()

if __name__ == "__main__":
    run_server()
