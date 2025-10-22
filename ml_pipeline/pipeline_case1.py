from setup_environment import *
from data_gathering import *
from data_preprocessing import *
from data_visualization import *

from category_encoders import BinaryEncoder
import argparse
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, OrdinalEncoder
import sys
from autogluon.tabular import TabularPredictor
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

############ Setup global variables ############

# Define base directory
base_dir = '../converted_results/'

# Define all possible categories manually
ALL_TYPES = ['datacall', 'directoryCall', 'ExtendedAttributesCall', 'MetadataCall', 'SpecialCall']
ALL_APPLICATIONS = ['gromacs', 'openfoam', 'pytorch', 'tensorflow']

# Create the encoders
type_encoder = OneHotEncoder(categories=[ALL_TYPES], handle_unknown='ignore', sparse_output=False)
application_encoder = OneHotEncoder(categories=[ALL_APPLICATIONS], handle_unknown='ignore', sparse_output=False)

label_encoder = LabelEncoder()
# type_encoder = OneHotEncoder(sparse_output=False)
# application_encoder = OneHotEncoder(sparse_output=False)
binary_encoder = BinaryEncoder()
ordinal_encoder = OrdinalEncoder()

target_column = 'next_systemcalls'

# Number of previous calls to consider
N = 50
# Number of future calls to predict
num_predictions = 1

# n_values = range(1, N+1)
n_values = range(25, 101, 25)
len_n_values = len(n_values)

############ Setup logging ############


# Set up argument parser
parser = argparse.ArgumentParser(description='System Call Prediction Script')
parser.add_argument('-a', '--application', type=str, required=True, help='Application name to test')
parser.add_argument('-c', '--case', type=str, required=True, help='Case name to test')
parser.add_argument('-r', '--run', type=int, required=True, help='Run number to test (1, 2, or 3)')
parser.add_argument('-o', '--output', type=str, required=True, help='Output folder')
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
args = parser.parse_args()

# Define case of test
app_base = args.application
case_base = args.case
run_base = args.run
debug_base = args.debug
output_dir = args.output

configure_logging(output_dir, debug_base)


# Redirect stdout and stderr
sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)



############ Training Data ############

# Note: Load training data from all cases and all runs except the specified test run

# Initialize an empty DataFrame for training data
train_data = pd.DataFrame()

# Dynamically get the list of all case names from the base_app directory
main_folder = base_dir + app_base
all_cases = [d for d in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, d))]

# Iterate through all cases
for case in all_cases:
    for run in range(1, 4):  # Runs 1, 2, and 3
        if str(case) == case_base and int(run) == int(run_base):
            print("Skip test run")
            continue  # Skip the test case and run
        if str(case) != case_base:
            print("SKIP case " + str(case) + " run " + str(run))
            continue
        train_data = pd.concat([train_data, load_timeseries_data(base_dir, app_base, case, run, debug=debug_base)], ignore_index=True)


############ Test Data ############

# Note: Load test data from the specified case and run

test_data = load_timeseries_data(base_dir, app_base, case_base, run_base, debug=debug_base)


############ Model Training and Predicting ############

scores = []

for Nv in n_values:

    logging.info(f"Training with N={Nv}...")

    # ---- Preprocess training data ----
    logging.debug("Preprocessing training data...")
    processed_train = preprocessing(train_data.copy(), Nv, type_encoder, application_encoder, label_encoder)

    # Generate target labels (future system calls)
    processed_train[target_column] = [get_next_systemcalls(processed_train, num_predictions, idx)
                                      for idx in processed_train.index]
    
    
    print(processed_train.columns)
    print(processed_train.info())
    first_rows(processed_train)

    # ---- Train the model ----
    logging.info("Training model...")
    predictor = TabularPredictor(label=target_column).fit(
        train_data=processed_train,
        excluded_model_types=['CAT', 'XGB', 'RF', 'GBM', 'XT', 'NN_TORCH', 'KNN'],
        time_limit=5000
    )

    # ---- Preprocess test data ----
    logging.debug("Preprocessing test data...")
    processed_test = preprocessing(test_data.copy(), Nv, type_encoder, application_encoder, label_encoder)
    processed_test[target_column] = [get_next_systemcalls(processed_test, num_predictions, idx)
                                     for idx in processed_test.index]
    
    print(processed_test.columns)
    print(processed_test.info())
    first_rows(processed_test)

    # ---- Predict and evaluate ----
    logging.debug("Making predictions on test data...")
    test_features = processed_test.drop(columns=[target_column], errors='ignore')
    test_labels = processed_test[target_column]

    test_predictions = predictor.predict(test_features)

    # Evaluate
    acc = accuracy_score(test_labels, test_predictions)
    prec = precision_score(test_labels, test_predictions, average='macro', zero_division=0)
    rec = recall_score(test_labels, test_predictions, average='macro', zero_division=0)
    f1 = f1_score(test_labels, test_predictions, average='macro', zero_division=0)

    logging.info(f"N={Nv} => Accuracy: {acc:.4f}, Precision: {prec:.4f}, Recall: {rec:.4f}, F1: {f1:.4f}")
    scores.append({
        'N': Nv,
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1_score': f1
    })

# Plot and save figures
# Extract individual metric lists and N values
accuracies = [m['accuracy'] for m in scores]
precisions = [m['precision'] for m in scores]
recalls = [m['recall'] for m in scores]
f1s = [m['f1_score'] for m in scores]

# Use your updated function
plot_metric(output_dir, accuracies, "Accuracy", len_n_values)
plot_metric(output_dir, precisions, "Precision", len_n_values)
plot_metric(output_dir, recalls, "Recall", len_n_values)
plot_metric(output_dir, f1s, "F1-Score", len_n_values)