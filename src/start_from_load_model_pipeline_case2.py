from setup_environment import *
from data_gathering import *
from data_preprocessing import *
from data_visualization import *
from model_evaluation import *

import argparse
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
import sys
import logging
from autogluon.tabular import TabularPredictor
from autogluon.multimodal import MultiModalPredictor
from fastai.learner import load_learner


############ Global constants ############

target_column = 'next_systemcalls'


############ Data loading and preprocessing ############

def load_and_preprocess_data(base_dir, app, case, run, situation, debug,
                             type_enc, app_enc, label_enc, num_predictions, is_train=True):
    if is_train:
        data = load_training_data(base_dir, app, case, run, situation, debug, ALL_APPLICATIONS)
    else:
        data = load_timeseries_data(base_dir, app, case, run, debug)

    first_rows(data)

    data = preprocessing(data, N, type_enc, app_enc, label_enc)

    if is_train:
        data[target_column] = [get_next_systemcalls(data, num_predictions, idx) for idx in range(len(data))]
    else:
        if 'new_path' not in data.columns:
            data['new_path'] = None
    return data


############ Model evaluation ############

def evaluate_and_plot(predictor, test_data, feature_cols, output_folder, num_predictions, label_enc):
    predictions = predictor.predict(test_data[feature_cols])
    #predictions = learner.get_preds(dl=test_data[feature_cols])
    test_data[target_column] = [get_next_systemcalls(test_data, num_predictions, idx) for idx in range(len(test_data))]

    true_seqs = test_data[target_column]
    pred_seqs = predictions

    accuracy_scores, precision_scores, recall_scores, f1_scores = evaluate_model(num_predictions, true_seqs, pred_seqs)

    plot_metric(output_folder, accuracy_scores, "Accuracy", num_predictions)
    plot_metric(output_folder, precision_scores, "Precision", num_predictions)
    plot_metric(output_folder, recall_scores, "Recall", num_predictions)
    plot_metric(output_folder, f1_scores, "F1-Score", num_predictions)

    table_results(output_folder, accuracy_scores, precision_scores, recall_scores, f1_scores)
    
    pred_df = save_predictions_csv(test_data, predictions, output_folder, label_enc)
    type_matrix =  "predictions"
    for call in ALL_SYSTEMCALLS:
        plot_syscall_followups(pred_df, call, output_folder, type_matrix)

    print("Get unique next 10 sequences")
    unique_next10_seqs = get_unique_next10_sequences(pred_df, type_matrix, output_folder)

############ Main function ############

def main():
    parser = argparse.ArgumentParser(description='System Call Prediction Script')
    parser.add_argument('-a', '--application', type=str, required=True, help='Application name to test')
    parser.add_argument('-c', '--case', type=str, required=True, help='Case name to test')
    parser.add_argument('-r', '--run', type=int, required=True, help='Run number to test (1, 2, or 3)')
    parser.add_argument('-s', '--situation', type=str, required=True, help='only/app/all')
    parser.add_argument('-n', '--num_predictions', type=int, required=True, help='Number of the next systemcalls to predict')
    parser.add_argument('-m', '--model', type=str, required=True, help='Model to load')
    parser.add_argument('-w',  '--warm_up', type=int, required=True, help='Warm up time to be disconsidered on the test dataset (in seconds)')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output folder')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    app_base = args.application
    case_base = args.case
    run_base = args.run
    debug_base = args.debug
    situation_base = args.situation
    model_base = args.model
    warm_up = args.warm_up
    output_folder = args.output
    num_predictions = args.num_predictions

    configure_logging(output_folder, debug_base)
    sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)

    type_enc, app_enc, label_enc = create_encoders()
    
    test_data = load_and_preprocess_data(base_dir, app_base, case_base, run_base, situation_base, debug_base,
                                         type_enc, app_enc, label_enc, num_predictions, is_train=False)

    train_data = load_and_preprocess_data(base_dir, app_base, case_base, run_base, situation_base, debug_base,
                                          type_enc, app_enc, label_enc, num_predictions, is_train=True)

    print(test_data.isnull().sum())

    feature_columns = [col for col in test_data.columns if col != target_column]
    predictor = TabularPredictor.load(models_dir+model_base)

    # Filter out the warm-up period using relative_time
    df_filtered = test_data[test_data['relative_time'] >= warm_up]

    evaluate_and_plot(predictor, test_data, feature_columns, output_folder, num_predictions, label_enc)
        


if __name__ == "__main__":
    main()
