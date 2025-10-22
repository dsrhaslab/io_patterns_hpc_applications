from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import logging
import os
import sys


def evaluate_model(num_predictions, true_seqs, pred_seqs):
    # Store metric values per position
    precision_scores = []
    recall_scores = []
    f1_scores = []
    accuracy_scores = []

    # Convert true and predicted sequences into column-wise lists
    true_by_pos = [[] for _ in range(num_predictions)]
    pred_by_pos = [[] for _ in range(num_predictions)]

    for true_seq, pred_seq in zip(true_seqs, pred_seqs):
        for i in range(num_predictions):
            if i < len(true_seq) and i < len(pred_seq):
                true_by_pos[i].append(true_seq[i])
                pred_by_pos[i].append(pred_seq[i])

    # Calculate metrics
    for i in range(num_predictions):
        y_true = true_by_pos[i]
        y_pred = pred_by_pos[i]

        precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
        recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
        f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
        accuracy = accuracy_score(y_true, y_pred)

        accuracy_scores.append(accuracy)
        precision_scores.append(precision)
        recall_scores.append(recall)
        f1_scores.append(f1)

    return accuracy_scores, precision_scores, recall_scores, f1_scores



def evaluate_burst(true_values, predictions, output_folder, debug):

    mae = mean_absolute_error(true_values, predictions)
    rmse = np.sqrt(mean_squared_error(true_values, predictions))
    r2 = r2_score(true_values, predictions)

    if debug:
        logging.info(f"\nEvaluation Metrics:")
        logging.info(f"MAE:  {mae:.4f}")
        logging.info(f"RMSE: {rmse:.4f}")
        logging.info(f"R²:   {r2:.4f}")

    # Save metrics
    os.makedirs(output_folder, exist_ok=True)
    with open(os.path.join(output_folder, 'regression_metrics.txt'), 'w') as f:
        f.write(f"MAE: {mae:.4f}\n")
        f.write(f"RMSE: {rmse:.4f}\n")
        f.write(f"R2: {r2:.4f}\n")

    # Plot true vs predicted
