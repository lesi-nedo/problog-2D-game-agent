import logging
import queue
import numpy as np
import typer
import time
import os
import sys
import matplotlib
import logging
import pandas as pd

logging.getLogger().setLevel(logging.WARNING)
# Suppress PIL debug logging
logging.getLogger('PIL').setLevel(logging.WARNING)

# Suppress matplotlib font manager debug logging
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)

# Suppress matplotlib debug logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)

# Suppress debug messages for PNG handling
logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)
matplotlib.use('Agg') 


# Get the absolute path of the project root directory 
project_root = os.path.abspath(os.path.join(os.getcwd()))

# Add both the root and problog agent directory to Python path
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'prolog_based', 'problog_agent_ole'))

print(f"Project root: {project_root}")

from datetime import datetime
from display_thread import DisplayThread
from typing import Dict


from pyftg import (
    AIInterface,
    AudioData,
    CommandCenter,
    FrameData,
    GameData,
    Key,
    RoundResult,
    ScreenData,
)

from pyftg.models.enums.action import Action
from pyftg.models.character_data import CharacterData
from problog.program import PrologString
from problog.engine import DefaultEngine
from problog.sdd_formula import SDD
from problog.logic import Term, term2list, term2str
from problog import get_evaluatable
from mappings import actions_type
from terms import attack_b_actions, move_actions

rng = np.random.default_rng()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
problog_logger = logging.getLogger("problog")
problog_logger.setLevel(logging.ERROR)

