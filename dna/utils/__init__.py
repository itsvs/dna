from dna.utils.certbot_utils import Certbot, LockError
from dna.utils.db_utils import SQLite, Service, Domain
from dna.utils.docker_utils import Docker
from dna.utils.nginx_utils import Nginx, Block
from dna.utils.log_utils import Logger
import dna.utils.flask_utils as flask

import subprocess

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
