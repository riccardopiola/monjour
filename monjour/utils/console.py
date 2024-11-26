import subprocess
import platform

from monjour.core import log

def launch_program(command: list[str], window=True, close_shell=True, **kwargs) -> int:
    """
    Creates an external console with the external program running in it.

    Args:
        command: The command to run in the external console.
        shell:   Whether to run the command in a shell.
        close_shell: Whether to close the shell after the command has completed
    """
    msg = f"Launching external program, {command}"
    if not close_shell:
        msg += " (Close the terminal window to continue)"
    log.info(msg)
    if not window:
        proc = subprocess.Popen(command, **kwargs)
        return proc.wait()

    system = platform.system()
    if system == "Windows":
        arg = '/c' if close_shell else '/k'
        proc = subprocess.Popen(['cmd.exe', arg] + command, creationflags=subprocess.CREATE_NEW_CONSOLE)
        return proc.wait()
    elif system == "Darwin":  # macOS
        proc =  subprocess.Popen(['open', '-a', 'Terminal', '-n', '--args'] + command)
        return proc.wait()
    elif system == "Linux":
        # TODO: Check if a graphical environment is available
        proc = subprocess.Popen(['xterm', '-e'] + command)
        return proc.wait()
    else:
        log.warning("Unsupported operating system for launch_program. Falling back to subprocess.run")
        proc = subprocess.Popen(command)
        return proc.wait()
