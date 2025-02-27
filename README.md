# ProbLog Based AI Agent

### 1. Problog Agent Ole
A probabilistic logic agent implemented using ProbLog:
- Uses probabilistic logic programming for decision making under uncertainty
- Implements probabilistic reasoning about opponent behavior and action outcomes
- Maintains dynamic probabilistic models of game state
- Makes decisions based on utility and probability scores
- Adapts strategy based on health, energy, and positional factors

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
