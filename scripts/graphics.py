from fedt.settings import final_results_folder, graphics_path
from fedt.utils import setup_logger
from glob import glob
import logging
import json
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
import numpy as np

logger = setup_logger(
    name="GRAPHICS",
    log_file="graphics.log",
    level=logging.DEBUG
)

class Settings:
    labels_fontsize = 14
    tricks_fontsize = 13
    legend_fontsize = 13

    markersize = 7
    line_size = 2.5
    marker_spacing = 1
    border_weight = 0.2
    marker_styles = {
        'random': 'D', # Original: d
        'best_trees': 's', # Original: o 
        'threshold': 'o', # Original: p
        'best_forests': '>' # Original: ^ 
    }
    colors = {
        "random": "g", # Original: #1f77b4 
        "best_trees": "y", # Original: #9467bd 
        "threshold": "b", # Original: #d62728 
        "best_forests": "m" # Original: #2ca02c 
    }
    border_color = "white"
    small_figure_size = (8, 5)

    error_capsize = 3
    error_capthick = 1
    error_spacing = 2

    error_bar_alpha = 0.5
    grid_alpha = 0.5

    legend_dict = {
        "random" : "FEdT - Random Trees",
        "best_trees" : "FEdT - Best Trees",
        "threshold" : "FEdT - Best Trees w/ Threshold Cond.",
        "best_forests" : "FEdT - Best Forests"
    }

def compute_server_values(base_data, target_metric):
    server_data = base_data["server"]
    rounds = [int(r) for r in server_data.keys()]
    rounds.sort()

    values = []
    for r in rounds:
        str_r = str(r)
        values.append(server_data[str_r][target_metric])

    return rounds, np.array(values)
    
def compute_server_network_or_performance(base_data, target_metric):
    server_data = base_data["server"]
    rounds = [int(r) for r in server_data.keys()]
    rounds.sort()

    values = []
    for r in rounds:
        str_r = str(r)
        values.append(sum(server_data[str_r][target_metric]))

    return rounds, np.array(values)

def server_mean_and_std_graphic(target_metric, file_name, y_label_name, compute_values_function, shift = True):
    logger.warning(f"Gráfico: {file_name}")
    strategies_folder = [path for path in final_results_folder.iterdir() if path.is_dir()]
    logger.info(f"Estrátegias encontrados: {[strategy_folder.name for strategy_folder in strategies_folder]}")

    plt.figure(figsize=Settings.small_figure_size)

    for strategy_folder in strategies_folder:
        strategy_name = strategy_folder.name
        search_pattern = f"{strategy_name}_*.json"
        logger.debug(f"Padrão de busca de arquivos: {search_pattern}")
        files_path = strategy_folder.glob(search_pattern)

        all_sim_server_values = []
        reference_rounds = None

        for file_path in files_path:
            with open(file_path, "r") as file:
                base_data = json.load(file)

            rounds, server_values = compute_values_function(base_data, target_metric)

            if reference_rounds is None:
                reference_rounds = rounds
            else:
                if rounds != reference_rounds:
                    raise ValueError(f"Rounds inconsistentes em {file_path.name}")

            all_sim_server_values.append(server_values)

        all_sim_server_values = np.array(all_sim_server_values)   # shape = [num_sims, num_rounds]

        final_mean = np.mean(all_sim_server_values, axis=0)
        final_std = np.std(all_sim_server_values, axis=0)

        if shift:
            reference_rounds = [round+1 for round in reference_rounds]

        # Plot
        plt.plot(
            reference_rounds,
            final_mean,
            label=Settings.legend_dict[strategy_name],
            color=Settings.colors[strategy_name],
            marker=Settings.marker_styles[strategy_name],
            markersize=Settings.markersize,
            markevery=Settings.marker_spacing,
            markeredgecolor=Settings.border_color,
            markeredgewidth=Settings.border_weight,
            linewidth=Settings.line_size,
        )

        interval_error = Settings.error_spacing
        x_marked = reference_rounds[::interval_error]
        y_marked = final_mean[::interval_error]
        std_marked = final_std[::interval_error]

        plt.errorbar(
            x_marked,
            y_marked,
            yerr=std_marked,
            fmt='none',
            capsize=Settings.error_capsize,
            capthick=Settings.error_capthick,
            ecolor=Settings.colors[strategy_name],
            alpha=Settings.error_bar_alpha
        )

    plt.xlabel("Rounds", fontsize=Settings.labels_fontsize, weight='bold')
    plt.ylabel(y_label_name, fontsize=Settings.labels_fontsize, weight='bold')
    plt.xticks(fontsize=Settings.tricks_fontsize)
    plt.yticks(fontsize=Settings.tricks_fontsize)
    plt.legend(fontsize=Settings.legend_fontsize)
    plt.grid(True, alpha=Settings.grid_alpha)
    plt.tight_layout()
    plt.savefig(f"{graphics_path}/{file_name}.pdf", format="pdf", dpi=300)
    plt.close()

