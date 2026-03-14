"""New unit tests for BuildExecutor."""

import subprocess
from pathlib import Path
import pytest
from adibuild.core.executor import BuildExecutor, BuildError, ExecutionResult, ScriptBuilder

def test_executor_check_tools_success(mocker):
    """Test check_tools when all tools exist."""
    mock_execute = mocker.patch.object(BuildExecutor, "execute")
    mock_execute.return_value = ExecutionResult("which tool", 0, "/usr/bin/tool", "", 0.1)
    
    executor = BuildExecutor()
    assert executor.check_tools(["tool1", "tool2"]) is True
    assert mock_execute.call_count == 2

def test_executor_check_tools_failure(mocker):
    """Test check_tools when some tools are missing."""
    mock_execute = mocker.patch.object(BuildExecutor, "execute")
    # First call success, second fails
    mock_execute.side_effect = [
        ExecutionResult("which tool1", 0, "/usr/bin/tool1", "", 0.1),
        ExecutionResult("which tool2", 1, "", "not found", 0.1),
        # Windows fallback if needed
        ExecutionResult("where tool2", 1, "", "not found", 0.1),
    ]
    
    executor = BuildExecutor()
    with pytest.raises(BuildError) as excinfo:
        executor.check_tools(["tool1", "tool2"])
    assert "Required tools not found: tool2" in str(excinfo.value)

def test_executor_execute_basic(mocker):
    """Test basic execution without streaming."""
    mock_process = mocker.Mock()
    # Popen uses process.stdout as a file-like object
    mock_process.stdout.read.return_value = "line1\nline2\n"
    mock_process.wait.return_value = 0
    mocker.patch("subprocess.Popen", return_value=mock_process)
    
    executor = BuildExecutor()
    result = executor.execute("ls", stream_output=False)
    
    assert result.return_code == 0
    assert result.stdout == "line1\nline2"
    assert result.failed is False

def test_executor_execute_failure(mocker):
    """Test execution failure."""
    mock_process = mocker.Mock()
    mock_process.stdout.read.return_value = "error\n"
    mock_process.wait.return_value = 1
    mocker.patch("subprocess.Popen", return_value=mock_process)
    
    executor = BuildExecutor()
    result = executor.execute("ls", stream_output=False)
    
    assert result.return_code == 1
    assert result.failed is True

def test_executor_make_basic(mocker):
    """Test make command execution."""
    mock_execute = mocker.patch.object(BuildExecutor, "execute")
    mock_execute.return_value = ExecutionResult(["make", "all"], 0, "ok", "", 0.1)
    
    executor = BuildExecutor()
    result = executor.make("all")
    
    assert result.return_code == 0
    mock_execute.assert_called_once()
    args, kwargs = mock_execute.call_args
    assert "make" in args[0]
    assert "all" in args[0]

def test_executor_cmake_basic(mocker):
    """Test cmake command execution."""
    mock_execute = mocker.patch.object(BuildExecutor, "execute")
    mock_execute.return_value = ExecutionResult(["cmake"], 0, "ok", "", 0.1)
    
    executor = BuildExecutor()
    initial_cwd = executor.cwd
    build_dir = Path("/tmp/build")
    result = executor.cmake([".."], build_dir=build_dir)
    
    assert result.return_code == 0
    mock_execute.assert_called_once()
    # Check that it changed cwd and restored it
    assert executor.cwd == initial_cwd

def test_script_builder_basic(tmp_path):
    """Test ScriptBuilder writes commands to file."""
    script_path = tmp_path / "build.sh"
    sb = ScriptBuilder(script_path)
    
    sb.write_comment("Start build")
    sb.write_command("ls -l", cwd=Path("/tmp"), env={"FOO": "bar"})
    
    content = script_path.read_text()
    assert "#!/bin/bash" in content
    assert "# Start build" in content
    assert "mkdir -p /tmp" in content
    assert "cd /tmp" in content
    assert "export FOO='bar'" in content
    assert "ls -l" in content

def test_executor_execute_streaming(mocker):
    """Test execution with streaming output."""
    mock_process = mocker.Mock()
    # Mock stdout as an iterable of lines
    mock_process.stdout = ["line1\n", "line2\n"]
    mock_process.wait.return_value = 0
    mocker.patch("subprocess.Popen", return_value=mock_process)
    
    executor = BuildExecutor()
    result = executor.execute("ls", stream_output=True)
    
    assert result.return_code == 0
    assert result.stdout == "line1\nline2"

def test_executor_execute_with_log_file(mocker, tmp_path):
    """Test execution with log file."""
    log_file = tmp_path / "build.log"
    mock_process = mocker.Mock()
    mock_process.stdout.read.return_value = "output data\n"
    mock_process.wait.return_value = 0
    mocker.patch("subprocess.Popen", return_value=mock_process)
    
    executor = BuildExecutor(log_file=log_file)
    executor.execute("ls", stream_output=False)
    
    assert log_file.exists()
    content = log_file.read_text()
    assert "Command: ls" in content
    assert "output data" in content

def test_executor_extract_errors():
    """Test extracting errors from output."""
    executor = BuildExecutor()
    output = "Some warning\nerror: something went wrong\nfatal: boom\nnormal line"
    errors = executor._extract_errors(output)
    assert len(errors) == 2
    assert "error: something went wrong" in errors
    assert "fatal: boom" in errors

def test_executor_style_output_line():
    """Test styling output lines."""
    executor = BuildExecutor()
    assert executor._style_output_line("error: oops").style == "bold red"
    assert executor._style_output_line("warning: heads up").style == "yellow"
    # rich.Text.style is "" if not set
    assert executor._style_output_line("just a line").style == ""

def test_executor_keyboard_interrupt(mocker):
    """Test keyboard interrupt handling."""
    mock_process = mocker.Mock()
    # Raising KeyboardInterrupt during wait
    mock_process.wait.side_effect = KeyboardInterrupt()
    mocker.patch("subprocess.Popen", return_value=mock_process)
    
    executor = BuildExecutor()
    with pytest.raises(KeyboardInterrupt):
        executor.execute("ls", stream_output=False)
    
    mock_process.terminate.assert_called_once()
