import logging

class ScreenFormatter(logging.Formatter):
    def __init__(self, fmt, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record):
        if "created" in record.msg:
            symbol = "[+]"
        elif record.levelno == logging.DEBUG:
            symbol = "[i]"
        elif record.levelno == logging.WARNING:
            symbol = "[!]"
        elif record.levelno == logging.ERROR:
            symbol = "[x]"
        else:
            symbol = "[-]"
        original_msg = super().format(record)
        return f"{symbol} {original_msg}"

class FileFormatter(logging.Formatter):
    def __init__(self, fmt, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record):
        if "created" in record.msg:
            symbol = "[+]"
        elif record.levelno == logging.DEBUG:
            symbol = "[i]"
        elif record.levelno == logging.WARNING:
            symbol = "[!]"
        elif record.levelno == logging.ERROR:
            symbol = "[x]"
        else:
            symbol = "[-]"
        original_msg = super().format(record)
        timestamp, message = original_msg.split(" ", 1)
        return f"{timestamp} -- {symbol} {message}"

def setup_logging(debug: bool, log: bool, log_file: str = None):
    level = logging.DEBUG if debug else logging.INFO
    console_handler = logging.StreamHandler()
    handlers = [console_handler]
    if log:
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)
    console_format = "%(message)s"
    file_format = "%(asctime)s.%(msecs)03d %(message)s"
    console_formatter = ScreenFormatter(console_format)
    console_handler.setFormatter(console_formatter)
    if log:
        file_formatter = FileFormatter(file_format, datefmt="%H:%M:%S")
        file_handler.setFormatter(file_formatter)
    logging.basicConfig(level=level, handlers=handlers)
