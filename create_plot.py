import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import argparse
import os

def parse_args():
    parser = argparse.ArgumentParser(description='System Call Prediction Plotting Script')
    parser.add_argument('-a', '--application', required=True, help='Application name')
    parser.add_argument('-c', '--case', required=True, help='Case name')
    parser.add_argument('-s', '--situation', required=True, help='Prediction situation (only/app/all)')
    parser.add_argument('-o', '--output', required=True, help='Output folder for plots')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()

def load_metrics(file_path, label):
    file = os.path.join(file_path, label, "metrics_summary.csv")
    return pd.read_csv(file)

def dynamic_ylim(data, padding=0.1):
    min_val, max_val = min(data), max(data)
    margin = (max_val - min_val) * padding if max_val != min_val else 0.01
    return max(0, min_val - margin), min(1, max_val + margin)

def plot_metric(steps, values, title, ylabel, colors, output_file):
    plt.figure(figsize=(14, 7))

    for i, (step, val, label, color) in enumerate(zip(steps, values, ['Next 1', 'Next 10', 'Next 100'], colors)):
        if i == 0:
            # Only first line has markers
            plt.plot(step, val, label=label, color=color, marker='o', linewidth=2, markersize=8)
        else:
            # Other lines without markers
            plt.plot(step, val, label=label, color=color, linewidth=2)

    # Apply larger fonts similar to your simple plot_metric function
    plt.title(title, fontsize=20, fontweight='bold', pad=20)
    plt.xlabel('Prediction Next Step', fontsize=20)
    plt.ylabel(ylabel, fontsize=20)
    plt.xticks(range(0, 101, 5), fontsize=18, color='dimgray')
    plt.yticks(fontsize=18, color='dimgray')
    plt.xlim(-5, 105)

    # Dynamic y-axis limits
    all_vals = [v for sublist in values for v in sublist]
    y_min, y_max = dynamic_ylim(all_vals)
    plt.ylim(y_min, y_max)

    plt.axhline(0, color='black', linestyle='--', linewidth=0.5)
    plt.axhline(0.5, color='red', linestyle='--', linewidth=0.5, label='Threshold (0.5)')
    plt.legend(fontsize=18)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)  # High-quality save
    plt.show()


def main():
    args = parse_args()

    base_path = os.path.join('../model_results', args.application, args.case, args.situation)

    if args.debug:
        print(f"[DEBUG] Base path: {base_path}")

    df_next1 = load_metrics(base_path, "next1")
    df_next10 = load_metrics(base_path, "next10")
    df_next100 = load_metrics(base_path, "next100")

    # Prepare data
    steps = [
        [1],
        list(range(1, 11)),
        list(range(1, 101))
    ]

    f1_scores = [
        [df_next1['F1-Score'].iloc[0]],
        df_next10['F1-Score'].tolist(),
        df_next100['F1-Score'].tolist()
    ]

    accuracies = [
        [df_next1['Accuracy'].iloc[0]],
        df_next10['Accuracy'].tolist(),
        df_next100['Accuracy'].tolist()
    ]

    sns.set(style="whitegrid")
    plot_metric(
        steps,
        f1_scores,
        title='F1-Score over Prediction Steps',
        ylabel='F1-Score',
        colors=sns.color_palette("Set2", 4),
        output_file=os.path.join(args.output, 'plot_f1_score.png')
    )

    plot_metric(
        steps,
        accuracies,
        title='Accuracy over Prediction Steps',
        ylabel='Accuracy',
        colors=sns.color_palette("Set1", 4),
        output_file=os.path.join(args.output, 'plot_accuracy.png')
    )

if __name__ == '__main__':
    main()
