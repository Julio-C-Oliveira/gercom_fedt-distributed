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
    intervalo = 1
    border_weight = 0.2
    marker_styles = {
        'random': 'd',
        'best_trees': 'o',
        'threshold': 'p',
        'best_forests': '^'
    }
    colors = {
        "random": "#1f77b4",
        "best_trees": "#9467bd",
        "threshold": "#d62728",
        "best_forests": "#2ca02c"
    }
    border_color = "white"
    small_figure_size = (8, 5)

    error_capsize = 3
    error_capthick=1

    error_bar_alpha = 0.5
    grid_alpha = 0.5

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

def server_mean_and_std_graphic(target_metric, file_name, y_label_name, compute_values_function):
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

        # Plot
        plt.plot(
            reference_rounds,
            final_mean,
            label=strategy_name,
            color=Settings.colors[strategy_name],
            marker=Settings.marker_styles[strategy_name],
            markersize=Settings.markersize,
            markevery=Settings.intervalo,
            markeredgecolor=Settings.border_color,
            markeredgewidth=Settings.border_weight,
            linewidth=Settings.line_size,
        )

        interval_error = Settings.intervalo
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
    zoom_loc1, zoom_loc2):

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

        # Plot
        ax.plot(
            reference_rounds,
            final_mean,
            label=strategy_name,
            color=Settings.colors[strategy_name],
            marker=Settings.marker_styles[strategy_name],
            markersize=Settings.markersize,
            markevery=Settings.intervalo,
            markeredgecolor=Settings.border_color,
            markeredgewidth=Settings.border_weight,
            linewidth=Settings.line_size,
        )

        interval_error = Settings.intervalo
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

            values.append(user_data[str_round][target_metric])

        means.append(np.mean(values))
        stds.append(np.std(values))

    return rounds, np.array(means), np.array(stds)
    
def all_clients_mean_and_std_graphic(target_metric, file_name, y_label_name):
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

        plt.plot(
            reference_for_rounds,
            final_mean,
            label=strategy_name,
            color=Settings.colors[strategy_name],
            marker=Settings.marker_styles[strategy_name],
            markersize=Settings.markersize,
            markevery=Settings.intervalo,
            markeredgecolor=Settings.border_color,
            markeredgewidth=Settings.border_weight,
            linewidth=Settings.line_size,
        )

        interval_error = Settings.intervalo
        x_marked = reference_for_rounds[::interval_error]
        y_marked = final_mean[::interval_error]
        std_marked = final_std[::interval_error]

        plt.errorbar(
            x_marked,
            y_marked,
            fmt='none',
            capsize=Settings.error_capsize,
            capthick=Settings.error_capthick,
            yerr=final_std,
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


server_mean_and_std_graphic_with_zoom(
    target_metric="aggregation_time",
    file_name="aggregation_time",
    y_label_name="Time in Seconds",
    compute_values_function=compute_server_values,
    zoom_width=2.1,
    zoom_height=0.8,
    zoom_loc="upper right",
    bbox_to_anchor=(0.99, 0.49),
    zoom_xlim=(35,39),
    zoom_ylim=(0,0.004),
    zoom_ticksize=13,
    zoom_loc1=3,
    zoom_loc2=4
)
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
#     y_label_name="Time in Seconds"
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
