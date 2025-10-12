import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import argparse
import sys
import logging
import os

from setup_environment import *
from data_gathering import *
from data_preprocessing import *
from data_visualization import *
from model_evaluation import *


def prepare_encoded_matrix(app, case, run, situation, type_enc, app_enc, label_enc, num_predictions, debug, is_train):
    
    if is_train:
        data = load_training_data(base_dir, app, case, run, situation, debug, ALL_APPLICATIONS)
    else:
        data = load_timeseries_data(base_dir, app, case, run, debug)
    
    data = preprocessing(data, N, type_enc, app_enc, label_enc)
    data = data.sort_values(by='relative_time')

    if debug:
        logging.info("Build systemcall matrix")
    matrix = build_systemcall_matrix(data, num_predictions)
    matrix_values = matrix.values

    # Create flat array and mask of valid (non-NaN) positions
    flat_values = matrix_values.flatten()
    valid_mask = ~pd.isna(flat_values)

    # Decode only valid values
    valid_encoded = flat_values[valid_mask].astype(int)
    decoded_valid = label_enc.inverse_transform(valid_encoded)

    # Create an empty array and populate only the decoded values
    decoded_flat = np.full(flat_values.shape, '', dtype=object)
    decoded_flat[valid_mask] = decoded_valid

    # Reshape to original shape and reconstruct DataFrame
    decoded_matrix = pd.DataFrame(
        decoded_flat.reshape(matrix.shape),
        columns=matrix.columns,
        index=matrix.index
    )

    # Add the time at which the prediction row starts
    time_column = data['relative_time'].iloc[1 : 1 + len(decoded_matrix)].reset_index(drop=True)
    decoded_matrix.insert(0, 'relative_time', time_column)

    return decoded_matrix


def main():
    parser = argparse.ArgumentParser(description='Plot decoded systemcall prediction matrix')
    parser.add_argument('-a', '--application', type=str, required=True)
    parser.add_argument('-c', '--case', type=str, required=True)
    parser.add_argument('-r', '--run', type=int, required=True)
    parser.add_argument('-s', '--situation', type=str, required=True)
    parser.add_argument('-n', '--num_predictions', type=int, required=True)
    parser.add_argument('-o', '--output', type=str, help='Output prefix for plot and CSV')
    parser.add_argument('-d', '--debug', action='store_true')

    args = parser.parse_args()

    app_base = args.application
    case_base = args.case
    run_base = args.run
    situation_base = args.situation
    num_predictions = args.num_predictions
    output_folder = args.output
    debug_base = args.debug

    configure_logging(output_folder, debug_base)
    sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)

    type_enc, app_enc, label_enc = create_encoders()

    train_decoded_matrix = prepare_encoded_matrix(app_base, case_base, run_base, situation_base, type_enc, app_enc, label_enc, num_predictions, debug_base, True)
    test_decoded_matrix = prepare_encoded_matrix(app_base, case_base, run_base, situation_base, type_enc, app_enc, label_enc, num_predictions, debug_base, False)
    
    unique_sequences_by_type = {}

    for type_matrix,decoded_matrix in [('train',train_decoded_matrix), ('test',test_decoded_matrix)]:
        
        # Plot and save
        if debug_base:
            logging.info("Save results")
        save_decoded_matrix(decoded_matrix, output_folder, type_matrix)

        for call in ALL_SYSTEMCALLS:
            plot_syscall_followups(decoded_matrix, call, output_folder, type_matrix)


        if debug_base:
            logging.info("Get unique next 10 sequences")
        unique_next10_seqs = get_unique_next10_sequences(decoded_matrix, type_matrix, output_folder)
        unique_sequences_by_type[type_matrix] = unique_next10_seqs
        
    
    # Compare test vs train
    test_only_sequences = unique_sequences_by_type['test'] - unique_sequences_by_type['train']

    if debug_base:
        logging.info("\nSequences in TEST but not in TRAIN:")
        logging.info(f"Count: {len(test_only_sequences)}")

    res_path = os.path.join(output_folder, f"squences_in_test_but_not_in_train.txt")
    with open(res_path, 'w') as f:
        for seq in sorted(test_only_sequences):
            f.write(f"{seq}\n")


if __name__ == "__main__":
    main()
