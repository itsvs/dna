from datetime import datetime as dt
import os, logging

for level in range(10, 51, 10):
    logging.addLevelName(
        level,
        logging.getLevelName(level).lower(),
    )

fmt = logging.Formatter(
    '[%(asctime)s.%(msecs)03d] [%(name)s - %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        handler = logger.handlers[0]
    else:
        handler = logging.FileHandler(f'{name}.log')
        handler.setLevel(logging.INFO)
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    return logger

class Logger:
    """Various utilities to interface with logs

    :param path: the path to the logfile
    :type path: str
    :param append: whether to append to the logfile\
        (defaults to ``False`` and overwrites logfile)
    :type append: bool
    """

    def __init__(self, path, append=False):
        self.path = path
        self.append = append

    def open(self):
        """Open the logfile for writing"""
        self.f = open(self.path, "a" if self.append else "w")

    def write(self, line):
        """Write to the logfile

        :param line: the line to write
        :type line: str
        """
        if not line:
            return

        if not isinstance(line, str):
            line = line.decode("utf-8")
        if not line.endswith("\n"):
            line = line + "\n"

        self.f.write(f"[{dt.now()}] {line}")
        self.f.flush()
        os.fsync(self.f.fileno())

    def pipe(self, gen):
        """Pipe all output from ``gen`` to the logfile

        :param gen: the generator to pipe from
        :type gen: generator
        """
        for line in gen:
            self.write(line)

    def close(self):
        """Close the logfile"""
        self.f.close()

    def file(self):
        """Return the logfile object"""
        return self.f
