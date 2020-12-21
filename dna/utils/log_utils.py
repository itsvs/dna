from datetime import datetime as dt
import os, subprocess


def sh(*args, **kwargs):
    """A wrapper around ``subprocess.Popen`` that returns a generator
    streaming output from the command specified by ``args``

    :param args: the command to run, split on whitespaces
    :param kwargs: other options to pass into ``Popen``, such as a ``cwd``

    :return: a generator to stream lines from the subprocess output
    """
    out = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
        **kwargs,
    )

    def generator():
        while True:
            line = out.stdout.readline()
            yield line
            returncode = out.poll()
            if returncode is not None:
                return f"Process completed with code {returncode}."

    return generator()


class Logger:
    """Various utilities to interface with logs

    :param path: the path to the logfile
    :type path: str
    """

    def __init__(self, path):
        self.path = path

    def open(self):
        """Open the logfile for writing"""
        self.f = open(self.path, "w")

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
