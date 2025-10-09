import shlex
import signal
import atexit
import logging
import subprocess
import psutil
from threading import Thread


logger = logging.getLogger(__name__)


class CommandRunner:
    _children = set()
    _signal_handlers_installed = False

    def __init__(self, logger_obj=None):
        self.logger = logger_obj or logger
        type(self)._install_signal_handlers_once()

    def run_command_stream(self, cmd, cwd=None, env=None):
        """Run a command and return (rc, stdout, stderr)."""
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)

        logger.debug(f"Executing command: {' '.join(cmd)}")
        rc, out, err = self._spawn(cmd, cwd=cwd, env=env)

        return rc, out, err

    # ----------------------------------------------------------------------
    # Spawn / Streaming Methods
    # ----------------------------------------------------------------------

    def _spawn(self, cmd, cwd, env):
        """Spawn a subprocess, stream its stdout/stderr to the logger, and
        return (returncode, stdout_text, stderr_text).
        """
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            bufsize=1,
            cwd=cwd,
            env=env,
            close_fds=True,
            start_new_session=True,
        )

        self._register_child(p)

        stdout_lines, stderr_lines = [], []

        def _reader(pipe, collector, is_err=False):
            try:
                for line in iter(pipe.readline, ""):
                    if not line:
                        break
                    line = line.rstrip("\n")
                    collector.append(line)
                    (logger.error if is_err else logger.info)(line)
            finally:
                try:
                    pipe.close()
                except Exception:
                    pass

        t_out = Thread(target=_reader, args=(p.stdout, stdout_lines, False), daemon=True)
        t_err = Thread(target=_reader, args=(p.stderr, stderr_lines, True), daemon=True)
        t_out.start()
        t_err.start()

        try:
            rc = p.wait()
        except KeyboardInterrupt:
            self._kill_process_group(p, signal.SIGTERM)
            try:
                p.wait(timeout=5)
            except Exception:
                self._kill_process_group(p, signal.SIGKILL)
            rc = p.returncode if p.returncode is not None else 130
        finally:
            t_out.join(timeout=1)
            t_err.join(timeout=1)
            self._unregister_child(p)

        return rc, "\n".join(stdout_lines), "\n".join(stderr_lines)

    # ----------------------------------------------------------------------
    # Child Registry
    # ----------------------------------------------------------------------

    @classmethod
    def _register_child(cls, p):
        cls._children.add(p)

    @classmethod
    def _unregister_child(cls, p):
        cls._children.discard(p)


    # ----------------------------------------------------------------------
    # Signal/Exit Handlers
    # ----------------------------------------------------------------------

    @classmethod
    def _install_signal_handlers_once(cls):
        if cls._signal_handlers_installed:
            return

        def _handler(signum, frame):
            cls._cleanup_all()
            raise SystemExit(128 + signum)

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _handler)
            except Exception:
                pass

        atexit.register(cls._cleanup_all)
        cls._signal_handlers_installed = True
    
    # ----------------------------------------------------------------------
    # Process Cleanup
    # ----------------------------------------------------------------------

    @classmethod
    def _kill_process_group(cls, p, sig=signal.SIGTERM):
        """Kill the entire process tree for the process "p" using psutil.

        This implementation enumerates the process and its descendants,
        attempts to send the requested signal, waits briefly and escalates
        to SIGKILL if necessary. Any processes that remain are logged as
        warnings.
        """
        pid = getattr(p, "pid", None)
        if pid is None:
            return

        try:
            root = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return

        procs = [root] + root.children(recursive=True)
        for proc in procs:
            try:
                proc.send_signal(sig)
            except Exception:
                pass

        gone, alive = psutil.wait_procs(procs, timeout=3)
        if alive:
            for proc in alive:
                try:
                    proc.kill()
                except Exception:
                    pass
            gone2, alive2 = psutil.wait_procs(alive, timeout=3)
            if alive2:
                for proc in alive2:
                    try:
                        pid = proc.pid
                        name = proc.name()
                        cmdline = " ".join(proc.cmdline()) if proc.cmdline() else ""
                        logger.warning(f"Process did not terminate after kill: pid={pid} name={name} cmdline={cmdline}")
                    except Exception:
                        try:
                            logger.warning(f"Process did not terminate after kill: pid={proc.pid}")
                        except Exception:
                            logger.warning("Process did not terminate after kill: unknown process")

    @classmethod
    def _cleanup_all(cls):
        for p in list(cls._children):
            cls._kill_process_group(p, signal.SIGTERM)
        for p in list(cls._children):
            try:
                p.wait(timeout=3)
            except Exception:
                cls._kill_process_group(p, signal.SIGKILL)