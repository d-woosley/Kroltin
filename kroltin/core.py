from kroltin.cli_args import load_args

class Kroltin:
    def __init__(self):
        pass

    def cli(self):
        args = load_args()
        print("Running Kroltin CLI")

    def web(self):
        print("Running Kroltin Web")