import asyncio
import typer
import sys
import os
import pathlib

sys.path.append(os.path.join(pathlib.Path(os.path.dirname(__file__)).parent))


from typing_extensions import Annotated, Optional
from pyftg.socket.aio.gateway import Gateway
from pyftg.utils.logging import DEBUG, set_logging

from problog_agent.ProblogAgent import ProblogAgent

app = typer.Typer(pretty_exceptions_enable=False)
from StatsTracker import StatsTracker

async def start_process(
        host:str , port: int, character: str = "ZEN", game_number: int = 1, keep_stats: bool = False,  echo_actions: bool = False,
        plot_scenes: bool = False
    ):
        """
        Start the process to run the game between the PrologAgent and the chosen agent.
        The chosen agent can be the PrologAI, the MctsAi or MctsAi23i.

        Parameters:
        host (str): The host used by DareFightingICE
        port (int): The port used by DareFightingICE
        character (str): The character to be used in the game
        game_number (int): The number of games to be played
        keep_stats (bool): Flag to indicate if the statistics should be kept
        echo_actions (bool): Flag to indicate if the actions should be echoed
        plot_scenes (bool): Flag to indicate if the scenes should be plotted
        """


        gateway = Gateway(host, port)
            
        
        
        name_agent = "MctsAi23i"

        if keep_stats:
            stats_tracker= StatsTracker(name_agent, "ProblogAgent")
            a2 = ProblogAgent(plot_scenes=plot_scenes, stats_tracker=stats_tracker, echo_actions=echo_actions)
        else:
            a2 = ProblogAgent(plot_scenes=plot_scenes, echo_actions=echo_actions)
        gateway.register_ai("ProblogAgent", a2)
        await gateway.run_game([character, character], [name_agent,"ProblogAgent"], game_number)
        

    
    



@app.command()
def main(
        host: Annotated[Optional[str], typer.Option(help="Host used by DareFightingICE")] = "127.0.0.1",
        port: Annotated[Optional[int], typer.Option(help="Port used by DareFightingICE")] = 31415,
        plot_scenes: Annotated[Optional[bool], typer.Option(help="Plot the scenes")] = False,
        # a1: Annotated[Optional[str], typer.Option(help="The AI name to use for player 1")] = None,
        # a2: Annotated[Optional[str], typer.Option(help="The AI name to use for player 2")] = None
    ):
    
    typer.echo(f"Starting the process with host: {host}, port: {port}")
    asyncio.run(start_process(host, port, plot_scenes=plot_scenes, echo_actions=False, keep_stats=True))
    

if __name__ == '__main__':
    set_logging(log_level=DEBUG)
    app()