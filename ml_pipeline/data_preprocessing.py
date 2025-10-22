import pandas as pd
import numpy as np
import logging
from sklearn.preprocessing import MinMaxScaler


def preprocessing(base_data, N, type_encoder, application_encoder, label_encoder):

    ####### descomment when pipeline case 3  ######
    
    # Add relative_time column (in seconds), grouped by run_number
    # base_data['relative_time'] = base_data.groupby('run_number')['timestamp'].transform(
    #     lambda x: (x - x.min()).dt.total_seconds().astype(int)
    # )

    ###############################################

    base_data['systemcall_encoded'] = label_encoder.fit_transform(base_data['systemcall'])


    ###### comment when pipeline case 3   ########
    
    # # Now generate the N previous systemcalls
    for i in range(1, N + 1):
        base_data[f'prev_systemcall_{i}'] = base_data['systemcall_encoded'].shift(i)

    
    # base_data.drop('timestamp', axis=1, inplace=True)
    # base_data.drop('run_number', axis=1, inplace=True)

    ###############################################

    return base_data


# Create one column with the next num_predictions systemcalls separated by commas
def get_next_systemcalls(base_data, num_predictions, idx):
    next_calls = base_data['systemcall_encoded'].iloc[idx+1 : idx+1+num_predictions]
    return ",".join(map(str, next_calls))


def build_systemcall_matrix(data, num_predictions):
    
    syscall_seq = data['systemcall_encoded'].tolist()
    matrix = []

    for i in range(len(syscall_seq) - num_predictions):
        row = syscall_seq[i:i + num_predictions + 1]  # current + next N
        matrix.append(row)

    columns = [f"pred_{i}" for i in range(num_predictions + 1)]
    matrix_df = pd.DataFrame(matrix, columns=columns)

    return matrix_df


def preprocessing_aggregate(df, window_size_sec, burst_threshold, debug, is_train):
    
    if debug:
        logging.info("Starting preprocessing_aggregate...")

    df = df.copy()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['timestamp'] = df['timestamp'].dt.tz_localize(None)

    if debug:
        logging.info("Grouping by 'run_number' and timestamp windows...")

    aggregated = []

    for run_id, run_group in df.groupby('run_number'):
        run_group = run_group.set_index('timestamp')

        windowed = run_group.resample(f'{window_size_sec}s').agg({
            'systemcall': 'count',
        })

        windowed.rename(columns={'systemcall': 'total_syscalls'}, inplace=True)
        windowed['timestamp'] = windowed.index
        
        windowed['run_number'] = run_id
        windowed['is_burst'] = windowed['total_syscalls'] >= burst_threshold

        if is_train:
            if debug:
                logging.info(f"Calculating time to next burst for run {run_id}...")
            next_burst_time = []
            burst_times = windowed.loc[windowed['is_burst'], 'timestamp'].values

            for current_time in windowed['timestamp']:
                future_bursts = burst_times[burst_times > current_time]
                if len(future_bursts) > 0:
                    next_burst_time.append(future_bursts[0] - current_time)
                else:
                    next_burst_time.append(pd.Timedelta(seconds=9999))  # Ensures dtype consistency

            windowed['seconds_to_next_burst'] = next_burst_time
            windowed['seconds_to_next_burst'] = pd.to_timedelta(windowed['seconds_to_next_burst']).dt.total_seconds().astype(int)


        aggregated.append(windowed)

    result = pd.concat(aggregated).reset_index(drop=True)

    # Add relative_time column (in seconds), grouped by run_number
    result['relative_time'] = result.groupby('run_number')['timestamp'].transform(
        lambda x: (x - x.min()).dt.total_seconds().astype(int)
    )

    if is_train:
        return_columns = ['run_number', 'relative_time', 'total_syscalls', 'seconds_to_next_burst']
    else:
        return_columns = ['run_number', 'relative_time', 'total_syscalls']

    return result[return_columns]



def preprocessing_aggregate_online(df, window_size_sec, burst_threshold, debug, is_train):
    if debug:
        logging.info("Starting preprocessing_aggregate...")

    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)

    aggregated = []

    for run_id, run_group in df.groupby('run_number'):
        run_group = run_group.set_index('timestamp')
        windowed = run_group.resample(f'{window_size_sec}s').agg({'systemcall': 'count'})
        windowed.rename(columns={'systemcall': 'total_syscalls'}, inplace=True)
        windowed['timestamp'] = windowed.index
        windowed['run_number'] = run_id
        windowed['is_burst'] = windowed['total_syscalls'] >= burst_threshold

        if is_train:
            next_burst_time = []
            burst_times = windowed.loc[windowed['is_burst'], 'timestamp'].values

            for current_time in windowed['timestamp']:
                future_bursts = burst_times[burst_times > current_time]
                delta = future_bursts[0] - current_time if len(future_bursts) else pd.Timedelta(seconds=9999)
                next_burst_time.append(delta)
            
            windowed['seconds_to_next_burst'] = next_burst_time
            windowed['seconds_to_next_burst'] = pd.to_timedelta(windowed['seconds_to_next_burst']).dt.total_seconds().astype(int)

        aggregated.append(windowed)

    result = pd.concat(aggregated).reset_index(drop=True)
    result['relative_time'] = result.groupby('run_number')['timestamp'].transform(
        lambda x: (x - x.min()).dt.total_seconds().astype(int)
    )

    return_cols = ['run_number', 'relative_time', 'total_syscalls']
    if is_train:
        return_cols.append('seconds_to_next_burst')

    return result[return_cols]



def compute_thresholds(train_data, debug, TIME_THRESHOLD):

    # Make sure timestamps are sorted
    train_data = train_data.sort_values('timestamp')
    
    # Create time window column
    train_data['time_window'] = (train_data['timestamp'].astype('int64') // 1_000_000_000 // TIME_THRESHOLD).astype(int)
        
    # Count rows in each window = burst sizes
    burst_sizes = train_data.groupby('time_window').size()
    
    # Compute 90th percentile of burst sizes
    burst_threshold = burst_sizes.quantile(0.95)

    if debug:
        logging.info(f"Auto Burst Threshold (95th percentile burst size): {burst_threshold}")
        logging.info(f"Time Threshold: {TIME_THRESHOLD}")

    return burst_threshold
