
import sys

from kroltin.core import Kroltin


def cli():
    instance = Kroltin()
    try:
        instance.cli()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


def web():
    instance = Kroltin()
    try:
        instance.web()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli()