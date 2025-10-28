import logging
import re


# ANSI Colors
RED = "\033[91m"
CYAN = "\033[96m"
GREY = "\033[37m"
GREEN = "\033[92m"
RESET = "\033[0m"

class ScreenFormatter(logging.Formatter):
    def __init__(self, fmt, datefmt=None):
        super().__init__(fmt, datefmt)
        self.positive_msgs = ["exported", "removed", "successful"]

    def format(self, record):
        if "os_password" in record.msg:
            record.msg = self._redact_password(record.msg)

        if any(msg in record.msg for msg in self.positive_msgs):
            symbol = f"  {GREEN}[+]{RESET}"
        elif record.levelno == logging.DEBUG:
            symbol = f"  {CYAN}[i]{RESET}"
        elif record.levelno == logging.WARNING:
            symbol = f"  {RED}[!]{RESET}"
        elif record.levelno == logging.ERROR:
            symbol = f"  {RED}[x]{RESET}"
        else:
            symbol = "  [-]"
        original_msg = super().format(record)
        return f"{symbol} {original_msg}"
    
    @staticmethod
    def _redact_password(msg: str) -> str:
        """Redact OS passwords from log messages."""
        pattern = r"(-var\s+os_password=)(\S+)"
        return re.sub(pattern, r"\1********", msg)

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
