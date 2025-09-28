import os
import shlex
import signal
import atexit
import logging
import subprocess
from threading import Thread

logger = logging.getLogger(__name__)

_children = set()

def _register_child(p):
    _children.add(p)

def _unregister_child(p):
    _children.discard(p)

def _kill_process_group(p, sig=signal.SIGTERM):
    try:
        pgid = os.getpgid(p.pid)
        os.killpg(pgid, sig)
    except Exception:
        try:
            p.terminate()
        except Exception:
            pass

def _cleanup_all():
    for p in list(_children):
        _kill_process_group(p, signal.SIGTERM)
    for p in list(_children):
        try:
            p.wait(timeout=3)
        except Exception:
            _kill_process_group(p, signal.SIGKILL)

def _install_signal_handlers_once():
    installed = getattr(_install_signal_handlers_once, "_done", False)
    if installed:
        return
    def _handler(signum, frame):
        _cleanup_all()
        raise SystemExit(128 + signum)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handler)
        except Exception:
            pass
    atexit.register(_cleanup_all)
    _install_signal_handlers_once._done = True

_install_signal_handlers_once()

def _detect_vm_type(cmd):
    s = " ".join(cmd) if isinstance(cmd, (list, tuple)) else str(cmd)
    s = s.lower()
    if any(t in s for t in ("virtualbox-iso", "virtualbox", "source.virtualbox-iso")):
        return "virtualbox"
    if any(t in s for t in ("vmware-iso", "vmware", "source.vmware-iso")):
        return "vmware"
    return None

def _env_for(vm_type, base_env=None):
    e = (base_env or os.environ).copy()
    if vm_type == "virtualbox":
        e.pop("LD_LIBRARY_PATH", None)
    return e

def _spawn(cmd, cwd, env):
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
    _register_child(p)
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
        _kill_process_group(p, signal.SIGTERM)
        try:
            p.wait(timeout=5)
        except Exception:
            _kill_process_group(p, signal.SIGKILL)
        rc = p.returncode if p.returncode is not None else 130
    finally:
        t_out.join(timeout=1)
        t_err.join(timeout=1)
        _unregister_child(p)

    return rc, "\n".join(stdout_lines), "\n".join(stderr_lines)

def run_command_stream(cmd, cwd=None, env=None):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    vm_type = _detect_vm_type(cmd)
    proc_env = env if env is not None else _env_for(vm_type)

    logger.debug(f"Executing command: {' '.join(cmd)}")
    rc, out, err = _spawn(cmd, cwd=cwd, env=proc_env)

    if rc != 0 and (vm_type in (None, "virtualbox")):
        suspect = any(x in err for x in (
            "/usr/lib/vmware/lib/",
            "GLIBCXX_3.",
            "no version information available",
        ))
        if suspect:
            clean_env = os.environ.copy()
            clean_env.pop("LD_LIBRARY_PATH", None)
            logger.debug("Retrying with LD_LIBRARY_PATH stripped (VirtualBox self-heal)")
            rc, out, err = _spawn(cmd, cwd=cwd, env=clean_env)

    if rc != 0 and vm_type == "vmware":
        if ("error while loading shared libraries" in err and
            "cannot read file data: Error 21" in err and
            "/usr/lib/vmware/lib/" in err):
            clean_env = os.environ.copy()
            clean_env.pop("LD_LIBRARY_PATH", None)
            logger.debug("Retrying VMware run with LD_LIBRARY_PATH stripped")
            rc, out, err = _spawn(cmd, cwd=cwd, env=clean_env)

    return rc, out, err