def server_mean_and_std_graphic_with_zoom(
    target_metric, file_name, y_label_name, 
    compute_values_function, 
    zoom_width, zoom_height, zoom_loc, bbox_to_anchor,
    zoom_xlim, zoom_ylim, zoom_ticksize,
    zoom_loc1, zoom_loc2,
    shift = True):

    logger.warning(f"Gráfico: {file_name}")
    strategies_folder = [path for path in final_results_folder.iterdir() if path.is_dir()]
    logger.info(f"Estrátegias encontrados: {[strategy_folder.name for strategy_folder in strategies_folder]}")

    fig, ax = plt.subplots(figsize=Settings.small_figure_size)

    axins = inset_axes(
        ax,
        width=zoom_width,
        height=zoom_height,
        loc=zoom_loc,
        bbox_to_anchor=bbox_to_anchor,
        bbox_transform=ax.transAxes
    )

    for strategy_folder in strategies_folder:
        strategy_name = strategy_folder.name
        search_pattern = f"{strategy_name}_*.json"
        logger.debug(f"Padrão de busca de arquivos: {search_pattern}")
        files_path = strategy_folder.glob(search_pattern)

        all_sim_server_values = []
        reference_rounds = None

        for file_path in files_path:
            with open(file_path, "r") as file:
                base_data = json.load(file)

            rounds, server_values = compute_values_function(base_data, target_metric)

            if reference_rounds is None:
                reference_rounds = rounds
            else:
                if rounds != reference_rounds:
                    raise ValueError(f"Rounds inconsistentes em {file_path.name}")

            all_sim_server_values.append(server_values)

        all_sim_server_values = np.array(all_sim_server_values)   # shape = [num_sims, num_rounds]

        final_mean = np.mean(all_sim_server_values, axis=0)
        final_std = np.std(all_sim_server_values, axis=0)

        if shift:
            reference_rounds = [round+1 for round in reference_rounds]

        # Plot
        ax.plot(
            reference_rounds,
            final_mean,
            label=Settings.legend_dict[strategy_name],
            color=Settings.colors[strategy_name],
            marker=Settings.marker_styles[strategy_name],
            markersize=Settings.markersize,
            markevery=Settings.marker_spacing,
            markeredgecolor=Settings.border_color,
            markeredgewidth=Settings.border_weight,
            linewidth=Settings.line_size,
        )

        interval_error = Settings.error_spacing
        x_marked = reference_rounds[::interval_error]
        y_marked = final_mean[::interval_error]
        std_marked = final_std[::interval_error]

        plt.errorbar(
            x_marked,
            y_marked,
            yerr=std_marked,
            fmt='none',
            capsize=Settings.error_capsize,
            capthick=Settings.error_capthick,
            ecolor=Settings.colors[strategy_name],
            alpha=Settings.error_bar_alpha
        )

        logger.debug(f"Reference rounds: {reference_rounds[-5:]}")
        logger.debug(f"Final mean: {final_mean[-5:]}")

        axins.plot(
            reference_rounds[-5:],
            final_mean[-5:],
            color=Settings.colors[strategy_name],
            linewidth=Settings.line_size,
        )

    axins.set_xlim(*zoom_xlim)
    axins.set_ylim(*zoom_ylim)
    axins.tick_params(axis='both', labelsize=zoom_ticksize)

    mark_inset(
        ax, axins,
        loc1=zoom_loc1,
        loc2=zoom_loc2,
        fc="none",
        ec="0.4",
        alpha=0.3
    )

    ax.set_xlabel("Rounds", fontsize=Settings.labels_fontsize, weight='bold')
    ax.set_ylabel(y_label_name, fontsize=Settings.labels_fontsize, weight='bold')
    ax.tick_params(axis='x', labelsize=Settings.tricks_fontsize)
    ax.tick_params(axis='y', labelsize=Settings.tricks_fontsize)

    ax.legend(fontsize=Settings.legend_fontsize)
    ax.grid(True, alpha=Settings.grid_alpha)

    plt.tight_layout()
    plt.savefig(f"{graphics_path}/{file_name}.pdf", format="pdf", dpi=300)
    plt.close()

