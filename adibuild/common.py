import subprocess
import logging
import time

import git

log = logging.getLogger(__name__)


class Common:

    timeout = 60*60*4  # 4 hours

    _log_output = False
    _log_output_file = "log.txt"
    _log_commands = False
    _log_commands_file = "commands.txt"

    def _get_git_commit(self, repo_path=None, tag_check=False):
        if repo_path is None:
            repo_path = "."
        try:
            repo = git.Repo(repo_path)
            if tag_check:
                # Check if the current commit is tagged
                tags = repo.tags
                return bool(tags)
            commit_hash = repo.head.commit.hexsha
            return commit_hash
        except git.exc.InvalidGitRepositoryError:
            log.warning(f"No git repository found at {repo_path}")
            return None


    def _run_shell_cmd(self, cmd):
        log.debug(f"Running shell command: {cmd}")

        # Split && separated commands into a list
        if self._log_commands:
            log.info(f"Logging commands to file: {self._log_commands_file}")
            cmd_no_and = cmd.split("&&")
            with open(self._log_commands_file, "a") as f:
                for c in cmd_no_and:
                    f.write(c.strip() + "\n")

        cmd = ["/bin/bash", "-c", cmd]

        # Start the process
        process = subprocess.Popen(
            cmd,  # Replace with your actual command and arguments
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Ensures output is in string format instead of bytes
        )

        # Monitor output and errors in real-time
        stdout = []
        stderr = []
        start_time = time.time()
        while process.poll() is None:
            for line in process.stdout:
                log.debug(f"STDOUT: {line.strip()}")
                stdout.append(line.strip())

            for line in process.stderr:
                log.debug(f"STDERR: {line.strip()}")
                stderr.append(line.strip())

            # Check for timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > self.timeout:
                log.error(f"Command timed out after {self.timeout} seconds")
                process.kill()
                raise TimeoutError("Command timed out")
            
        # Wait for process to complete
        # process.wait()

        if self._log_output:
            log.info(f"Logging output to file: {self._log_output_file}")
            with open(self._log_output_file, "a") as f:
                f.write("STDOUT:\n")
                f.write("\n".join(stdout))
                f.write("\n")
                f.write("STDERR:\n")
                f.write("\n".join(stderr))
                f.write("\n")
                f.write("ERROR:\n")
                f.write(str(process.returncode))
                f.write("\n")

        # Get exit code
        exit_code = process.returncode
        log.debug(f"Process exited with code {exit_code}")

        return stdout, stderr, exit_code

    def _shell_out(self, script):
        # Run shell command so we see the output as it happens
        log.info("Running command: " + script)
        p = subprocess.Popen(
            script, shell=True, executable="/bin/bash", stdout=subprocess.PIPE
        )

    def _shell_out2(self, script):
        log.info("Running command: " + script)
        # p = subprocess.Popen(script, shell=True, executable="/bin/bash",stdout=subprocess.PIPE)
        # p = subprocess.Popen([script], executable="/bin/bash",stdout=subprocess.PIPE)
        # output, err = p.communicate()
        try:
            output = subprocess.check_output(
                script, shell=True, executable="/bin/bash", stderr=subprocess.STDOUT
            )
            # log.info(output)
            print(output.decode("utf-8"))
            return True
        except Exception as ex:
            # log.error("XSDB failed on command: " + script)
            # log.error("msg: " + str(ex))
            print("XSDB failed on command: " + script)
            print("msg: " + str(ex))
        return False
        # logging.info(output.decode("utf-8"))
        # return output.decode("utf-8")
