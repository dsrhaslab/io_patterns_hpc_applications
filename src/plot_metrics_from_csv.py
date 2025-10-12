import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

# 🔧 Static output folder for all plots
OUTPUT_DIR = "plots"

def plot_metric(output_dir, values, metric_name, N):
    plt.figure(figsize=(8, N))
    plt.plot(range(1, N + 1), values, marker='o', linewidth=2)
    # No title
    plt.xlabel("Number of System Calls", fontsize=20)
    plt.ylabel(metric_name, fontsize=20)
    plt.xticks(range(1, N + 1), fontsize=18,  color='dimgray')
    plt.yticks(fontsize=18,  color='dimgray')
    plt.grid(True)
    plt.tight_layout()
    # plt.savefig(os.path.join(output_dir, f'{metric_name.lower()}_results.png'))
    plt.savefig(os.path.join(output_dir, f'{metric_name.lower()}_results.png'), dpi=300)
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Plot metrics from CSV results')
    parser.add_argument('-a', '--application', type=str, required=True, help='Application name to test')
    parser.add_argument('-s', '--situation', type=str, required=True, help='only/app/all')
    parser.add_argument('-c', '--case', type=str, required=True, help='Case name to test')
    parser.add_argument('-r', '--run', type=str, required=True, help='Run number to test')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Build CSV path
    csv_path = os.path.join(
        "../../model_results",
        args.application,
        args.case,
        args.situation,
        args.run,
        "metrics_summary.csv"
    )

    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found at: {csv_path}")
        return

    # Ensure output folder exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.debug:
        print(f"📂 Reading CSV from: {csv_path}")
        print(f"💾 Saving plots to: {OUTPUT_DIR}")

    # Load CSV
    df = pd.read_csv(csv_path)

    # Plot each metric
    for metric_name in df.columns:
        values = df[metric_name].values
        N = len(values)
        plot_metric(OUTPUT_DIR, values, metric_name, N)
        if args.debug:
            print(f"✅ Saved plot for metric: {metric_name}")

if __name__ == "__main__":
    main()
