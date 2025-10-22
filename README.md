# I/O Characterization of HPC applications

This folder contains all the scripts necessary for identifying and classifying HPC applications based on their I/O patterns.

## Structure

- **Frontera folder**: Contains the scripts to run the applications. Each application may have multiple test cases, so each subfolder corresponds to a different test of the same application. At the base of the folder, there are also scripts required for different steps, but configured with Frontera-specific options to submit jobs using *sbatch*.

- **Scripts folder**: Contains scripts for running the different steps on a standard computer.

- **Software folder**: Contains dstat script used.

- **ML Pipeline folder**: Contains all code related to train and test the models.

- **Python files**:  Python scripts that are called by the Bash scripts in the Frontera and Scripts folders.


## Analyzed Applications

#### GROMACS

GROMACS is a molecular dynamics simulation application used to study the behavior of biological and non-biological systems.

Two types of tests were created:

- **md_cluster_workflow**: Runs a molecular dynamics simulation to analyze how water molecules and other particles interact with a protein or chemical structure. It prepares the system by creating a water box around the molecules, then performs energy minimization and temperature/pressure adjustments before running the main simulation.

- **water**: Performs a molecular dynamics simulation using pre-prepared input files to track molecular movements and energies. It includes two cases: 3072, which is more complex than 1536. Additional cases can be found at [GROMACS benchmarks](https://ftp.gromacs.org/pub/benchmarks/water_GMX50_bare.tar.gz) (last checked: 06/03/2025).


#### OpenFOAM

OpenFOAM is widely used across engineering and science fields, including both commercial and academic applications. It offers extensive features for solving complex fluid dynamics problems, including chemical reactions, turbulence, heat transfer, acoustics, solid mechanics, and electromagnetics.

Two types of tests were created:

- **combustion**: Simulates buoyant combustion with Lagrangian particles and wall film interactions using buoyantReactingFoam. It models burning fuel in a heated environment, where hot containers create rising air currents that mix fuel droplets with air. It tracks how some droplets form liquid films on surfaces while others burn, using parallel computing to handle the complex interactions between fire, particles, and heat flow.

- **incompressible**: Simulates airflow around a car shape to study aerodynamic efficiency. The script automatically creates and refines a digital mesh around the vehicle, then runs the airflow analysis in parallel using different detail levels (from quick tests to high-accuracy models) to show how air moves around the car body.


#### PyTorch

PyTorch is an open-source machine learning library based on the Torch framework, widely used for applications such as computer vision and natural language processing.

This folder contains three test cases:

- **ResNet50**: This script runs a distributed PyTorch training job for image recognition using the ResNet-50 model on the ImageNet dataset. The training process spans four GPU nodes (16 GPUs in total) and involves coordinating multiple GPUs to learn patterns from over 1,000 image categories. The script sets up a temporary Python environment with PyTorch, manages distributed training, saves progress checkpoints, and monitors system performance throughout the process.

- **BERT**: the propose is to train a BERT (Bidirectional Encoder Representations from Transformers) model from scratch using a dataset of movie dialogues. The application aims to create a language model capable of understanding and generating human-like text by learning from the context of conversations. It processes the dialogue data to generate question-answer pairs, tokenizes the text, and prepares it for training. The model is trained to perform two main tasks: next sentence prediction (determining if one sentence logically follows another) and masked language modeling (predicting missing words in a sentence).

- **BERT-finetuning**: This script fine-tunes a pre-trained BERT model for sequence classification using the CoLA dataset, which evaluates the grammaticality of sentences. Unlike training BERT from scratch, this approach refines an existing model to classify sentences as grammatically acceptable or unacceptable based on linguistic rules. The script handles dataset preprocessing, sentence tokenization, and model training to enhance its classification accuracy.

**Note**: Information about GPU usage during the run is captured using `nvidia-smi`



#### TensorFlow

TensorFlow is an open-source machine learning and artificial intelligence (AI) library used to build and deploy ML-powered applications.

The script supports training different neural network models on the ImageNet dataset:
  - ResNet18: A lightweight residual network model that balances accuracy and efficiency, often used as a baseline for image classification tasks.
  - AlexNet: One of the earlier CNN architectures, AlexNet has fewer and shallower layers than ResNet18, making it computationally lighter. As a result, it tends to train faster but is more dependent on I/O performance.


## SCRIPTS

### Step 0: Compile the Trace Collector Tool

Instructions for compiling the tool can be found in the README file located in the trace-collector folder.

### Step 1: Capturing Traces

Capture traces using the scripts in the frontera folder. As described earlier, each application has different test cases.

**Notes:** 
For each script:
- `LD_PRELOAD` is set to the path of the Trace Collector.
- `DSTAT_PATH` is set to the path of the dstat Python script with the `--ib` option. It can be found in the software folder.
- Its created an output folder and inside that a logs folder that gets the result of the dstat when the program runs
- An output folder is created, with a `logs` subfolder storing the *dstat* output when the program runs.
- The scripts follow this structure:
    - Load modules
    - Directory setup
    - Export variables
    - Run *dstat* on all nodes
    - Sleep for 300 seconds (to allow dstat to initialize)
    - Run application
    - Unset varibles
    - Sleep for 300 seconds (to allow dstat to finish)

Traces should be placed in `results/app/runX/trace`, and dstat results in `results/app/runX/dstat`.


### Step 2: Converting Traces to JSON

Run convert_all_dstat_to_json.sh and convert_all_tracer_tp_json scripts (in frontera or scripts folder). This will create a new output folder (converted_results) with the same structure as the original folder results.

Run `convert_all_dstat_to_json.sh` and `convert_all_tracer_to_json.sh` (in the *frontera* or *scripts* folder). This creates a new output folder (`converted_result`) with the same structure as `results/`.

#### convert_all_dstat_to_json.sh

For each **dstat** folder inside `results/`, this script runs `convert_dstat_log.py` to convert *dstat* logs into JSON format.
- The timestamp is converted to nanoseconds and formatted in ISO 8601.
- The node name is included in the JSON structure.

Example output:
```
[
  {
    "timestamp": "2025-02-27T09:28:10.837337+00:00",
    "node": "c204-001.frontera.tacc.utexas.edu",
    "usr": 38,
    "sys": 1,
    "idl": 61,
    "wai": 0,
    "stl": 0,
    "dsk_read": 35,
    "dsk_writ": 211,
    "io_read": 0.34,
    "io_writ": 1.0,
    "net_recv": 0,
    "net_send": 0,
    "used": 4893704192,
    "free": 194347270144,
    "buff": 0,
    "cach": 268435456,
    "paging_in": 0,
    "paging_out": 0,
    "ib_recv": 0,
    "ib_send": 0
  },
  ...
]
```


#### convert_all_tracer_to_json.sh

For each **tracer** folder inside `results/`, this script runs `convert_tracer_to_json.py` to convert *tracer* logs into JSON format.

- It groups operations into categories (file operations, directory changes, etc.).
- It converts technical timestamps into human-readable dates.
- It runs `combine_files.py`, which merges tracer files with the same PID (tracer files follow the pid_tid naming format, and the result is pid.json).
- Finally, it runs `correlate_fds.py`, which adds a *file_path* parameter to complete the trace with the file involved in each operation.


Example output:
```
[
    {
        "systemcall": "openat",
        "type": "metadatacall",
        "timestamp": "2025-02-27T09:33:29.321313+00:00",
        "tid": 47166370808960,
        "pid": 116472,
        "node": "c204-003.frontera.tacc.utexas.edu",
        "descriptor": -1,
        "path": "/sys/bus/cpu/devices/cpu3/cache/index0/level",
        "new_path": null,
        "offset": null,
        "size": null,
        "return_value": 4,
        "file_path": "/sys/bus/cpu/devices/cpu3/cache/index0/level"
    },
    ...
]
```

### Step 3: ElasticSearch Connection

Run the `send_all_elasticsearch.sh` script in the *scripts* folder.
**Note**: Ensure you update *ES_URL* with the correct Elasticsearch address.

This script uploads all data from the *converted_results* folder to Elasticsearch for each application. The session name in Elasticsearch will follow the format *app_runX*.

After data ingestion, use the automated dashboard cloning tool to create session-specific visualizations:

**Usage:**
```
python replicate_dashboard.py \
  --kibana-url http://<kibana_ip>:5601 \
  --es-host http://<elasticsearch_ip>:9200 \
  --es-user <elastic_user> \
  --es-pass <elastic_password> \
  --base-dashboard <base_dashboard_id> \
  --sessions gromacs_run3 openfoam_run1 pytorch_run2
```

**Key Parameters:**

- --base-dashboard: ID of your template base dashboard (the one you want to replicate by session)
- --sessions: Space-separated list of sessions to create dashboards for (e.g. session1 session2)

This way, the data can be analyzed through various graphs and visualizations.


To verify that all events were successfully uploaded to Elasticsearch, the count.py script was created. It takes as input the path to the desired converted_results folder and returns the number of events found in the tracer, dstat, and nvidia subfolders.

**Usage:**
```
python count.py [path_to_folder]
```

Example:
```
> python3 count.py converted_results/pytorch/imagenet/1
Total documents in tracer: 9244639
Total documents in dstat: 19285
Total documents in nvidia: 81464
```

## Analysis

####  I/O Pattern GROMACS:
- The first node reads and writes data over time during the run. Occasionally, it performs other operations like close, fclose, fopen, open, open_variadic, read and rename. At the end, it always performs at least the following operations: close, fclose, fopen, read, rename, and unlinkat.
- The other nodes may or may not read and write data over time (only the md_cluster_workflow case does), but they perform closing operations at the end.
- At the beginning, all nodes perform various operations such as close, fclose, fopen, fopen64, mmap, munmap, open, open64, open_variadic, openat, read, socket and unlink.


#### I/O Pattern OpenFOAM:
- The first node reads and writes data over time during the run and occasionally performs operations like fclose, fopen64, mkdir, and read.
- The other nodes only perform read and write operations, more reads then writes.
- All nodes perform different operations at the start of the run, including close, fclose, fopen64, munmap, open, open64 and read.


#### I/O Patterns Pytorch
- All nodes perform the same type of work throughout the run, with system calls evenly distributed across them.

- Certain system calls, such as close, munmap, socket, unlink, open64, write, and read, are continuously invoked during execution, though their frequency varies over time.

- The system call open64 shows a higher frequency at the beginning of the execution.

- The system calls fopen, fclose, and mmap primarily occur at the beginning and end of the run and are rarely observed in the middle, across all nodes. However, fclose may also be invoked continuously throughout the execution on the first node.

- The behavior of fopen64 mirrors that of fopen, but only on the first node. On the remaining nodes, fopen64 is only observed at the beginning of the run.

- The system calls mkdir, open, openat, open-variadic, rename, and statfs are exclusively observed at the beginning of the run on all nodes.

- The system calls rmdir and unlinkat only occur at the end of the run.


#### I/O Patterns Tensorflow

- All nodes perform the same type of work throughout the run, with system calls evenly distributed across them.

- A high volume of pread calls was observed consistently throughout the entire run across all nodes.

- Close calls appeared in large numbers at the beginning of the execution, then quickly decreased to a lower but nearly constant rate for the remainder of the run across all nodes.
- open calls occurred continuously during the run, though in relatively small numbers, across all nodes.

- mmap calls were concentrated primarily at the beginning of the execution on all nodes, with occasional occurrences during the run on some nodes.

- read and write system calls were observed mainly at the beginning and end of the run across all nodes, with sporadic appearances in the middle phase on certain nodes.

- open64, fclose, and unlink calls occurred predominantly at the beginning of the run on all nodes, with some nodes also showing occurrences toward the end.

- The munmap system call appeared at both the beginning and end of the execution on all nodes.

- The following system calls were observed exclusively at the beginning of the run, across all nodes: fopen, fopen64, mkdir, open64\_varidiac, openat, rename, socket, and statfs.



#### Notes:
- For the same application and study case, the total number of events varies between runs, but the I/O pattern remains consistent over time across the nodes.
- The first node does more work than the others in the applications OpenFOAM and GROMACS.


## Model Training and Testing

The `ml_pipeline/` directory contains all the scripts required to train and evaluate system call prediction models using [AutoGluon](https://www.autogluon.ai/). Each script is modularized to support various stages of the machine learning pipeline, from data preparation to model evaluation.

### Contents of `ml_pipeline/`:

- **Setup Environment**: Configures the logging and runtime environment.

- **Data Gathering**: Collects training and testing datasets from the traced system call logs.

- **Data Preprocessing**: Prepares the dataset by cleaning column names, generating features, and removing or creating necessary columns.

- **Data Visualization**: Provides ongoing visualizations to aid in data understanding and informed decision-making.

- **Model Evaluation**: Evaluates models using metrics such as accuracy, precision, recall, and execution time. Also includes visualizations of evaluation results.

- **Pipeline Case 1**: Investigates the minimum number of system calls required to reliably predict the next system call.

- **Pipeline Case 2**: Examines whether knowing the last `N` system calls allows accurate prediction of future calls.

- **Pipeline Case 3**: Explores whether it is possible to predict the occurrence of system call bursts during application execution.

### Additional Scripts

- **`script.sh`**: Bash script used to execute the training and evaluation pipeline on the Frontera HPC system.

- **`start_from_load_model_pipeline.py`**: Script that loads a previously trained model and runs the evaluation pipeline without retraining, also to run on Frontera HPC system.

---



## Visualization of the Results

The `create_plot` script is designed to visualize the performance of system call prediction models by plotting **Accuracy** and **F1-Score** across different prediction lengths (1, 10, and 100 next system calls). It combines results from multiple runs to provide an overview of how prediction performance changes with horizon size.

### Usage

```bash
python create_plot.py \
  --application <application_name> \
  --case <case_name> \
  --situation <only|app|all> \
  --output <output_directory> \
  [--debug]
````

### Arguments

* `--application` / `-a`:
  Name of the application being analyzed.

* `--case` / `-c`:
  Specific case or scenario within the application.

* `--situation` / `-s`:
  Defines the training and testing setup:

  * `only`: Model trained and tested only on the specified case.
  * `app`: Model trained on all cases of the specified application.
  * `all`: Model trained on all cases across all applications.

* `--output` / `-o`:
  Directory where the output plots (`plot_f1_score.png` and `plot_accuracy.png`) will be saved.

* `--debug` / `-d`: *(Optional)*
  Enables debug mode for verbose output.

### Output

The script reads performance metrics from CSV files located at:

```
../model_results/<application>/<case>/<situation>/next1/metrics_summary.csv
../model_results/<application>/<case>/<situation>/next10/metrics_summary.csv
../model_results/<application>/<case>/<situation>/next100/metrics_summary.csv
```

It generates two plots:

* `plot_f1_score.png`: F1-Score over 1, 10, and 100 predicted steps
* `plot_accuracy.png`: Accuracy over 1, 10, and 100 predicted steps

These visualizations help compare model performance across different prediction horizons.