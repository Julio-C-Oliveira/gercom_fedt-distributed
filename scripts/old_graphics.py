from scripts.graphics import Settings
from fedt.settings import graphics_path

import pandas as pd
import matplotlib.pyplot as plt

def plot_fedt_metric(data, metric, file_name, y_label_name, centralize = False):
    base_strategy_name = "AVG MSE " if metric == "mse" else "AVG Pearson "

    plt.figure(figsize=Settings.small_figure_size)

    for strategy, strategy_name in zip([
        f"{base_strategy_name}FedT_Random_Trees", 
        f"{base_strategy_name}FedT_Best Trees", 
        f"{base_strategy_name}FedT_Threshould", 
        f"{base_strategy_name}FedT_Best Forests"
        ], Settings.marker_styles.keys()):

        plt.plot(
            data["Rounds"],
            data[strategy],
            label=Settings.legend_dict[strategy_name],
            color=Settings.colors[strategy_name],
            marker=Settings.marker_styles[strategy_name],
            markersize=Settings.markersize,
            markevery=Settings.marker_spacing,
            markeredgecolor=Settings.border_color,
            markeredgewidth=Settings.border_weight,
            linewidth=Settings.line_size
        )

    plt.plot(
        data["Rounds"],
        data[f"{base_strategy_name}FedAVG"],
        label="FedAVG",
        color="r",
        marker="d",
        markersize=Settings.markersize,
        markevery=Settings.marker_spacing,
        markeredgecolor=Settings.border_color,
        markeredgewidth=Settings.border_weight,
        linewidth=Settings.line_size
    )

    if centralize:
        base_strategy_name = "MSE" if metric == "mse" else "Pearson"

        plt.plot(
            data["Rounds"],
            data[f"Centralized {base_strategy_name}"],
            label="Centralized Learning",
            color="c",
            linewidth=Settings.line_size+3,
            linestyle="--",
        )

    plt.xlabel("Rounds", fontsize=Settings.labels_fontsize, weight='bold')
    plt.ylabel(y_label_name, fontsize=Settings.labels_fontsize, weight='bold')
    plt.xticks(fontsize=Settings.tricks_fontsize)
    plt.yticks(fontsize=Settings.tricks_fontsize)
    plt.legend(fontsize=Settings.legend_fontsize)
    plt.grid(True, alpha=Settings.grid_alpha)
    plt.tight_layout()
    plt.savefig(f"{graphics_path}/old_{file_name}.pdf", format="pdf", dpi=300)
    plt.close()

plot_fedt_metric(
    data=pd.read_csv("/home/juliocoliveira/Julio/Gercom/FedT_Distribuido/gercom_fedt-distributed/resultados.csv"),
    metric="mse",
    file_name="squared_error",
    y_label_name="Average Mean Sqared Error"
)

plot_fedt_metric(
    data=pd.read_csv("/home/juliocoliveira/Julio/Gercom/FedT_Distribuido/gercom_fedt-distributed/resultados.csv"),
    metric="pearson",
    file_name="pearson_corr",
    y_label_name="Average Pearson Correlaion",
    centralize=True
)