from kroltin.core import Kroltin


def cli():
    instance = Kroltin()
    instance.cli()


def web():
    instance = Kroltin()
    instance.web()


if __name__ == "__main__":
    cli()