"""Console Engine."""
from typing import Dict, Any
from .console import ConsoleCommand, ConsoleResponse

class ConsoleEngine:
    def __init__(self)->None:self._commands:Dict[str,Any]={
        "help":"Show available commands","status":"Show system status",
        "workflows":"List workflows","policies":"List policies",
    }
    def execute(self,cmd:ConsoleCommand)->ConsoleResponse:
        if cmd.command in self._commands:
            return ConsoleResponse(command=cmd.command,success=True,data={"info":self._commands[cmd.command]})
        return ConsoleResponse(command=cmd.command,success=False,error=f"Unknown command: {cmd.command}")
    def list_commands(self)->Dict[str,Any]:return dict(self._commands)
