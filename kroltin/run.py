
import signal
import sys

from kroltin.core import Kroltin

# Global cleanup registry
cleanup_callbacks = []

def register_cleanup(callback):
    cleanup_callbacks.append(callback)

def cleanup_all():
    for cb in cleanup_callbacks:
        try:
            cb()
        except Exception as e:
            print(f"Cleanup error: {e}", file=sys.stderr)

def signal_handler(sig, frame):
    print(f"\nReceived signal {sig}, cleaning up...")
    cleanup_all()
    sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def cli():
    instance = Kroltin()
    try:
        instance.cli()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        cleanup_all()
        sys.exit(1)


def web():
    instance = Kroltin()
    try:
        instance.web()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        cleanup_all()
        sys.exit(1)


if __name__ == "__main__":
    cli()