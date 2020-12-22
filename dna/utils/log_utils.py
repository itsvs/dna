from datetime import datetime as dt
import os, subprocess


def sh(*args, stream=True, **kwargs):
    """A wrapper around ``subprocess.Popen`` that returns a generator
    streaming output from the command specified by ``args``

    :param args: the command to run, split on whitespaces
    :param stream: whether to stream the output as a generator (defaults to\
        ``True``)
    :type stream: bool
    :param kwargs: other options to pass into ``Popen``, such as a ``cwd``

    :return: a generator to stream lines from the subprocess output if stream\
        is ``True``, else the subprocess output as a completed string
    """
    if not stream:
        return subprocess.run(args, capture_output=True).stdout.decode("utf-8")

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
