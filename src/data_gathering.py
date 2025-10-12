import pandas as pd
import os
import logging
import json
from data_preprocessing import *


#### Auxiliary function to standardize the timestep format
def standardize_timestamp(ts):
    # Check if the timestamp has fractional seconds
    if '+' in ts:
        # Split the timestamp into the main part and the timezone part
        main_part, tz_part = ts.split('+')
        # Check if there are fractional seconds
        if '.' not in main_part:
            # Add '.000000' to the main part if missing
            main_part += '.000000'
        # Reconstruct the timestamp
        return main_part + '+' + tz_part
    return ts  # Return as is if it already has the correct format


#### Auxiliary setup function to load time series data
def load_timeseries_data(base_dir, base_app, case_name, run_number, debug=False):
    if debug:
        logging.info(f"Running {base_app} case {case_name} run number {run_number}")

    tracer_dir = os.path.join(base_dir, base_app, case_name, str(run_number), 'tracer')
    data_files = [f for f in os.listdir(tracer_dir) if f.endswith('.json')]
    if not data_files:
        raise ValueError(f"No JSON files found in {tracer_dir}")

    all_series = []
    node_set = set()

    for f in data_files:
        file_path = os.path.join(tracer_dir, f)
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            df = pd.DataFrame(json_data)

            if df.empty:
                logging.warning(f"Empty DataFrame from file {f}. Skipping.")
                continue

            if 'node' not in df.columns:
                logging.warning(f"File {f} does not contain 'node' column. Skipping.")
                continue

            node_set.update(df['node'].unique())

            df['timestamp'] = df['timestamp'].apply(standardize_timestamp)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['application'] = base_app

            all_series.append(df)

            if debug:
                logging.info(f"Loaded {len(df)} records from {f}")
        

    all_series = [df.dropna(axis=1, how='all') for df in all_series]
    combined_df = pd.concat(all_series, ignore_index=True)

    # combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)

    node_list = list(node_set)
    node_mapping = {node: index for index, node in enumerate(node_list)}
    combined_df['node_index'] = combined_df['node'].map(node_mapping)

    combined_df['run_number'] = run_number

    return combined_df


def get_all_cases(main_folder):
    return [d for d in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, d))]

def should_skip(app, case, run, app_base, case_base, run_base, situation_base):
    if str(app) == app_base and str(case) == case_base and int(run) == int(run_base):
        print("Skip test run")
        return True
    if situation_base == "only" and str(case) != case_base:
        print(f"SKIP case {case} run {run}")
        return True
    return False

def load_training_data(base_dir, app_base, case_base, run_base, situation_base, debug_base, N, ALL_APPLICATIONS, type_enc, app_enc, label_enc):
    train_data = pd.DataFrame()

    if situation_base in ("only", "app"):
        app = app_base
        main_folder = os.path.join(base_dir, app)
        all_cases = get_all_cases(main_folder)

        for case in all_cases:
            for run in range(1, 4):
                if should_skip(app, case, run, app_base, case_base, run_base, situation_base):
                    continue
                data = preprocessing(load_timeseries_data(base_dir, app, case, run, debug=debug_base), N, type_enc, app_enc, label_enc)
                train_data = pd.concat(
                    [train_data, data],
                    ignore_index=True
                )

    elif situation_base == "all":
        for app in ALL_APPLICATIONS:
            main_folder = os.path.join(base_dir, app)
            all_cases = get_all_cases(main_folder)
            for case in all_cases:
                for run in range(1, 4):
                    if should_skip(app, case, run, app_base, case_base, run_base, situation_base):
                        continue
                    train_data = pd.concat(
                        [train_data, load_timeseries_data(base_dir, app, case, run, debug=debug_base)],
                        ignore_index=True
                    )

    return train_data