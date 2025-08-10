from argparse import ArgumentParser, ArgumentTypeError

def load_args():
    parser = ArgumentParser(
        description="A Command and Control (C2) service for penetration testing",
        epilog="by: Duncan Woosley (github.com/d-woosley)",
    )

    # Add arguments
    parser.add_argument(
        '-d',
        "--debug",
        dest="debug",
        help="Set output to debug",
        action="store_true",
        default=False
        )

    # Get arg results
    args = parser.parse_args()

    return(args)