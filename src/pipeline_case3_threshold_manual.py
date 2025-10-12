from setup_environment import *
from data_gathering import *
from data_preprocessing import *
from data_visualization import *
from model_evaluation import *


from category_encoders import BinaryEncoder
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, OrdinalEncoder
from autogluon.tabular import TabularPredictor
from autogluon.timeseries import TimeSeriesPredictor
import matplotlib.pyplot as plt
import argparse
import os
import sys
import pandas as pd
import logging

############ Setup ############

target_column = 'seconds_to_next_burst'
BURST_THRESHOLD = 10000

############ Data loading and preprocessing ############

def load_and_preprocess_data(base_dir, app, case, run, situation, debug,
                             type_enc, app_enc, label_enc, is_train=True):
    if is_train:
        data = load_training_data(base_dir, app, case, run, situation, debug, N, ALL_APPLICATIONS, type_enc, app_enc, label_enc)
        data = preprocessing_aggregate(data, TIME_THRESHOLD, BURST_THRESHOLD, debug, True)
    else:
        data = load_timeseries_data(base_dir, app, case, run, debug)
        data = preprocessing(data, N, type_enc, app_enc, label_enc)

    return data


############ Model training ############

def train_model(train_data, target_column, situation, debug):
    
    feature_cols = [col for col in train_data.columns if col != target_column]
    if debug:
        logging.info(f"Feature collumns: {feature_cols}")

    predictor = TabularPredictor(label=target_column, problem_type='regression').fit(
        train_data=train_data,
        presets='high_quality',
        time_limit=5000
    )

    return predictor, feature_cols


############ Model Evaluation ############

def offline_testing(predictor, full_data, debug):

    if debug:
        logging.info("Started offline testing...")

    # Aggregate full data (not in training mode)
    X = preprocessing_aggregate(full_data, TIME_THRESHOLD, BURST_THRESHOLD, debug, is_train=False)

    # Make prediction for each window (each row of X)
    y_pred = predictor.predict(X)

    return y_pred



############ Main function ############

def main():
    parser = argparse.ArgumentParser(description='System Call Burst Prediction Script')
    parser.add_argument('-a', '--application', type=str, required=True, help='Application name to test')
    parser.add_argument('-c', '--case', type=str, required=True, help='Case name to test')
    parser.add_argument('-s', '--situation', type=str, required=True, help='only/app/all')
    parser.add_argument('-r', '--run', type=int, required=True, help='Run number to test (1, 2, or 3)')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output folder')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    app_base = args.application
    case_base = args.case
    run_base = args.run
    debug_base = args.debug
    situation_base = args.situation
    output_folder = args.output

    configure_logging(args.output, args.debug)
    sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)

    type_enc, app_enc, label_enc = create_encoders()

    train_data = load_and_preprocess_data(base_dir, app_base, case_base, run_base, situation_base, debug_base,
                                          type_enc, app_enc, label_enc, is_train=True)
    test_data = load_and_preprocess_data(base_dir, app_base, case_base, run_base, situation_base, debug_base,
                                         type_enc, app_enc, label_enc, is_train=False)

    save_decoded_matrix(train_data, output_folder, "train")

    predictor, feature_columns = train_model(train_data, target_column, situation_base, debug_base)
    
    predictions = offline_testing(predictor, test_data, debug_base)
    
    test_data_agg = preprocessing_aggregate(test_data, TIME_THRESHOLD, BURST_THRESHOLD, debug_base, True)
    true_values = test_data_agg[target_column].tolist()

    save_decoded_matrix(test_data_agg, output_folder, "true_values")
    
    time_windows = [i * TIME_THRESHOLD for i in range(len(predictions))]
    df = pd.DataFrame({
        "time_window": time_windows,
        "seconds_to_next_burst": predictions
    })
    # df["seconds_to_next_burst"] = df["seconds_to_next_burst"].round(2)
    save_decoded_matrix(df, output_folder, "predictions")

    evaluate_burst(true_values, predictions, output_folder, debug_base)
    true_vs_predicted_next_brust(output_folder, true_values, predictions, TIME_THRESHOLD)


if __name__ == "__main__":
    main()
