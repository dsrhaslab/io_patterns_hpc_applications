import os
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import seaborn as sns
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import pandas as pd


# Function to plot correlation matrix for numeric columns
def plot_correlation_matrix(base_data, output_dir, corr_threshold=0):
    # Select numeric columns
    numeric_columns = base_data.select_dtypes(include=['float64', 'int64']).columns
    
    # Check if there are any numeric columns
    if numeric_columns.empty:
        print("No numeric columns to plot correlation matrix.")
        return
    
    # Calculate the correlation matrix
    corr_matrix = base_data[numeric_columns].corr()
    
    # Apply threshold to filter only strong correlations
    mask = (corr_matrix >= corr_threshold) | (corr_matrix <= -corr_threshold)
    filtered_corr_matrix = corr_matrix.where(mask, other=0)
    
    # Plot the heatmap with adjustments
    plt.figure(figsize=(20, 16))
    sns.heatmap(filtered_corr_matrix, annot=False, fmt=".2f", cmap='coolwarm', square=True, 
                cbar_kws={"shrink": 0.7}, linewidths=0.5)
    plt.title("Correlation Matrix (Thresholded)", fontsize=18)
    plt.xticks(rotation=90, ha='center', fontsize=10)
    plt.yticks(fontsize=10)
    plt.savefig(os.path.join(output_dir, 'correlation_matrix.png'))
    plt.close()



# Function to filter columns by missing values and display the desired outputs
def filter_columns_by_missing_values(base_data, threshold):
    # Calculate the percentage of missing values for each column
    missing_percentage = base_data.isnull().mean()

    # Get columns with 0% missing values
    zero_missing = missing_percentage[missing_percentage == 0]
    zero_missing_list = zero_missing.index.tolist()

    # Get columns with more than 85% missing values
    high_missing = missing_percentage[missing_percentage > threshold]
    high_missing_list = high_missing.index.tolist()

    # Print the results
    print("Columns with 0% Missing Values:", zero_missing_list)
    print(f"Columns with >{threshold} Missing Values:", high_missing_list)


def plot_distribution(base_data, output_dir):
    """Plot distribution for a numerical column."""

    for column in base_data.select_dtypes(include=['float64', 'int64']).columns:
        plt.figure(figsize=(10, 6))
        sns.histplot(base_data[column].dropna(), kde=True)
        plt.title(f'Distribution of {column}')
        plt.xlabel(column)
        plt.ylabel('Frequency')
        plt.show()
        plt.savefig(os.path.join(output_dir, f'distribution_of_{column}.png'))
        plt.close()


def evaluation_metrics(y_true, y_pred):
    # Calculate evaluation metrics only if lengths match
    if len(y_true) == len(y_pred):
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average='weighted')
        recall = recall_score(y_true, y_pred, average='weighted')
        f1 = f1_score(y_true, y_pred, average='weighted')

        print(f'Accuracy: {accuracy:.2f}')
        print(f'Precision: {precision:.2f}')
        print(f'Recall: {recall:.2f}')
        print(f'F1 Score: {f1:.2f}')
    else:
        print("Error: The lengths of y_true and y_pred do not match.")


# Check the shapes
def shape(df):
    print(f"Shape of {df}:", df.shape)


# Check the first few rows of both DataFrames
def first_rows(df):
    print(f"Test {df}")
    print(df.head())


# 1. Confusion Matrix for Each Label
def matrix_for_label(output_dir, num_predictions, test_labels_df, predicted_labels_df, label_encoder):
    for i in range(num_predictions):
        true_labels = test_labels_df.iloc[:, i].values  # Actual labels
        predicted_labels = predicted_labels_df.iloc[:, i].values  # Predicted labels for the current label

        # Create confusion matrix
        conf_matrix = confusion_matrix(true_labels, predicted_labels)
        plt.figure(figsize=(10, 7))
        sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=label_encoder.classes_, yticklabels=label_encoder.classes_)
        plt.title(f'Confusion Matrix for Label {i}')
        plt.xlabel('Predicted')
        plt.ylabel('True')
        plt.savefig(os.path.join(output_dir, f'confusion_matrix_label_{i}.png'))
        plt.close()


