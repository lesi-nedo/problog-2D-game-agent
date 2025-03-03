# ProbLog Based AI Agent

### 1. Problog Agent Ole
A probabilistic logic agent implemented using ProbLog:
- Uses probabilistic logic programming for decision making under uncertainty
- Implements probabilistic reasoning about opponent behavior and action outcomes
- Maintains dynamic probabilistic models of game state
- Makes decisions based on utility and probability scores
- Adapts strategy based on health, energy, and positional factors

## Getting Started

### Prerequisites
- Python 3.8+
- ProbLog (`pip install problog[sdd]`)
- PyFTG (Fighting Game AI Framework)
- DareFightingICE game environment

### Setup
1. Clone this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Ensure the DareFightingICE game environment is properly set up in the `DareFightingICE_CODE` directory

### Running the Game and Agent

#### Option 1: Using the run_py_ag.sh script
This script handles both launching the game and connecting the agent:

```bash
# Basic usage
./run_py_ag.sh problog_agent/MainMctsVsProblog.py

# To run with specific port
./run_py_ag.sh problog_agent/MainMctsVsProblog.py -p 4242

# To run in headless mode (without GUI)
./run_py_ag.sh problog_agent/MainMctsVsProblog.py --headless

# To play against the agent using a keyboard
./run_py_ag.sh problog_agent/MainKeyboardVsProblogA.py
```

#### Option 2: Manual startup
1. Start the DareFightingICE game:
   ```bash
   cd DareFightingICE_CODE
   ./compile_run_linux.sh
   ```

2. In a separate terminal, start the agent:
   ```bash
   python problog_agent/MainMctsVsProblog.py
   ```

### Command Line Parameters for the Agent

When running `MainMctsVsProblog.py` or `MainKeyboardVsProblogA.py`:

- `--host`: Specify the host (default: 127.0.0.1, must match the game host)
- `--port`: Specify the port (default: 31415, must match the game port) 
- `--plot-scenes`: Enable visual plotting of game scenes (only for jupyter notebook)

Example:
```bash
python problog_agent/MainMctsVsProblog.py
```

## Project Files Overview

### Problog Agent Implementation
- `problog_agent/ProblogAgent.py`: Main Problog agent using probabilistic logic programming
- `problog_agent/terms.py`: Defines terms and predicates for probabilistic reasoning
- `problog_agent/KB_V1.pl`: ProbLog knowledge base with probabilistic rules

### Shell Scripts and Automation
- `run_py_ag.sh`: Bash script for running the Prolog agent against the game environment
- `run_py_ag_parallel.sh`: Script for running multiple Python agents in parallel with configurable executions
- `monitor_restart.sh`: Monitoring script that watches for file changes and automatically restarts agents
- `common.sh`: Common utilities and functions shared between shell scripts

### Testing and Evaluation
- `stats_k=*/`: Directory containing test results and statistics for ProbLog agent
- `results_k=*.ipynb`: Jupyter notebooks for analyzing and visualizing Problog agent performance

### Documentation
- `README.md`: Project documentation and setup instructions
- `run_py_ag.md`: Instructions for running Python agents against the game environment
- `monitor_restart.md`: Guide for monitoring and restarting agents on file changes



### Tools and Technologies

- **Programming Languages:** Python
- **Libraries:** found in `requirements.txt` 
- **Platforms:** GitHub
