from setup_environment import *
from data_gathering import *
from data_preprocessing import *
from data_visualization import *
from model_evaluation import *


from category_encoders import BinaryEncoder
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, OrdinalEncoder
from autogluon.tabular import TabularPredictor
import matplotlib.pyplot as plt
import argparse
import os
import sys
import pandas as pd
import logging


TARGET_COLUMN = 'seconds_to_next_burst'
BURST_THRESHOLD = 10000
RETRAIN_EVERY_N = 500  # Retrain after accumulating this many new samples
TIME_LIMIT_PER_TRAIN = 5000  # seconds per retrain


def load_and_preprocess_data(base_dir, app, case, run, situation, debug,
                             type_enc, app_enc, label_enc, is_train=True):
    if is_train:
        data = load_training_data(base_dir, app, case, run, situation, debug, N, ALL_APPLICATIONS, type_enc, app_enc, label_enc)
        data = preprocessing_aggregate(data, TIME_THRESHOLD, BURST_THRESHOLD, debug, True)
    else:
        data = load_timeseries_data(base_dir, app, case, run, debug)
        data = preprocessing_aggregate(data, TIME_THRESHOLD, BURST_THRESHOLD, debug, True)

    return data


def main(debug=True):
    
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


    # Load runs 1 & 2 for initial training
    train_df = load_and_preprocess_data(base_dir, app_base, case_base, run_base, situation_base, debug_base,
                                          type_enc, app_enc, label_enc, is_train=True)
    

    # Initialize predictor
    predictor = TabularPredictor(label=TARGET_COLUMN, problem_type='regression').fit(
        train_data=train_df,
        time_limit=TIME_LIMIT_PER_TRAIN
    )

    # Load run 3 for online testing
    test_df_full = load_and_preprocess_data(base_dir, app_base, case_base, run_base, situation_base, debug_base,
                                         type_enc, app_enc, label_enc, is_train=False)

    # Online loop
    accumulated_new_samples = []
    all_predictions = []
    true_values = []

    for idx, row in test_df_full.iterrows():
        X_row = row.drop(TARGET_COLUMN).to_frame().T
        y_true = row[TARGET_COLUMN]

        # Predict
        y_pred = predictor.predict(X_row).values[0]

        # Store for evaluation
        all_predictions.append(y_pred)
        true_values.append(y_true)

        # Add this new sample to retrain later
        accumulated_new_samples.append(row)

        if (len(accumulated_new_samples) >= RETRAIN_EVERY_N) or (idx == len(test_df_full) - 1):
            new_df = pd.DataFrame(accumulated_new_samples)
            if debug:
                logging.info(f"Retraining with {len(new_df)} new samples (step {idx})...")
            # Retrain predictor incrementally
            predictor = TabularPredictor(label=TARGET_COLUMN, problem_type='regression').fit(
                train_data=pd.concat([train_df, new_df]),
                time_limit=TIME_LIMIT_PER_TRAIN
            )
            # Append to training data
            train_df = pd.concat([train_df, new_df])
            accumulated_new_samples = []

    # Evaluate
    print("\nFINAL EVALUATION ON RUN 3:")
    print(true_values)
    print(all_predictions)

    evaluate_burst(true_values, all_predictions, output_folder, debug_base)
    true_vs_predicted_next_brust(output_folder, true_values, all_predictions, TIME_THRESHOLD)


if __name__ == "__main__":
    main()