def compute_mean_std_per_round(base_data, target_metric):
    rounds = [int(str_round) for str_round in base_data["client-id-0"].keys()]
    means, stds = [], []
    
    for round in rounds:
        str_round = str(round)
        values = []

        for user, user_data in base_data.items():
            if user == "server":
                continue
            
            metric_data = user_data[str_round][target_metric]
            
            if isinstance(metric_data, list):
                values.append(np.mean(metric_data) if metric_data else 0)
            else:
                values.append(metric_data)

        means.append(np.mean(values))
        stds.append(np.std(values))

    return rounds, np.array(means), np.array(stds)

def compute_server_mean_performance(base_data, target_metric):
    server_data = base_data["server"]
    rounds = [int(r) for r in server_data.keys()]
    rounds.sort()

    values = []
    for r in rounds:
        str_r = str(r)
        metric_data = server_data[str_r][target_metric]
        
        if isinstance(metric_data, list):
            values.append(np.mean(metric_data) if metric_data else 0)
        else:
            values.append(metric_data)

    return rounds, np.array(values)
    
def all_clients_mean_and_std_graphic(target_metric, file_name, y_label_name, skip_setup_round = False, shift = True):
    logger.warning(f"Gráfico: {file_name}")
    strategies_folder = [path for path in final_results_folder.iterdir() if path.is_dir()]
    logger.info(f"Estrátegias encontrados: {[strategy_folder.name for strategy_folder in strategies_folder]}")

    plt.figure(figsize=Settings.small_figure_size)

    for strategy_folder in strategies_folder:
        strategy_name = strategy_folder.name
        search_pattern = f"{strategy_name}_*.json"
        logger.debug(f"Padrão de busca de arquivos: {search_pattern}")
        files_path = strategy_folder.glob(search_pattern)

        means_per_simulation, stds_per_simulation = [], []
        reference_for_rounds = None

        for file_path in files_path:
            with open(file_path, "r") as file:
                base_data = json.load(file)

            rounds, means, stds = compute_mean_std_per_round(base_data, target_metric)

            if reference_for_rounds is None: reference_for_rounds = rounds
            else:
                if rounds != reference_for_rounds: 
                    logger.error(f"Os rounds possuem tamanhos distindos, {file_path.name}")
                    raise ValueError(f"Os rounds possuem tamanhos distindos, {file_path.name}")

            means_per_simulation.append(means)
            stds_per_simulation.append(stds)

        means_per_simulation = np.array(means_per_simulation)
        stds_per_simulation = np.array(stds_per_simulation)

        final_mean = np.mean(means_per_simulation, axis=0) 
        final_std = np.mean(stds_per_simulation, axis=0)

        logger.debug(f"Len: {len(final_mean)}, {len(final_std)}")

        if skip_setup_round:
            final_mean[0] = None
            final_std[0] = None

        if shift:
            reference_for_rounds = [round+1 for round in reference_for_rounds]

        plt.plot(
            reference_for_rounds,
            final_mean,
            label=Settings.legend_dict[strategy_name],
            color=Settings.colors[strategy_name],
            marker=Settings.marker_styles[strategy_name],
            markersize=Settings.markersize,
            markevery=Settings.marker_spacing,
            markeredgecolor=Settings.border_color,
            markeredgewidth=Settings.border_weight,
            linewidth=Settings.line_size,
        )

        interval_error = Settings.error_spacing
        x_marked = reference_for_rounds[::interval_error]
        y_marked = final_mean[::interval_error]
        std_marked = final_std[::interval_error]

        plt.errorbar(
            x_marked,
            y_marked,
            fmt='none',
            capsize=Settings.error_capsize,
            capthick=Settings.error_capthick,
            yerr=std_marked,
            ecolor=Settings.colors[strategy_name],
            alpha=Settings.error_bar_alpha
        )

    plt.xlabel("Rounds", fontsize=Settings.labels_fontsize, weight='bold')
    plt.ylabel(y_label_name, fontsize=Settings.labels_fontsize, weight='bold')
    plt.xticks(fontsize=Settings.tricks_fontsize)
    plt.yticks(fontsize=Settings.tricks_fontsize)
    plt.legend(fontsize=Settings.legend_fontsize)
    plt.grid(True, alpha=Settings.grid_alpha)
    plt.tight_layout()
    plt.savefig(f"{graphics_path}/{file_name}.pdf", format="pdf", dpi=300)
    plt.close()

