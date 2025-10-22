from setup_environment import *
from data_gathering import *
from data_preprocessing import *
from data_visualization import *
from model_evaluation import *

import argparse
import sys
import logging
from autogluon.tabular import TabularPredictor
from autogluon.multimodal import MultiModalPredictor

############ Global constants ############

target_column = 'next_systemcalls'

############ Data loading and preprocessing ############

def load_and_preprocess_data(base_dir, app, case, run, situation, debug,
                             type_enc, app_enc, label_enc, num_predictions, is_train=True):
    if is_train:
        data = load_training_data(base_dir, app, case, run, situation, debug, N, ALL_APPLICATIONS, type_enc, app_enc, label_enc)
    else:
        data = load_timeseries_data(base_dir, app, case, run, debug)
        data = preprocessing(data, N, type_enc, app_enc, label_enc)

    print(data.columns)
    print(data.info())
    first_rows(data)  

    if is_train:
        data[target_column] = [get_next_systemcalls(data, num_predictions, idx) for idx in range(len(data))]
    else:
        if 'new_path' not in data.columns:
            data['new_path'] = None
    return data


############ Model training ############

def train_model(train_data, target_column, situation):
    feature_cols = [col for col in train_data.columns if col != target_column]

    predictor = TabularPredictor(label=target_column, problem_type='multiclass').fit(
        train_data=train_data,
        presets='best_quality',
        num_bag_folds=0,
        num_stack_levels=0,
        excluded_model_types=['CAT', 'XGB', 'RF', 'GBM', 'XT', 'NN_TORCH', 'KNN'],
        time_limit=5000
    )

    return predictor, feature_cols


############ Model evaluation ############

def evaluate_and_plot(predictor, test_data, feature_cols, output_folder, num_predictions):
    predictions = predictor.predict(test_data[feature_cols])
    test_data[target_column] = [get_next_systemcalls(test_data, num_predictions, idx) for idx in range(len(test_data))]

    true_seqs = test_data[target_column]
    pred_seqs = predictions

    accuracy_scores, precision_scores, recall_scores, f1_scores = evaluate_model(num_predictions, true_seqs, pred_seqs)

    plot_metric(output_folder, accuracy_scores, "Accuracy", num_predictions)
    plot_metric(output_folder, precision_scores, "Precision", num_predictions)
    plot_metric(output_folder, recall_scores, "Recall", num_predictions)
    plot_metric(output_folder, f1_scores, "F1-Score", num_predictions)

    table_results(output_folder, accuracy_scores, precision_scores, recall_scores, f1_scores)


############ Main function ############

def main():
    parser = argparse.ArgumentParser(description='System Call Prediction Script')
    parser.add_argument('-a', '--application', type=str, required=True, help='Application name to test')
    parser.add_argument('-c', '--case', type=str, required=True, help='Case name to test')
    parser.add_argument('-r', '--run', type=int, required=True, help='Run number to test (1, 2, or 3)')
    parser.add_argument('-s', '--situation', type=str, required=True, help='only/app/all')
    parser.add_argument('-n', '--num_predictions', type=int, required=True, help='Number of the next systemcalls to predict')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output folder')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    app_base = args.application
    case_base = args.case
    run_base = args.run
    debug_base = args.debug
    situation_base = args.situation
    output_folder = args.output
    num_predictions = args.num_predictions

    configure_logging(output_folder, debug_base)
    sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)

    type_enc, app_enc, label_enc = create_encoders()

    train_data = load_and_preprocess_data(base_dir, app_base, case_base, run_base, situation_base, debug_base,
                                          type_enc, app_enc, label_enc, num_predictions, is_train=True)
    test_data = load_and_preprocess_data(base_dir, app_base, case_base, run_base, situation_base, debug_base,
                                         type_enc, app_enc, label_enc, num_predictions, is_train=False)

    print(train_data.columns)
    print(train_data.info())
    first_rows(train_data)

    print(train_data.isnull().sum())
    print(test_data.isnull().sum())

    print(train_data[target_column].head())
    print(train_data[target_column].apply(type).value_counts())

    # plot_correlation_matrix(train_data, output_folder)
    filter_columns_by_missing_values(train_data, threshold=85)

    predictor, feature_columns = train_model(train_data, target_column, situation_base)
    evaluate_and_plot(predictor, test_data, feature_columns, output_folder, num_predictions)


if __name__ == "__main__":
    main()