class ProblogAgent(AIInterface):
    """
    ProblogAgent class that implements the AIInterface for the ProblogAgent. This agent uses ProbLog 
    for probabilistic reasoning to select actions in a fighting game environment.
    The agent maintains game state information across multiple rounds and uses probabilistic logic programming
    to make decisions about which actions to take based on the current game state, opponent behavior, 
    and learned patterns.
    Attributes:
        plot_scenes (bool): Whether to plot game scenes visually (default: False) 
        echo_actions (bool): Whether to print selected actions (default: False)
        width (int): Width of game window (default: 960)
        height (int): Height of game window (default: 640)
        blind_flag (bool): Whether agent operates in blind mode
        width (int): Window width
        height (int): Window height
        play_number (bool): Player number identifier
        game_data (GameData): Game state data
        cc (CommandCenter): Command center for executing actions
        my_character_data (CharacterData): Current player character data
        opponent_character_data (CharacterData): Opponent character data
        current_round (int): Current game round number
        aggressive_action (bool): Flag for aggressive actions
    State Tracking:
        - Tracks positions, hitboxes, actions, energy levels and health for both players
        - Maintains history of states and actions across multiple rounds
        - Records timing and performance metrics
        - Tracks round results and game statistics
    Methods:
        initialize: Sets up the agent with game data and player number
        processing: Main processing loop for selecting actions
        round_end: Handles end of round cleanup and statistics
        game_end: Handles end of game cleanup
        close: Cleanup and save statistics
    The agent uses ProbLog rules defined in an external .pl file for action selection logic.
    Statistical tracking helps analyze agent performance across games.
    """


    def __init__(self, k_most_prob_actions: int = 5, plot_scenes: bool = False, echo_actions=False, width: int = 960, height: int = 640, **kwargs):
        # time.sleep(20)
        super().__init__()
        self.blind_flag = True # It should be used to get the data screen from the game, but it is not working correctly
        self.width = width 
        self.height = height
        self.play_number: bool
        self.game_data: GameData 
        self.cc = CommandCenter()
        self.plot_scenes = plot_scenes
        self.empty_key_dict = Key().to_dict()
        self.my_character_data: CharacterData
        self.opponent_character_data: CharacterData
        self.is_control = False
        self.my_curr_pos: dict[int, list[tuple[int,int]]] = {}
        self.opponent_curr_pos: dict[int, list[tuple[int,int]]] = {}
        self.my_hboxes: dict[Dict[str, int]] = {}
        self.opponent_hboxes: dict[Dict[str, int]] = {}
        self.my_actions_inferred: dict[int, list[Action]] = {1: [], 2: [], 3: []}
        self.kb = ""
        self.engine = DefaultEngine()
        self.db_org = None
        self.my_actions: dict[int, list[Action]] = {1: [Action.STAND.value], 2: [Action.STAND.value], 3: [Action.STAND.value]}
        self.opponent_actions: dict[int, list[Action]] = {1: [Action.STAND.value], 2: [Action.STAND.value], 3: [Action.STAND.value]}
        self.opponent_actions_type: dict[int, list[Action]] = {1: ["non_attack"], 2: ["non_attack"], 3: ["non_attack"]}
        self.my_actions_type: dict[int, list[Action]] = {1: ["non_attack"], 2: ["non_attack"], 3: ["non_attack"]}
        self.my_state: dict[int, list[Action]] = {1: [Action.STAND.value], 2: [Action.STAND.value], 3: [Action.STAND.value]}
        self.opponent_state: dict[int, list[Action]] = {1: [Action.STAND.value], 2: [Action.STAND.value], 3: [Action.STAND.value]}
        self.opponent_speed: dict[int, list[tuple[int,int]]] = {1: [(0, 0)], 2: [(0, 0)], 3: [(0, 0)]}  
        self.opponent_energy: dict[int, list[int]] = {1: [0], 2: [0], 3: [0]}
        self.my_energy: dict[int, list[int]] = {1: [0], 2: [0], 3: [0]}
        self.opponent_hps: dict[int, list[int]] = {}
        self.my_hps: dict[int, list[int]] = {}
        self.count_frames = 0
        self.round_results: dict[int, str|None] = {1: None, 2: None, 3: None}
        self.echo_actions= echo_actions

        self.durations: dict[int, float] = {1: 0.0, 2: 0.0, 3: 0.0}
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.time_taken: dict[int, list[float]] = {1: [], 2: [], 3: []}
        self.prefix = "./prolog_based/problog_agent_ole/"
        self.kb_rules_file_name = "KB_V1.pl"
        self.kb_path_rules =os.path.join(self.current_dir, self.kb_rules_file_name)
        self.screen_data_raw = None
        self.echo = typer.echo
        self.width_game = 960
        self.height_game = 640
        self.k_most_prob_actions = k_most_prob_actions # Number of opponent's best actions to consider. It is not used in the final version
        self.current_round = 1
        self.aggressive_action = False # Flag for aggressive actions, if is true, the agent will add the opponent's action to the Knowledge Base. (It is not used in the final version)
        # Initialize plot on first frame if not already done
        if self.plot_scenes:
            self._init_plots()
            self.echo = self.display_thread.add_log

        self.default_positions = {
            0: (720, 537),
            1: (240, 537)
        }

        self.default_hbox = {
            1: {
                "left": 200,
                "right": 260,
                "top": 435,
                "bottom":640
            },
            0: {
                "left": 700,
                "right": 740,
                "top": 435,
                "bottom": 640
            }
        }

        self.default_dir = {
            0: -1,
            1: 1
        }

        self.direction = {
            1: 1,
            0: -1
        }
        # Counters for state tracking, used for probabilistic estimation of opponent state
        self.counters = {
            'me': {
                'stand': 0,
                'down': 0,
                'air': 0,
                'crouch': 0,
                'total': 1
            },
            'opponent': {
                'stand': 0,
                'down': 0,
                'air': 0,
                'crouch': 0,
                'total': 1
            }
        }
        self.state_counters = {
            'me': {
                'stand': lambda: self._increment_counter('me', 'stand'),
                'down': lambda: self._increment_counter('me', 'down'),
                'air': lambda: self._increment_counter('me', 'air'),
                'crouch': lambda: self._increment_counter('me', 'crouch')
            },
            'opponent': {
                'stand': lambda: self._increment_counter('opponent', 'stand'),
                'down': lambda: self._increment_counter('opponent', 'down'),
                'air': lambda: self._increment_counter('opponent', 'air'),
                'crouch': lambda: self._increment_counter('opponent', 'crouch')
            }
        }
        
        # Counter for opponent actions to estimate aggressive actions. (Final version does not use this)
        self.counter_actions = {}
        self.counter_actions_total = 1
        self.clauses_to_add = dict()

        self.select_box_side = {
            0: "left",
            1: "right"
        }


        self.name_conv = {
            "me": "my",
            "opponent": "opponent"
        }
        self.stats_tracker = None

        if kwargs.get("stats_tracker", None):
            self.stats_tracker = kwargs.get("stats_tracker")
        

        
    def name(self) -> str:
        return self.__class__.__name__

    def is_blind(self) -> bool:
        """
        Check if the agent is operating in blind mode, i.e. without access to screen data
        """
        return self.blind_flag
    
    def to_string(self):
        return self.name()
    
    def _init_attributes(self):
        """
        Initialize agent attributes and data structures with default values
        Adds clauses to the ProbLog knowledge base for initial game state
        Grounds the knowledge base with the initial game state
        """
        self.key = Key()
        self.frame_data = FrameData()

        self.my_curr_pos = {1: [self.default_positions.get(self.my_number)], 2: [self.default_positions.get(self.my_number)], 3: [self.default_positions.get(self.my_number)]}
        self.opponent_curr_pos = {1: [self.default_positions.get(self.opponent_number)], 2: [self.default_positions.get(self.opponent_number)], 3: [self.default_positions.get(self.opponent_number)]}
        self.my_hboxes = {1: [self.default_hbox.get(self.my_number)], 2: [self.default_hbox.get(self.my_number)], 3: [self.default_hbox.get(self.my_number)]}
        self.opponent_hboxes = {1: [self.default_hbox.get(self.opponent_number)], 2: [self.default_hbox.get(self.opponent_number)], 3: [self.default_hbox.get(self.opponent_number)]}
        self.opponent_hps = {1: [self.game_data.max_hps[self.opponent_number]], 2: [self.game_data.max_hps[self.opponent_number]], 3: [self.game_data.max_hps[self.opponent_number]]}
        self.my_hps = {1: [self.game_data.max_hps[self.my_number]], 2: [self.game_data.max_hps[self.my_number]], 3: [self.game_data.max_hps[self.my_number]]}

        self.db_enriched = self.db_org.extend()

        my_prev_action = f"prev_action(me, {Action.STAND.value}).\n"
        opponent_prev_action = f"prev_action(opponent, {Action.STAND.value}).\n"
        me_str_hp = f"curr_hp_value(me, {self.my_hps[self.current_round][0]}).\n"
        me_str_energy = f"curr_energy_value(me, {self.my_energy[self.current_round][0]}).\n"
        opponent_str_hp = f"curr_hp_value(opponent, {self.opponent_hps[self.current_round][0]}).\n"
        opponent_str_energy = f"curr_energy_value(opponent, {self.opponent_energy[self.current_round][0]}).\n"
        count_state_opponent, count_total_states_opponent = f"count_state({Action.STAND.value}, {self.counters['opponent']['stand']}).\n", f"count_total_states({self.counters['opponent']['total']}).\n"
        my_facing_dir = f"facing_dir(me, {self.default_dir.get(self.my_number)}).\n"
        opponent_facing_dir = f"facing_dir(opponent, {self.default_dir.get(self.opponent_number)}).\n"
        me_curr_pos = f"1.0::curr_pos(me, {self.my_curr_pos[self.current_round][0][0]}, {self.my_curr_pos[self.current_round][0][1]}).\n"
        opponent_curr_pos = f"0.9::curr_pos(opponent, {self.opponent_curr_pos[self.current_round][0][0]}, {self.opponent_curr_pos[self.current_round][0][1]}).\n"
        my_state = f"my_state({Action.STAND.value}).\n"
        opponent_prev_energy = f"prev_energy_value(opponent, {self.opponent_energy[self.current_round][0]}).\n"
        me_prev_energy = f"prev_energy_value(me, {self.my_energy[self.current_round][0]}).\n"
        # counter_action = f"count_action({Action.STAND_FA.value}, 1).\n"
        # counter_total_actions = f"count_total_actions(1).\n"
        my_prev_health = f"prev_hp_value(me, {self.my_hps[self.current_round][0]}).\n"
        my_prev_energy = f"prev_energy_value(me, {self.my_energy[self.current_round][0]}).\n"
        opponent_prev_health = f"prev_hp_value(opponent, {self.opponent_hps[self.current_round][0]}).\n"
        opponent_prev_energy = f"prev_energy_value(opponent, {self.opponent_energy[self.current_round][0]}).\n"
        opponent_hbox = f"hbox(opponent, [{self.opponent_hboxes[self.current_round][0]['left']}, {self.opponent_hboxes[self.current_round][0]['right']}, {self.opponent_hboxes[self.current_round][0]['top']}, {self.opponent_hboxes[self.current_round][0]['bottom']}]).\n"


        str_concat = "\n".join([
            me_str_hp, me_str_energy, opponent_str_hp, opponent_str_energy,
            count_state_opponent, count_total_states_opponent, my_state,
            me_curr_pos, opponent_curr_pos, my_facing_dir, opponent_facing_dir,
            my_prev_action, opponent_prev_energy, opponent_prev_action,
            me_prev_energy, opponent_hbox, my_prev_health, my_prev_energy, opponent_prev_health, opponent_prev_energy])
        for statement in PrologString(str_concat):
            self.db_enriched += statement

        lof = self.engine.ground_all(self.db_enriched)
        self.sdd =  get_evaluatable(name='sdd')
        
        

    def initialize(self, game_data: GameData, player_number: int):
        """
        Initialize the agent with game data and player number
        Args:
        game_data (GameData): Game data object
        player_number (int): Player number identifier
    
        """
        self.cc = CommandCenter()
        self.key = Key()
        self.my_number = int(player_number)
        self.opponent_number = abs(1 - self.my_number)
        self.game_data = game_data 
        self.frame_data = FrameData()
        self.last_hp = game_data.max_hps[self.my_number]
        self.last_opponent_hp = game_data.max_hps[self.opponent_number]
        
        
        if not SDD.is_available():
            raise ImportError("SDD package not available, are you running on Windows?, then not supported. If linux, try to install with 'pip install problog[sdd]'")
        
        try:
            with open(self.kb_path_rules, "r") as f:
                self.kb_rules = f.read()
            self.kb = PrologString(self.kb_rules)
            self.db_org = self.engine.prepare(self.kb)

            
        
        except FileNotFoundError:
            logger.error("File not found")
            raise 
        
        self._init_attributes()

        
    def get_non_delay_frame_data(self, frame_data: FrameData):
        pass

    def input(self) -> Key:
        """
        Get the current key input for the agent
        It is used to get the key input from the agent to the game
        """
        return self.key

    def get_information(self, frame_data: FrameData, is_control: bool):
        """
        Get the current frame data and control status
        Args:
        frame_data (FrameData): Frame data object
        is_control (bool): whether the character can act. this parameter is not delayed
        """
        self.frame_data = frame_data
        self.my_character_data = self.frame_data.get_character(self.my_number)
        self.opponent_character_data = self.frame_data.get_character(self.opponent_number)
        self.cc.set_frame_data(self.frame_data, self.my_number)
        self.is_control = is_control
        self.current_round = self.frame_data.current_round

        

    def get_audio_data(self, audio_data: AudioData):
        self.audio_data = audio_data


    
    def select_action_from_problog_results(self, result):
        """
        It groups each best action (with utility) inferred by ProbLog and selects one of them based on their weights (utility + probabilities).
        If the result is empty, it selects a random action from the list of possible actions. Result is empty when the `find_best_action` predicate does not find any action.
        Args:
        result (dict): Dictionary of action-utility and their probabilities
        """
        try:
            # self.echo(f"Result: {result}")
            # Check if result exists and is iterable
            
            if not result or not hasattr(result, 'items'):
                self.echo(f"Result: {result}")
                logger.warning("Invalid result format from ProbLog")
                return None
                
            # Extract valid actions and their probabilities
            action_weights_dit = {}
            for res, prob in result.items():
                # Remember the arity of the term
                weight = prob
                try:
                    if isinstance(res, Term):
                        
                        # self.echo(f"Res- prob: {res.probability}")
                        action = term2str(res.args[0])
                        # If the action is super special, return it immediately
                        if action == "stand_d_df_fc":
                            return action
                        if hasattr(res.args[1], 'compute_value'):
                            weight += res.args[1].compute_value()
                        else:
                            # if here, it means that there was no action with utility, so it is a random attack action
                            weight += res.args[1]
                            action = term2str(rng.choice(attack_b_actions, size=1, replace=False)[0])

                        
     
                        if action not in action_weights_dit:
                            action_weights_dit[action] = weight
                        else:
                            action_weights_dit[action] += weight
                    else:
                        self.echo(f"Result not isinstance: {res}")
                        action = term2list(res)
                        return term2str(rng.choice(action, size=1, replace=False)[0])
                    
                except (AttributeError, IndexError, TypeError) as e:
                    self.echo(f"Error processing result item: {e}")
                    continue
            

            action_weights_list = [(action, prob) for action, prob in action_weights_dit.items() if prob > 0.0]
            if len(action_weights_list) == 0:
                # If here, it means that there was no action with utility-probability greater than 0.0.
                # It happens when the opponent can use the super special attack, so the agent should jump to avoid it.
                self.echo(f"Result-in not action_prob_list: {result}")
                combined_actions = ["for_jump", "back_jump"]
                return term2str(rng.choice(combined_actions, p=[0.8, 0.2], size=1, replace=False)[0])
            
           
            # Choose action list based on probabilities
            actions_list, weights = zip(*action_weights_list)
            sum_weights = sum(weights)
            probabilities = [weight / sum_weights for weight in weights]
            return term2str(rng.choice(actions_list, p=probabilities, size=1, replace=False)[0])
        
        except Exception as e:
            # If here, it means that there was an error in the selection of the action. So, the agent selects a random action from the attack and move actions.
            self.echo(f"Result: {result}")
            self.echo(f"Error in select_action_from_problog_results: {e}")
            combined_actions = attack_b_actions + move_actions
            return term2str(rng.choice(combined_actions, size=1, replace=False)[0])
            # exit(1)

    def processing(self):
        """
        Main processing loop for selecting actions
        It uses the ProbLog knowledge base to infer the best action based on the current game state
        It records the time taken for inference and the selected action
        It saves the game state information for the next frame 
        """
        if self.frame_data.empty_flag or self.frame_data.current_frame_number <= 0:
            return
        
        self.durations[self.current_round] += self.frame_data.current_frame_number
        
        if self.cc.get_skill_flag():
            self.key = self.cc.get_skill_key()       
        
        elif self.is_control:
            # The multipler is used to adjust the prediction of the opponent's position based on the speed of the opponent,
            # or based on hit confirm of the agent. 
            multiplier = np.abs(self.frame_data.current_frame_number - self.count_frames)
            self.key.empty()
            self.cc.skill_cancel()
            current_round = self.frame_data.current_round
            # opponent_actions_type_list = self.opponent_actions_type[current_round]
            # opponent_actions_type_list.append(self.get_opponent_prev_action_type())
            # prev action types
            # my_actions_type_list = self.my_actions_type[current_round]
            # my_actions_type_list.append(self.get_my_prev_action_type())
            # updating counters based on prev opponent action type
            # self.aggressive_action = opponent_actions_type_list[-1] == "attack" or opponent_actions_type_list[-1] == "special"
            # if self.aggressive_action:
            #     self.counter_actions.update({self.opponent_character_data.action.value: self.counter_actions.get(self.opponent_character_data.action.value, 0) + 1})
            #     self.counter_actions_total += 1

            # state update
            my_state_list = self.my_state[current_round]
            my_state_list.append(self.my_character_data.state)
            opponent_state_list = self.opponent_state[current_round]
            opponent_state_list.append(self.opponent_character_data.state)
            # action update
            my_actions_list = self.my_actions[current_round]
            my_actions_list.append(self.my_character_data.action.value)
            opponent_actions_list = self.opponent_actions[current_round]
            opponent_actions_list.append(self.opponent_character_data.action.value)
            # hp and energy update
            opponent_hp_list = self.opponent_hps[current_round]
            opponent_hp_list.append(self.opponent_character_data.hp)
            my_hp_list = self.my_hps[current_round]
            my_hp_list.append(self.my_character_data.hp)
            opponent_energy_list = self.opponent_energy[current_round]
            opponent_energy_list.append(self.opponent_character_data.energy)
            my_energy_list = self.my_energy[current_round]
            my_energy_list.append(self.my_character_data.energy)
            opponent_speed_list = self.opponent_speed[current_round]
            pred_speed_x = + int(self.opponent_character_data.speed_x*1.1 if opponent_speed_list[-1][0] <  self.opponent_character_data.speed_x else + self.opponent_character_data.speed_x * 0.9)
            pred_speed_y = + int(self.opponent_character_data.speed_y*1.1 if opponent_speed_list[-1][1] <  self.opponent_character_data.speed_y else + self.opponent_character_data.speed_y * 0.9)
            # estimate opponent position
            # if the opponent is in hit confirm, the agent should predict the opponent's position based on the impact of the attack
            # otherwise, the agent should predict the opponent's position based on the speed of the opponent
            px = pred_speed_x
            py = pred_speed_y
            if self.my_character_data.hit_confirm:
                px = self.my_character_data.attack_data.impact_x
                py = self.my_character_data.attack_data.impact_y
            opponent_speed_list.append((self.opponent_character_data.speed_x, self.opponent_character_data.speed_y))
                
            
            facing_dir = self.default_dir.get(self.opponent_character_data.front)
            # predict the opponent's the most close box position to the agent
            left = self.opponent_character_data.left
            right = self.opponent_character_data.right
            top = self.opponent_character_data.top
            bottom = self.opponent_character_data.bottom
            px *= int(facing_dir*multiplier)
            py *= int(facing_dir*multiplier)

            x = self.opponent_character_data.x
            y = self.opponent_character_data.y
            # final predicted position
            pred_pos_x = min(max(0, x+px), self.width_game)
            pred_pos_y = min(max(0, y+py), self.height_game)
            pred_left = min(max(0, left+px), self.width_game)
            pred_right = min(max(0, right+px), self.width_game)
            pred_top = min(max(0, top+py), self.height_game)
            pred_bottom = min(max(0, bottom+py), self.height_game)

            opponent_hboxes_list = self.opponent_hboxes[current_round]
            opponent_hboxes_list.append({
                "left": pred_left,
                "right": pred_right,
                "top": pred_top,
                "bottom": pred_bottom
            })
            opponent_curr_pos_list = self.opponent_curr_pos[current_round]
            opponent_curr_pos_list[-1] = (x, y) # update the previous position with true position
            opponent_curr_pos_list.append((pred_pos_x, pred_pos_y)) # add the new predicted position


            px = 0
            py = 0
            if self.opponent_character_data.hit_confirm:
                px = self.opponent_character_data.attack_data.impact_x
                py = self.opponent_character_data.attack_data.impact_y
            
            # My position prediction
            px *= int(facing_dir*multiplier)
            py *= int(facing_dir*multiplier)
    
            x = self.my_character_data.x
            y = self.my_character_data.y
            my_curr_pos_list = self.my_curr_pos[current_round]
            my_curr_pos_list[-1] = (x, y)
            my_curr_pos_list.append((x+px, y+py))
            
            self._increment_counter('me', self.my_character_data.state.value)
            self._increment_counter('opponent', self.opponent_character_data.state.value)

            
            before_exec = time.time()
            # Add clauses to the knowledge base, like the current state, previous state, current position, previous position, facing direction, etc.
            db = self._add_to_db_hp_energy_state()
            # Ground the knowledge base with the new clauses
            lf = self.engine.ground_all(
                db
            )
            # Create the SDD formula from the ground knowledge base
            self.sdd_formula = self.sdd.create_from(lf)
            # Evaluate the SDD formula to get the probabilities of the actions
            result = self.sdd_formula.evaluate()
            after_exec = time.time()

            time_taken_list = self.time_taken[current_round]
            time_taken_list.append(after_exec - before_exec)

            # Select the action to execute based on the probabilities
            action_to_execute = self.select_action_from_problog_results(result)
            action_to_execute = action_to_execute.upper()
            # Sends the action to the game
            self.cc.command_call(action_to_execute)
            my_actions_inferred_list = self.my_actions_inferred[current_round]
            my_actions_inferred_list.append(action_to_execute)

            if self.echo_actions:
                self.echo(f"Action to execute: {action_to_execute}")
            self.count_frames = self.frame_data.current_frame_number
        
    def _get_opp_facing_dir_evd(self):
        """
        not used

        """
        my_facing_dr = self.my_character_data.front
        opp_facing_dir = self.opponent_character_data.front
        diff_facings = my_facing_dr != opp_facing_dir
        self.echo(f"Opp facing dir: {diff_facings}")
        opp_facing_dir_evd = Term("opposite_facing_dir", Term("me"), Term("opponent"), arity=2) 
        return (opp_facing_dir_evd, diff_facings)
    
    def _get_clause_approx_hit_confirm(self):
        """
        not used
        """
        opponent_hps_list = self.opponent_hps[self.frame_data.current_round]
        diff_hp = opponent_hps_list[-1] - self.opponent_character_data.hp

        hit_confirm = int(diff_hp > 0) or int(self.opponent_character_data.hit_confirm)
        return f"approx_hit_confirm({hit_confirm}).\n"
    
    def _get_clause_count_actions(self):
        """
        It was used to create action count clause. It is not used in the final version.
        """
        if self.counter_actions:
            for action, count in self.counter_actions.items():
                yield f"count_action({action}, {count}).\n"
        else:
            yield f"count_action(stand_fb, 1).\n"
    
    def _get_clause_count_total_actions(self):
        """
        It was used to create total actions count clause. It is not used in the final version.
        """
        total = self.counter_actions_total
        return f"count_total_actions({total}).\n"

    def _get_clause_opp_action_type(self):
        """
        It was used to create opponent action type clause. It is not used in the final version.
        """
        opponent_actions_type_list = self.opponent_actions_type[self.frame_data.current_round]
        action_type = opponent_actions_type_list[-1]
        return f"opp_action_type({action_type}).\n"

    def _get_clause_eng_hp(self, player: str):
        """
        Create clauses for the current hp and energy of the player
        Args:
        player (str): Player name. It can be "me" or "opponent"
        """
        hps_list = getattr(self, f'{self.name_conv.get(player)}_hps')[self.frame_data.current_round]
        energy_list = getattr(self, f'{self.name_conv.get(player)}_energy')[self.frame_data.current_round]
        str_hp = f"curr_hp_value({player}, {hps_list[-1]})"
        str_energy = f"curr_energy_value({player}, {energy_list[-1]})"
        return f"{str_hp}.\n", f"{str_energy}.\n"
    
    def _get_clause_count_state(self, player: str):
        """
        Creates clauses for the current state and total states of the player. It is used to estimate the opponent's state.
        Args:
        player (str): Player name. It can be "me" or "opponent
        """
        character = getattr(self, f"{self.name_conv.get(player)}_character_data")
        return f"count_state({character.state.value}, {self.counters[player][character.state.value]}).\n", f"count_total_states({self.counters[player]['total']}).\n"
    
    def _get_clause_prev_hp_energy(self, player: str):
        """
        Creates clauses for the previous hp and energy of the player
        Args:
        player (str): Player name. It can be "me" or "opponent
        """
        prev_hp_list =  getattr(self, f"{self.name_conv.get(player)}_hps")[self.frame_data.current_round]
        prev_energy_list = getattr(self, f"{self.name_conv.get(player)}_energy")[self.frame_data.current_round]
        prev_hp =prev_hp_list[-2]
        prev_energy = prev_energy_list[-2] 
        return f"prev_hp_value({player}, {prev_hp}).\n", f"prev_energy_value({player}, {prev_energy}).\n"
    
    
    def _get_clause_curr_pos(self, player: str):
        """
        Creates clauses for the current position of the player
        Args:
        player (str): Player name. It can be "me" or "opponent
        """
        curr_pos_list = getattr(self, f"{self.name_conv.get(player)}_curr_pos")[self.frame_data.current_round]
        prob = 0.9
        return f"{prob}::curr_pos({player}, {curr_pos_list[-1][0]}, {curr_pos_list[-1][1]}).\n"
    
    def _get_clause_facing_dir(self, player: str):
        """
        Creates clauses for the facing direction of the player
        Args:
        player (str): Player name. It can be "me" or "opponent
        """
        curr_facing_dir = getattr(self, f"{self.name_conv.get(player)}_character_data").front
        curr_facing_dir = self.direction.get(int(curr_facing_dir))
        return f"facing_dir({player}, {curr_facing_dir}).\n"
    
    def _get_clause_my_state(self):
        """
        Creates clauses for the current state of the agent. Used by action utility predicates.
        """
        return f"my_state({self.my_character_data.state.value}).\n"
    
    def _get_hbox_clause(self, player: str):
        """
        Creates clauses for the current hitbox of the player
        Args:
        player (str): Player name. It can be "me" or "opponent
        """
        hboxes_list = getattr(self, f"{self.name_conv.get(player)}_hboxes")[self.frame_data.current_round]
        return f"hbox({player}, [{hboxes_list[-1]['left']}, {hboxes_list[-1]['right']}, {hboxes_list[-1]['top']}, {hboxes_list[-1]['bottom']}]).\n"
    
    def _get_clause_prev_action(self, player: str):
        """
        Creates clauses for the previous action of the player
        Args:
        player (str): Player name. It can be "me" or "opponent
        """

        prev_action_list = getattr(self, f"{self.name_conv.get(player)}_actions")[self.frame_data.current_round]
        return f"prev_action({player},{prev_action_list[-1]}).\n"
        
    
    def _add_to_db_hp_energy_state(self):
        """
        Adds the current hp, energy, state, facing direction, position, previous action, previous hp, previous energy, and hitbox of the agent and the opponent to the knowledge base
        by extending the original knowledge base with the new clauses.
        It gets executed before the inference of the best action.
        """
        db = self.db_org.extend()
        
        my_str_hp, my_str_energy = self._get_clause_eng_hp("me")
        opponent_str_hp, opponent_str_energy = self._get_clause_eng_hp("opponent")
        my_state_clause = self._get_clause_my_state() 
        opponent_state_clause, opponent_total_states_clause = self._get_clause_count_state("opponent")
        my_curr_pos = self._get_clause_curr_pos("me")
        opponent_curr_pos = self._get_clause_curr_pos("opponent")
        # my_hbox = self._get_hbox_clause("me")
        opponent_hbox = self._get_hbox_clause("opponent")
        my_prev_action = self._get_clause_prev_action("me")
        opponent_prev_action = self._get_clause_prev_action("opponent")
        opponent_prev_hp, opponent_prev_energy = self._get_clause_prev_hp_energy("opponent")
        my_prev_hp, my_prev_energy = self._get_clause_prev_hp_energy("me")
        my_facing_dir = self._get_clause_facing_dir("me")
        opponent_facing_dir = self._get_clause_facing_dir("opponent")

        # counters_actions = [action for action in self._get_clause_count_actions()]
        # for clause in counters_actions:
        #     self.clauses_to_add.update({clause: self.clauses_to_add.get(clause, 0) + 1})
        # best_actions_clauses_tuple = sorted(self.clauses_to_add.items(), key=lambda x: x[1], reverse=True)[:self.k_most_prob_actions]
        # best_k_actions_clauses = [clause for clause, _ in best_actions_clauses_tuple]
        # counters_actions_total = self._get_clause_count_total_actions()
       
        
        
        concat_str = "\n".join([
            my_str_hp, my_str_energy, my_state_clause,
            my_curr_pos, my_facing_dir, 
            my_prev_action, my_prev_hp, my_prev_energy])
        for statement in PrologString(concat_str):
            db += statement

        concat_str = "\n".join([
            opponent_str_hp, opponent_str_energy, opponent_state_clause, opponent_total_states_clause, 
            opponent_curr_pos, opponent_prev_energy,opponent_facing_dir, opponent_prev_action,
            opponent_prev_hp, opponent_hbox
        ])
        for statement in PrologString(concat_str):
            db += statement

        return db
    
            
   

    def _increment_counter(self, agent: str, state: str) -> None:
        """
        Increment the counter for the state of the agent
        Args:
        agent (str): Agent name. It can be "me" or "opponent"
        state (str): State of the agent. It can be "stand", "down", "air", or "crouch"
        """
        self.counters[agent][state] += 1
        self.counters[agent]['total'] += 1


    def get_opponent_prev_action_type(self):
        """
        Get the opponent's previous action type
        """
        action_type = actions_type.get(self.opponent_character_data.action.value.upper(), "attack")

        return action_type
    
    def get_my_prev_action_type(self):
        """
        Get the agent's previous action type
        """
        action_type = actions_type.get(self.my_character_data.action.value.upper(), "attack")

        return action_type
        

    def round_end(self, round_result: RoundResult):
        """
        Record the round result and the time taken for the round
        WARNING: The round result is inverted for the agent. The agent's hp is the opponent's hp and vice versa
        WARNING: Sometimes at the end of the last round is not called. It is a bug in the game engine.
        """
        mean_time = np.mean(self.time_taken[self.current_round])
        if self.echo_actions:
            self.echo(f"Mean time taken: {mean_time}")
            self.echo(f" My hp left: {round_result.remaining_hps[self.opponent_number]}, Opponent hp left: {round_result.remaining_hps[self.my_number]}")
        my_final_hp = round_result.remaining_hps[self.opponent_number]# they inverse the index, probably a bug
        opponent_final_hp = round_result.remaining_hps[self.my_number]
        value = "draw"
        if my_final_hp > opponent_final_hp:
            value = "win"
        elif my_final_hp < opponent_final_hp:
            value = "loss"

        self.round_results[self.current_round] = value
        self.my_hps[self.current_round].append(my_final_hp)
        self.opponent_hps[self.current_round].append(opponent_final_hp)
        
        
    def get_screen_data(self, screen_data: ScreenData):
        """
        Get the screen data from the game engine. Used for plotting the game screen
        Args:
        screen_data (ScreenData): Screen data object
        """
        if self.plot_scenes and hasattr(self, 'display_thread') and screen_data.display_bytes:
            try:
                if not screen_data or not screen_data.display_bytes:
                    logger.debug("No display bytes available")
                    return
                if self.display_thread.queue.full():
                    return
                self.display_thread.queue.put_nowait(screen_data.display_bytes)
                
            except queue.Full:
                pass
            except Exception as e:
                logger.error(f"Error queueing screen data: {e}")
            
        self.screen_data_raw = screen_data

    def _init_plots(self):
        """
        Initialize the display thread for plotting the game screen
        """
        if self.plot_scenes:
            self.display_thread = DisplayThread(self.width, self.height)
            self.display_thread.start()


    def game_end(self):
        self.echo("Game End")
    
    def to_dict(self):
        """
        Convert the agent's attributes to a dictionary
        Used for saving the agent's statistics
        """
        return {
            "name": self.name(),
            "my_actions_inferred": self.my_actions_inferred,
            "my_actions_executed": self.my_actions,
            "my_state": self.my_state,
            "opponent_state": self.opponent_state,
            "opponent_energy": self.opponent_energy,
            "my_energy": self.my_energy,
            "opponent_hps": self.opponent_hps,
            "my_hps": self.my_hps,
            "round_results": self.round_results,
            "time_taken": self.time_taken,
            "num_rounds": self.current_round,
            "durations": self.durations,
        }

    def close(self):
        """
        Close the agent
        Save the agent's statistics
        """
        if self.stats_tracker:
            dict_attr = self.to_dict()
            self.stats_tracker.save_stats(dict_attr)
        logger.info("Closing ProblogAgent")
        if hasattr(self, 'display_thread'):
            self.display_thread.stop()
            self.display_thread.join()