def extract_resampled_metric(base_data, target_metric, user_type, num_points=50):
    """
    Extrai as métricas de lista e interpola para um tamanho padrão, 
    permitindo gerar uma linha de progresso do round (0% a 100%).
    """
    all_profiles = []
    
    if user_type == "server":
        users = ["server"]
    else:
        # Pega todos os IDs de clientes, ignorando o server
        users = [u for u in base_data.keys() if u != "server"]
        
    rounds = [r for r in base_data["server"].keys()]
    
    for r in rounds:
        for user in users:
            if user in base_data and r in base_data[user]:
                metric_data = base_data[user][r].get(target_metric, [])
                
                # Só processa se de fato for uma lista (amostras intra-round)
                if isinstance(metric_data, list) and len(metric_data) > 0:
                    # Mapeia as amostras originais num eixo de 0 a 100
                    old_x = np.linspace(0, 100, len(metric_data))
                    new_x = np.linspace(0, 100, num_points)
                    
                    # Interpola para sempre termos `num_points` elementos
                    resampled = np.interp(new_x, old_x, metric_data)
                    all_profiles.append(resampled)
    
    if not all_profiles:
        return np.zeros(num_points), np.zeros(num_points)
        
    # Média e desvio padrão intra-round para aquele arquivo/simulação específica
    return np.mean(all_profiles, axis=0), np.std(all_profiles, axis=0)

