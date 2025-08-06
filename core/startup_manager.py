import subprocess
import sys
import os

class StartupManager:
    TASK_NAME = "FaceLockStartup"

    def _get_executable_path(self):
        # Gets the path to the pythonw.exe if running from source,
        # or the .exe file if compiled.
        if getattr(sys, 'frozen', False):
            return sys.executable
        else:
            # For development, this creates a command that runs the script
            # with the pythonw.exe interpreter to avoid a console window.
            python_exe = sys.executable.replace("python.exe", "pythonw.exe")
            script_path = os.path.abspath("main.py")
            return f'"{python_exe}" "{script_path}"'

    def is_task_created(self):
        try:
            command = f'schtasks /Query /TN "{self.TASK_NAME}"'
            result = subprocess.run(command, check=True, capture_output=True, shell=True)
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False

    def create_startup_task(self):
        if self.is_task_created():
            return True, "Task already exists."

        exe_path = self._get_executable_path()
        command = (
            f'schtasks /Create /SC ONLOGON /TN "{self.TASK_NAME}" '
            f'/TR {exe_path} /RL HIGHEST /F'
        )
        try:
            subprocess.run(command, check=True, shell=True, capture_output=True)
            return True, "Task created successfully."
        except subprocess.CalledProcessError as e:
            return False, f"Failed to create task: {e.stderr.decode()}"

    def delete_startup_task(self):
        if not self.is_task_created():
            return True, "Task does not exist."

        command = f'schtasks /Delete /TN "{self.TASK_NAME}" /F'
        try:
            subprocess.run(command, check=True, shell=True, capture_output=True)
            return True, "Task deleted successfully."
        except subprocess.CalledProcessError as e:
            return False, f"Failed to delete task: {e.stderr.decode()}"