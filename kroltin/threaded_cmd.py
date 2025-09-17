
import subprocess
from threading import Thread
import logging
from kroltin.run import register_cleanup

logger = logging.getLogger(__name__)


_running_processes = []
_running_threads = []

def cleanup_all_threaded_cmd():
    # Terminate all running subprocesses and join threads
    for proc in list(_running_processes):
        try:
            proc.terminate()
        except Exception:
            pass
    for t in list(_running_threads):
        if t.is_alive():
            try:
                t.join(timeout=1)
            except Exception:
                pass

if register_cleanup:
    register_cleanup(cleanup_all_threaded_cmd)

def run_command_stream(cmd, cwd=None, env=None):
    """
    Run a command and stream stdout/stderr as lines arrive.
    Returns (returncode, stdout, stderr) where stdout/stderr are the
    captured full outputs (joined by newlines). Lines are printed to
    the process stdout/stderr as they arrive and also logged.
    """
    logger = logging.getLogger(__name__)

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
    _running_processes.append(process)

    stdout_lines = []
    stderr_lines = []

    def _reader(pipe, collector, log_fn, is_err=False):
        try:
            for line in iter(pipe.readline, ''):
                if line == '':
                    break
                line = line.rstrip('\n')
                collector.append(line)
                logger.debug(line)
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

    logger.debug(f"Executing command: {' '.join(cmd)}")


    t_out = Thread(target=_reader, args=(process.stdout, stdout_lines, logger.debug, False))
    t_err = Thread(target=_reader, args=(process.stderr, stderr_lines, logger.error, True))
    t_out.daemon = True
    t_err.daemon = True
    t_out.start()
    t_err.start()
    _running_threads.extend([t_out, t_err])

    # Wait for threads to finish reading
    try:
        t_out.join()
        t_err.join()
        returncode = process.wait()
    except KeyboardInterrupt:
        try:
            process.terminate()
        except Exception:
            pass
        returncode = -1
    finally:
        if process in _running_processes:
            _running_processes.remove(process)
        for t in [t_out, t_err]:
            if t in _running_threads:
                _running_threads.remove(t)

    return returncode, "\n".join(stdout_lines), "\n".join(stderr_lines)