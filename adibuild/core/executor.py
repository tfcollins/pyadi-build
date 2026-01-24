"""Build command execution and output handling."""

import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.text import Text

from adibuild.utils.logger import get_logger


class BuildError(Exception):
    """Exception raised for build errors."""

    pass


@dataclass
class ExecutionResult:
    """Result of command execution."""

    command: str
    return_code: int
    stdout: str
    stderr: str
    duration: float

    @property
    def success(self) -> bool:
        """Check if command succeeded."""
        return self.return_code == 0

    @property
    def failed(self) -> bool:
        """Check if command failed."""
        return self.return_code != 0


class BuildExecutor:
    """Executes build commands with streaming output and error handling."""

    # Patterns to detect errors and warnings in build output
    ERROR_PATTERNS = [
        re.compile(r"error:", re.IGNORECASE),
        re.compile(r"fatal:", re.IGNORECASE),
        re.compile(r"undefined reference", re.IGNORECASE),
        re.compile(r"cannot find", re.IGNORECASE),
    ]

    WARNING_PATTERNS = [
        re.compile(r"warning:", re.IGNORECASE),
        re.compile(r"deprecated", re.IGNORECASE),
    ]

    def __init__(self, cwd: Path | None = None, log_file: Path | None = None):
        """
        Initialize BuildExecutor.

        Args:
            cwd: Working directory for commands
            log_file: Optional file to log command output
        """
        self.cwd = cwd or Path.cwd()
        self.log_file = log_file
        self.logger = get_logger("adibuild.executor")
        self.console = Console(stderr=True)

        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def execute(
        self,
        command: str | list[str],
        env: dict[str, str] | None = None,
        stream_output: bool = True,
        capture_output: bool = True,
    ) -> ExecutionResult:
        """
        Execute command with optional output streaming.

        Args:
            command: Command to execute (string or list)
            env: Optional environment variables (merged with current env)
            stream_output: Stream output in real-time to console
            capture_output: Capture output to result

        Returns:
            ExecutionResult

        Raises:
            BuildError: If command execution fails
        """
        # Prepare command
        if isinstance(command, list):
            cmd_str = " ".join(command)
            cmd_list = command
        else:
            cmd_str = command
            cmd_list = ["bash", "-c", command]

        self.logger.info(f"Executing: {cmd_str}")

        # Prepare environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        # Prepare output capture
        stdout_lines = []
        stderr_lines = []

        # Open log file if specified
        log_handle = None
        if self.log_file:
            log_handle = open(self.log_file, "a")
            log_handle.write(f"\n{'='*80}\n")
            log_handle.write(f"Command: {cmd_str}\n")
            log_handle.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_handle.write(f"{'='*80}\n\n")

        start_time = time.time()

        try:
            # Execute command
            process = subprocess.Popen(
                cmd_list,
                cwd=self.cwd,
                env=exec_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                text=True,
                bufsize=1,
            )

            # Stream and capture output
            if stream_output:
                for line in process.stdout:
                    line = line.rstrip()
                    if capture_output:
                        stdout_lines.append(line)

                    # Color-code errors and warnings
                    styled_line = self._style_output_line(line)
                    self.console.print(styled_line, highlight=False)

                    # Write to log file
                    if log_handle:
                        log_handle.write(line + "\n")
                        log_handle.flush()
            else:
                # Just capture without streaming
                stdout = process.stdout.read()
                if capture_output:
                    stdout_lines = stdout.splitlines()
                if log_handle:
                    log_handle.write(stdout)

            # Wait for process to complete
            return_code = process.wait()

            duration = time.time() - start_time

            # Create result
            result = ExecutionResult(
                command=cmd_str,
                return_code=return_code,
                stdout="\n".join(stdout_lines) if capture_output else "",
                stderr="\n".join(stderr_lines) if capture_output else "",
                duration=duration,
            )

            # Log completion
            if result.success:
                self.logger.info(f"Command completed successfully in {duration:.1f}s")
            else:
                self.logger.error(
                    f"Command failed with return code {return_code} after {duration:.1f}s"
                )

            if log_handle:
                log_handle.write(f"\nReturn code: {return_code}\n")
                log_handle.write(f"Duration: {duration:.1f}s\n")

            return result

        except subprocess.SubprocessError as e:
            raise BuildError(f"Failed to execute command: {e}") from e

        except KeyboardInterrupt:
            self.logger.warning("Command interrupted by user")
            if process:
                process.terminate()
                process.wait(timeout=5)
            raise

        finally:
            if log_handle:
                log_handle.close()

    def make(
        self,
        target: str | None = None,
        jobs: int | None = None,
        env: dict[str, str] | None = None,
        extra_args: list[str] | None = None,
    ) -> ExecutionResult:
        """
        Execute make command.

        Args:
            target: Make target (None for default target)
            jobs: Number of parallel jobs (-j flag)
            env: Optional environment variables
            extra_args: Additional make arguments

        Returns:
            ExecutionResult

        Raises:
            BuildError: If make fails
        """
        cmd = ["make"]

        # Add parallel jobs
        if jobs and jobs > 1:
            cmd.append(f"-j{jobs}")

        # Add extra arguments
        if extra_args:
            cmd.extend(extra_args)

        # Add target
        if target:
            cmd.append(target)

        result = self.execute(cmd, env=env)

        if result.failed:
            # Extract and highlight errors
            errors = self._extract_errors(result.stdout)
            error_msg = f"Make failed with return code {result.return_code}"
            if errors:
                error_msg += "\n\nErrors found:\n" + "\n".join(f"  • {e}" for e in errors[:5])
                if len(errors) > 5:
                    error_msg += f"\n  ... and {len(errors) - 5} more errors"

            raise BuildError(error_msg)

        return result

    def _style_output_line(self, line: str) -> Text:
        """
        Style output line with colors based on content.

        Args:
            line: Output line

        Returns:
            Rich Text object with styling
        """
        # Check for errors
        for pattern in self.ERROR_PATTERNS:
            if pattern.search(line):
                return Text(line, style="bold red")

        # Check for warnings
        for pattern in self.WARNING_PATTERNS:
            if pattern.search(line):
                return Text(line, style="yellow")

        # Default styling
        return Text(line)

    def _extract_errors(self, output: str) -> list[str]:
        """
        Extract error messages from build output.

        Args:
            output: Build output

        Returns:
            List of error messages
        """
        errors = []
        for line in output.splitlines():
            for pattern in self.ERROR_PATTERNS:
                if pattern.search(line):
                    errors.append(line.strip())
                    break
        return errors

    def check_tool(self, tool: str) -> bool:
        """
        Check if a tool is available.

        Args:
            tool: Tool name

        Returns:
            True if tool is available

        Raises:
            BuildError: If tool is not found
        """
        result = self.execute(
            f"which {tool}",
            stream_output=False,
            capture_output=True,
        )

        if result.failed:
            raise BuildError(f"Required tool '{tool}' not found in PATH")

        return True

    def check_tools(self, tools: list[str]) -> bool:
        """
        Check if multiple tools are available.

        Args:
            tools: List of tool names

        Returns:
            True if all tools are available

        Raises:
            BuildError: If any tool is not found
        """
        missing = []
        for tool in tools:
            try:
                self.check_tool(tool)
            except BuildError:
                missing.append(tool)

        if missing:
            raise BuildError(
                f"Required tools not found: {', '.join(missing)}. "
                "Please install these tools before continuing."
            )

        return True
