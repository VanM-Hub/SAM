"""
Execution Sandbox — isolasi eksekusi untuk filesystem, command, workspace.

Semua executor awal berjalan di dalam sandbox.
Sandbox mencatat semua aksi tanpa menjalankannya di sistem nyata.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum
import os
import tempfile


class SandboxOperationType(str, Enum):
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    FILE_BACKUP = "file_backup"
    FILE_RESTORE = "file_restore"
    COMMAND_EXECUTE = "command_execute"
    PROCESS_START = "process_start"
    PROCESS_STOP = "process_stop"
    PROCESS_KILL = "process_kill"
    NETWORK_CONNECT = "network_connect"
    DATABASE_COMMAND = "database_command"


@dataclass(frozen=True)
class SandboxOperation:
    """Satu operasi yang tercatat di sandbox."""
    operation_type: SandboxOperationType
    target: str                          # file path, command, process name
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    simulated_result: str = "completed"

    def to_text(self) -> str:
        return "[{ts}] {typ} -> {target} ({result})".format(
            ts=self.timestamp[-8:],
            typ=self.operation_type.value,
            target=self.target[:60],
            result=self.simulated_result,
        )


class ExecutionSandbox:
    """Sandbox untuk isolasi eksekusi.

    Semua aksi dicatat — tidak ada yang dijalankan di sistem nyata.
    Method utama:
      execute_op(type, target, params) -> str
      get_operations(limit) -> List[SandboxOperation]
      clear()

    Penggunaan:
      sandbox = ExecutionSandbox()
      result = sandbox.execute_op(SandboxOperationType.FILE_WRITE, "/tmp/test.txt", {"content": "test"})
    """

    def __init__(self, base_path: Optional[str] = None):
        self._operations: List[SandboxOperation] = []
        self._allowed_paths: List[str] = []
        self._allowed_commands: List[str] = []
        self._base_path = base_path or os.path.join(tempfile.gettempdir(), "sam_sandbox")

        # Default allowed paths
        sandbox = os.path.join(self._base_path, "files")
        self._allowed_paths = [sandbox]
        os.makedirs(sandbox, exist_ok=True)

        # Default allowed commands
        self._allowed_commands = [
            "echo", "dir", "ls", "whoami", "pwd", "date", "time",
            "python --version", "pip list", "git status",
        ]

    def execute_op(self, operation_type: SandboxOperationType,
                   target: str, parameters: Dict[str, Any] = None) -> str:
        """Eksekusi satu operasi di sandbox.

        Args:
            operation_type: Tipe operasi
            target: Target (path, command, name)
            parameters: Parameter tambahan

        Returns:
            str: Hasil simulasi

        Raises:
            ValueError: Jika target tidak diizinkan
        """
        parameters = parameters or {}

        # Validate
        if operation_type in (SandboxOperationType.FILE_READ,
                              SandboxOperationType.FILE_WRITE,
                              SandboxOperationType.FILE_DELETE,
                              SandboxOperationType.FILE_BACKUP,
                              SandboxOperationType.FILE_RESTORE):
            if not self._is_path_allowed(target):
                raise ValueError("Path not allowed: {}. Allowed: {}".format(target, self._allowed_paths))

        elif operation_type == SandboxOperationType.COMMAND_EXECUTE:
            if not self._is_command_allowed(target):
                raise ValueError("Command not allowed: {}. Allowed: {}".format(target, self._allowed_commands))

        # Record
        op = SandboxOperation(
            operation_type=operation_type,
            target=target,
            parameters=parameters,
            simulated_result="completed",
        )
        self._operations.append(op)

        # Simulate
        if operation_type == SandboxOperationType.FILE_WRITE:
            content = parameters.get("content", "")
            safe_path = os.path.join(self._base_path, "files",
                                     target.lstrip("/").lstrip("\\").replace(":", "").replace("\\", "_").replace("/", "_"))
            with open(safe_path, "w") as f:
                f.write(content)
            return "Simulated write: {} -> {}".format(target, safe_path)

        elif operation_type == SandboxOperationType.FILE_DELETE:
            return "Simulated delete: {}".format(target)

        elif operation_type == SandboxOperationType.FILE_READ:
            return "Simulated read: {} ({} bytes)".format(target, len(parameters.get("content", "")))

        elif operation_type == SandboxOperationType.COMMAND_EXECUTE:
            return "Simulated command: {} -> exit code 0".format(target)

        elif operation_type == SandboxOperationType.DATABASE_COMMAND:
            return "Simulated DB: {} -> OK".format(target)

        elif operation_type == SandboxOperationType.PROCESS_START:
            return "Simulated start: {}".format(target)

        elif operation_type == SandboxOperationType.PROCESS_STOP:
            return "Simulated stop: {}".format(target)

        return "Simulated: {} -> completed".format(target)

    def get_operations(self, limit: int = 50) -> List[SandboxOperation]:
        """Dapatkan daftar operasi yang tercatat."""
        return self._operations[-limit:]

    def get_log(self) -> str:
        """Dapatkan log semua operasi."""
        if not self._operations:
            return "No sandbox operations."
        return "\n".join(op.to_text() for op in self._operations)

    def count(self) -> int:
        return len(self._operations)

    def clear(self):
        """Bersihkan semua operasi (testing only)."""
        self._operations.clear()

    def add_allowed_path(self, path: str):
        """Tambah path yang diizinkan."""
        self._allowed_paths.append(path)

    def add_allowed_command(self, command: str):
        """Tambah command yang diizinkan."""
        self._allowed_commands.append(command)

    def _is_path_allowed(self, target: str) -> bool:
        """Cek apakah path diizinkan."""
        for allowed in self._allowed_paths:
            if target.startswith(allowed):
                return True
            if allowed in target:
                return True
        return False

    def _is_command_allowed(self, target: str) -> bool:
        """Cek apakah command diizinkan."""
        for allowed in self._allowed_commands:
            if target.strip().startswith(allowed.split()[0]):
                return True
        return False