# 2. Visualize True Labels vs Predictions for Each Label in Separate Graphs
def true_vs_predictions_labels(output_dir, N, num_predictions, predicted_labels_df, test_data, test_labels_df):
    for i in range(num_predictions):
        plt.figure(figsize=(12, 6))

        # Ensure that the relative_time is sliced correctly
        plt.plot(test_data['relative_time'].iloc[N:N + len(test_labels_df)], test_labels_df.iloc[:, i], label='True Labels', alpha=0.5)

        # Predictions should also match the same length
        plt.plot(test_data['relative_time'].iloc[N:N + len(test_labels_df)], predicted_labels_df.iloc[:, i], label='Predictions', alpha=0.5)

        plt.title(f'True Labels vs Predictions for Label {i}')
        plt.xlabel('Relative Time (seconds)')
        plt.ylabel('System Call Encoded')
        plt.legend()

        # Save each plot with a unique filename
        plt.savefig(os.path.join(output_dir, f'true_vs_predictions_label_{i}.png'))
        plt.close()


# 3. System Call Distribution Comparison (Train vs Test)
def system_call_distribution_comparison(output_dir, train_data, test_data):
    plt.figure(figsize=(14, 6))
    plt.subplot(1, 2, 1)
    train_data['systemcall'].value_counts().plot(kind='bar', color='blue', alpha=0.7)
    plt.title('System Call Distribution - Training Data')
    plt.ylabel('Frequency')

    plt.subplot(1, 2, 2)
    test_data['systemcall'].value_counts().plot(kind='bar', color='red', alpha=0.7)
    plt.title('System Call Distribution - Test Data')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'system_call_distribution.png'))
    plt.close()


def plot_accuracy(output_dir, accuracies):
    plt.figure(figsize=(8, 5))
    plt.plot(range(1, 6), accuracies, marker='o')
    plt.title("Prediction Accuracy vs. Number of System Calls Predicted")
    plt.xlabel("Number of System Calls")
    plt.ylabel("Accuracy")
    plt.xticks(range(1, 6))
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'accuracy_results.png'))
    plt.close()


def plot_metric(output_dir, values, metric_name, N):
    plt.figure(figsize=(8, N))
    plt.plot(range(1, N+1), values, marker='o')
    plt.title(f"{metric_name} vs. Number of System Calls Predicted")
    plt.xlabel("Number of System Calls")
    plt.ylabel(metric_name)
    plt.xticks(range(1, N+1))
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{metric_name.lower()}_results.png'))
    plt.close()


def table_results(output_dir, accuracies, precision_scores, recall_scores, f1_scores):
    

    print(accuracies)
    print(precision_scores)
    print(recall_scores)
    print(f1_scores)
    
    # Create the table
    metrics_table = pd.DataFrame({
        'Position': [f'next_{i+1}' for i in range(len(accuracies))],
        'Accuracy': accuracies,
        'Precision': precision_scores,
        'Recall': recall_scores,
        'F1-Score': f1_scores
    })

    print(metrics_table)

    # Save as CSV
    metrics_table_path = os.path.join(output_dir, 'metrics_summary.csv')
    metrics_table.to_csv(metrics_table_path, index=False)

    # Pretty print to console
    print("\n=== Metrics Summary Table ===")
    print(metrics_table.to_string(index=False, float_format="%.4f"))


def drop_trailing_9999(true_values):
    last_valid_idx = len(true_values)
    for i in range(len(true_values) - 1, -1, -1):
        if true_values[i] < 5000:
            last_valid_idx = i + 1
            break
    return true_values[:last_valid_idx]