def intra_round_profile_graphic(target_metric, file_name, y_label_name, num_points=50):
    logger.warning(f"Gráfico Intra-Round: {file_name}")
    strategies_folder = [path for path in final_results_folder.iterdir() if path.is_dir()]
    
    plt.figure(figsize=Settings.small_figure_size)
    
    # Eixo X agora representa o progresso do round (0% a 100%)
    x_axis = np.linspace(0, 100, num_points)
    
    for strategy_folder in strategies_folder:
        strategy_name = strategy_folder.name
        files_path = list(strategy_folder.glob(f"{strategy_name}_*.json"))
        
        server_profiles = []
        clients_profiles = []
        
        for file_path in files_path:
            with open(file_path, "r") as file:
                base_data = json.load(file)
                
            # Extrai e reamostra dados do servidor e clientes
            s_mean, _ = extract_resampled_metric(base_data, target_metric, "server", num_points)
            server_profiles.append(s_mean)
            
            c_mean, _ = extract_resampled_metric(base_data, target_metric, "clients", num_points)
            clients_profiles.append(c_mean)
            
        # Consolida a média final de todas as simulações
        final_server_mean = np.mean(server_profiles, axis=0)
        final_server_std = np.std(server_profiles, axis=0)
        
        final_clients_mean = np.mean(clients_profiles, axis=0)
        final_clients_std = np.std(clients_profiles, axis=0)
        
        # Para evitar uma bagunça de barras de erro sobrepostas
        interval_error = max(1, num_points // 10)
        x_marked = x_axis[::interval_error]
        
        # ----- PLOT SERVIDOR -----
        plt.plot(
            x_axis, final_server_mean,
            label=f"Server - {Settings.legend_dict.get(strategy_name, strategy_name)}",
            color=Settings.colors[strategy_name],
            linestyle='-', # Linha Sólida
            marker=Settings.marker_styles[strategy_name],
            markersize=Settings.markersize,
            markevery=interval_error,
            markeredgecolor=Settings.border_color,
            markeredgewidth=Settings.border_weight,
            linewidth=Settings.line_size,
        )
        
        plt.errorbar(
            x_marked, final_server_mean[::interval_error], yerr=final_server_std[::interval_error],
            fmt='none', capsize=Settings.error_capsize, capthick=Settings.error_capthick,
            ecolor=Settings.colors[strategy_name], alpha=Settings.error_bar_alpha
        )
        
        # ----- PLOT CLIENTES -----
        plt.plot(
            x_axis, final_clients_mean,
            label=f"Clients - {Settings.legend_dict.get(strategy_name, strategy_name)}",
            color=Settings.colors[strategy_name],
            linestyle='--', # Linha tracejada
            marker=Settings.marker_styles[strategy_name],
            markersize=Settings.markersize,
            markevery=interval_error,
            markeredgecolor=Settings.border_color,
            markeredgewidth=Settings.border_weight,
            linewidth=Settings.line_size,
        )
        
        plt.errorbar(
            x_marked, final_clients_mean[::interval_error], yerr=final_clients_std[::interval_error],
            fmt='none', capsize=Settings.error_capsize, capthick=Settings.error_capthick,
            ecolor=Settings.colors[strategy_name], alpha=Settings.error_bar_alpha
        )

    plt.xlabel("Progresso do Round (%)", fontsize=Settings.labels_fontsize, weight='bold')
    plt.ylabel(y_label_name, fontsize=Settings.labels_fontsize, weight='bold')
    plt.xticks(fontsize=Settings.tricks_fontsize)
    plt.yticks(fontsize=Settings.tricks_fontsize)
    
    # Legenda fora do gráfico (abaixo) para comportar as 8 entradas sem cobrir a visualização
    plt.legend(fontsize=Settings.legend_fontsize - 2, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    plt.grid(True, alpha=Settings.grid_alpha)
    
    # bbox_inches='tight' garante que o PDF salve com a legenda extraída
    plt.savefig(f"{graphics_path}/{file_name}.pdf", format="pdf", dpi=300, bbox_inches="tight")
    plt.close()

def extract_resampled_user_metric(base_data, target_metric, user_id, num_points=50):
    """
    Extrai as métricas de lista de todos os rounds para UM usuário específico
    e interpola para gerar o perfil médio do round (0 a 100%).
    """
    user_profiles = []
    
    if user_id in base_data:
        rounds = base_data[user_id].keys()
        for r in rounds:
            metric_data = base_data[user_id][r].get(target_metric, [])
            
            # Só processa se for lista de amostras intra-round e não estiver vazia
            logger.critical(f"Número de samples: {len(metric_data)}")
            if isinstance(metric_data, list) and len(metric_data) > 0:
                old_x = np.linspace(0, 100, len(metric_data))
                new_x = np.linspace(0, 100, num_points)
                resampled = np.interp(new_x, old_x, metric_data)
                user_profiles.append(resampled)
                
    if not user_profiles:
        return np.zeros(num_points)
        
    # Média do comportamento do usuário no round para ESTA simulação específica
    return np.mean(user_profiles, axis=0)

def intra_round_user_profile_graphic(target_metric, file_name, y_label_name, strategy="all", num_points=50):
    logger.warning(f"Gráfico Intra-Round por Usuário: {file_name} | Estratégia: {strategy}")
    
    # 1. Filtra as pastas de acordo com a estratégia desejada
    all_strategy_folders = [path for path in final_results_folder.iterdir() if path.is_dir()]
    if strategy != "all":
        strategies_to_process = [p for p in all_strategy_folders if p.name == strategy]
        if not strategies_to_process:
            logger.error(f"Estratégia '{strategy}' não encontrada nas pastas de resultados.")
            return
    else:
        strategies_to_process = all_strategy_folders

    # 2. Agrupa os perfis por Usuário
    # Estrutura: {"server": [array_sim1, array_sim2...], "client-id-0": [array_sim1...]}
    user_profiles_across_runs = {}

    for strategy_folder in strategies_to_process:
        files_path = list(strategy_folder.glob(f"{strategy_folder.name}_*.json"))
        
        for file_path in files_path:
            with open(file_path, "r") as file:
                base_data = json.load(file)
                
            # Extrai os dados para cada usuário presente neste JSON
            for user_id in base_data.keys():
                if user_id not in user_profiles_across_runs:
                    user_profiles_across_runs[user_id] = []
                
                user_sim_profile = extract_resampled_user_metric(base_data, target_metric, user_id, num_points)
                user_profiles_across_runs[user_id].append(user_sim_profile)

    # 3. Plota os gráficos
    plt.figure(figsize=Settings.small_figure_size)
    x_axis = np.linspace(0, 100, num_points)
    interval_error = max(1, num_points // 10)
    x_marked = x_axis[::interval_error]

    # Paleta de cores e marcadores para os usuários (já que o Settings.colors era para estratégias)
    cmap = plt.get_cmap('tab10') 
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    
    # Ordenamos para garantir que o server e os clientes apareçam na mesma ordem sempre
    sorted_users = sorted(user_profiles_across_runs.keys())

    for idx, user_id in enumerate(sorted_users):
        profiles = user_profiles_across_runs[user_id]
        
        # Média e desvio final entre todas as simulações lidas (seja 1 estratégia ou 'all')
        final_mean = np.mean(profiles, axis=0)
        final_std = np.std(profiles, axis=0)
        
        color = cmap(idx % 10)
        marker = markers[idx % len(markers)]

        plt.plot(
            x_axis, final_mean,
            label=user_id.capitalize(),
            color=color,
            linestyle='-', # Linhas SEMPRE contínuas
            marker=marker,
            markersize=Settings.markersize,
            markevery=interval_error,
            markeredgecolor=Settings.border_color,
            markeredgewidth=Settings.border_weight,
            linewidth=Settings.line_size,
        )
        
        plt.errorbar(
            x_marked, final_mean[::interval_error], yerr=final_std[::interval_error],
            fmt='none', capsize=Settings.error_capsize, capthick=Settings.error_capthick,
            ecolor=color, alpha=Settings.error_bar_alpha
        )

    plt.xlabel("Progresso do Round (%)", fontsize=Settings.labels_fontsize, weight='bold')
    plt.ylabel(y_label_name, fontsize=Settings.labels_fontsize, weight='bold')
    plt.xticks(fontsize=Settings.tricks_fontsize)
    plt.yticks(fontsize=Settings.tricks_fontsize)
    
    # Posicionamento da legenda
    plt.legend(fontsize=Settings.legend_fontsize, loc="best")
    plt.grid(True, alpha=0.3)
    
    # Salva o arquivo incluindo no nome se foi 'all' ou o nome da estratégia
    final_file_name = f"{file_name}_{strategy}"
    plt.savefig(f"{graphics_path}/{final_file_name}.pdf", format="pdf", dpi=300, bbox_inches="tight")
    plt.close()

# Client metrics:
# "trees_by_client"
# "first_server_serialise_trees_size"
# "fit_time"
# "client_serialise_trees_size"
# "final_server_serialise_trees_size"
# "squared_error"
# "pearson_corr"
# "round_time"
# "round_start_time"
# "round_end_time"
# "evaluate_time"
# "inference_time"

# Server metrics:
# "trees_by_client"
# "aggregation_time"
# "avg_execution_time"

# Ambos:
# "send_data"
# "receive_data"
# "cpu_percent"
# "memory_mb"

# Locs:
# 1 = upper right
# 2 = upper left
# 3 = lower left
# 4 = lower right

if __name__ == "__main__":
    intra_round_profile_graphic(
        target_metric="cpu_percent",
        file_name="intra_round_cpu_percent",
        y_label_name="CPU Usage (%)",
        num_points=50
    )
    intra_round_profile_graphic(
        target_metric="memory_mb",
        file_name="intra_round_memory_mb",
        y_label_name="Memory Usage (MB)",
        num_points=50
    )
    intra_round_user_profile_graphic(
        target_metric="cpu_percent", 
        file_name="intra_round_cpu", 
        y_label_name="CPU Usage (%)", 
        strategy="all",
        num_points=50
    )
    intra_round_user_profile_graphic(
        target_metric="memory_mb", 
        file_name="intra_round_ram", 
        y_label_name="Memory Usage (MB)", 
        strategy="all",
        num_points=50
    )
    # server_mean_and_std_graphic_with_zoom(
    #     target_metric="aggregation_time",
    #     file_name="aggregation_time",
    #     y_label_name="Time in Seconds",
    #     compute_values_function=compute_server_values,
    #     zoom_width=2.1,
    #     zoom_height=0.8,
    #     zoom_loc="upper right",
    #     bbox_to_anchor=(0.99, 0.49),
    #     zoom_xlim=(36,39),
    #     zoom_ylim=(0,0.004),
    #     zoom_ticksize=13,
    #     zoom_loc1=3,
    #     zoom_loc2=4
    # )
    # server_mean_and_std_graphic(
    #     target_metric="send_data",
    #     file_name="send_data",
    #     y_label_name="Size in Bytes",
    #     compute_values_function=compute_server_network_or_performance
    # )
    # server_mean_and_std_graphic(
    #     target_metric="receive_data",
    #     file_name="receive_data",
    #     y_label_name="Size in Bytes",
    #     compute_values_function=compute_server_network_or_performance
    # )
    # server_mean_and_std_graphic(
    #     target_metric="cpu_percent",
    #     file_name="server_cpu_percent",
    #     y_label_name="CPU Usage (%)",
    #     compute_values_function=compute_server_mean_performance
    # )
    # server_mean_and_std_graphic(
    #     target_metric="memory_mb",
    #     file_name="server_memory_mb",
    #     y_label_name="Memory Usage (MB)",
    #     compute_values_function=compute_server_mean_performance
    # )
    # all_clients_mean_and_std_graphic(
    #     target_metric="cpu_percent",
    #     file_name="cpu_percent",
    #     y_label_name="CPU Usage (%)"
    # )
    # all_clients_mean_and_std_graphic(
    #     target_metric="memory_mb",
    #     file_name="memory_mb",
    #     y_label_name="Memory Usage (MB)"
    # )
    # all_clients_mean_and_std_graphic(
    #     target_metric="fit_time",
    #     file_name="fit_time",
    #     y_label_name="Time in Seconds"
    # )
    # all_clients_mean_and_std_graphic(
    #     target_metric="squared_error",
    #     file_name="squared_error",
    #     y_label_name="Mean Squared Error"
    # )
    # all_clients_mean_and_std_graphic(
    #     target_metric="pearson_corr",
    #     file_name="pearson_corr",
    #     y_label_name="Pearson Correlation"
    # )
    # all_clients_mean_and_std_graphic(
    #     target_metric="round_time",
    #     file_name="round_time",
    #     y_label_name="Time in Seconds",
    #     skip_setup_round=True
    # )
    # all_clients_mean_and_std_graphic(
    #     target_metric="evaluate_time",
    #     file_name="evaluate_time",
    #     y_label_name="Time in Seconds"
    # )
    # all_clients_mean_and_std_graphic(
    #     target_metric="inference_time",
    #     file_name="inference_time",
    #     y_label_name="Time in Seconds"
    # )
    # all_clients_mean_and_std_graphic(
    #     target_metric="trees_by_client",
    #     file_name="trees_by_client",
    #     y_label_name="Number of Trees per Client"
    # )
