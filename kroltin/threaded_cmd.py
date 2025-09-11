import subprocess
from threading import Thread
import logging


logger = logging.getLogger(__name__)


def run_command_stream(cmd, cwd=None, env=None):
    """
    Run a command and stream stdout/stderr as lines arrive.

    Returns (returncode, stdout, stderr) where stdout/stderr are the
    captured full outputs (joined by newlines). Lines are printed to
    the process stdout/stderr as they arrive and also logged.
    """
    # Start the subprocess with pipes for stdout/stderr
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=cwd,
        env=env,
    )

    stdout_lines = []
    stderr_lines = []

    def _reader(pipe, collector, log_fn, is_err=False):
        try:
            for line in iter(pipe.readline, ''):
                if line == '':
                    break
                line = line.rstrip('\n')
                collector.append(line)
                print(line, flush=True)
                try:
                    if is_err:
                        log_fn.error(line)
                    else:
                        log_fn.info(line)
                except Exception:
                    pass
        finally:
            try:
                pipe.close()
            except Exception:
                pass

    t_out = Thread(target=_reader, args=(process.stdout, stdout_lines, logger.info, False))
    t_err = Thread(target=_reader, args=(process.stderr, stderr_lines, logger.error, True))
    t_out.start()
    t_err.start()

    # Wait for threads to finish reading
    t_out.join()
    t_err.join()

    returncode = process.wait()

    return returncode, "\n".join(stdout_lines), "\n".join(stderr_lines)