def true_vs_predicted_next_brust(output_dir, true_values, predictions, time_threshold):
    os.makedirs(output_dir, exist_ok=True)

    true_values = drop_trailing_9999(true_values)
    predictions = drop_trailing_9999(predictions)

    min_len = min(len(true_values), len(predictions))
    true_values = true_values[:min_len]
    predictions = predictions[:min_len]


    time_windows = [i * time_threshold for i in range(len(true_values))]

    fig, axs = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

    # True values plot
    axs[0].plot(time_windows, true_values, label='True', color='green', marker='o')
    axs[0].set_title('True Time to Next Burst')
    axs[0].set_xlabel('Time Window')
    axs[0].set_ylabel('Seconds to Next Burst')
    axs[0].grid(True)

    # Predicted values plot
    axs[1].plot(time_windows, predictions, label='Predicted', color='blue', marker='x')
    axs[1].set_title('Predicted Time to Next Burst')
    axs[1].set_xlabel('Time Window')
    axs[1].grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'true_vs_predicted_bursts_side_by_side.png'))
    plt.close()


def save_decoded_matrix(decoded_matrix, output_folder, type_matrix):
    # Save CSV
    csv_path = os.path.join(output_folder, f"decoded_matrix_{type_matrix}.csv")
    decoded_matrix.to_csv(csv_path, index=False)
    print(f"Saved decoded matrix CSV to {csv_path}")



def save_predictions_csv(test_data, predictions, output_dir, label_enc):
    # test_data: DataFrame with a 'relative_time' column
    # predictions: list of lists, each inner list with predicted system calls

    # Parse the comma-separated strings into lists of integers
    parsed_predictions = predictions.apply(lambda x: list(map(int, x.split(','))))

    # Decode all IDs to system call names
    decoded_predictions = parsed_predictions.apply(label_enc.inverse_transform)

    # Create dict for DataFrame columns
    data_dict = {'relative_time': test_data['relative_time'].values}

    first_rows(predictions)

    # Add pred_0, pred_1, ... pred_N columns
    num_preds = len(parsed_predictions.iloc[0])  # number of predicted calls per row
    for i in range(num_preds-1):
        data_dict[f'pred_{i}'] = decoded_predictions.apply(lambda pred: pred[i])

    pred_df = pd.DataFrame(data_dict)
    # pred_df.to_csv(os.path.join(output_dir, 'predicitons_results.csv'), index=False)

    save_decoded_matrix(pred_df, output_dir, "predictions")

    return pred_df


def plot_syscall_followups(decoded_matrix, syscall_name, output_folder, matrix):
    
    # Filter rows where input is the target syscall
    filtered = decoded_matrix[decoded_matrix['pred_0'] == syscall_name]

    if filtered.empty:
        print(f"No occurrences of syscall '{syscall_name}' found.")
        return

    # Collect prediction columns
    pred_cols = [col for col in decoded_matrix.columns if col.startswith('pred_') and col != 'pred_0']

    # Set up plotting
    num_preds = len(pred_cols)
    fig, axes = plt.subplots(1, num_preds, figsize=(4 * num_preds, 5), sharey=True)

    if num_preds == 1:
        axes = [axes]

    for i, col in enumerate(pred_cols):
        value_counts = filtered[col].value_counts(normalize=True).sort_values(ascending=False) * 100
        sns.barplot(x=value_counts.index, y=value_counts.values, ax=axes[i])
        axes[i].set_title(f'{col} after "{syscall_name}"')
        axes[i].set_ylabel('Percentage')
        axes[i].tick_params(axis='x', rotation=90)

    plt.tight_layout()
    os.makedirs(output_folder, exist_ok=True)
    plot_path = os.path.join(output_folder, f'syscall_followups_{syscall_name}_{matrix}.png')
    plt.savefig(plot_path)
    plt.close()

    print(f"Saved plot to {plot_path}")


def get_unique_next10_sequences(decoded_matrix, type_matrix, output_folder):
    # Get all columns starting with 'pred_' except 'pred_0'
    pred_cols = sorted([col for col in decoded_matrix.columns if col.startswith('pred_') and col != 'pred_0'])
    
    unique_sequences = set()

    res_path = os.path.join(output_folder, f"unique_next10_{type_matrix}.txt")

    for _, row in decoded_matrix.iterrows():
        # Extract the next 10 system calls as a tuple (or list)
        next10 = tuple(row[col] for col in pred_cols)
        unique_sequences.add(next10)

    with open(res_path, 'w') as f:
        for seq in sorted(unique_sequences):
            f.write(f"{seq}\n")
    
    return unique_sequences