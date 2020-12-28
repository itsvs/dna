from certbot._internal import cli, configuration, storage
from certbot._internal.plugins import disco as plugins_disco


class Certbot:
    """Various utilities to interface with certbot

    :param args: parameters to use with every call to ``certbot``,\
        such as custom DNS plugin configurations and installers
    :type args: list[str]

    When used with :class:`~dna.DNA`, the arguments will always be
    supplemented by ``-i nginx`` to force the nginx webserver.
    """

    def __init__(self, args=[]):
        from dna.utils import sh

        self.sh = sh
        self.plugins = plugins_disco.PluginsRegistry.find_all()
        self.args = args

    def _config(self, args=[]):
        """Generate a ``certbot`` configuration with the given arguments

        :param args: the arguments to use
        :type args: list[str]

        :return: a :class:`~certbot.interfaces.IConfig` object
        """
        args = args + self.args
        args = cli.prepare_and_parse_args(self.plugins, args)
        return configuration.NamespaceConfig(args)

    def _cert_iter(self):
        """An iterator over all renewable certificates on this machine"""
        for file in storage.renewal_conf_files(self._config()):
            yield storage.RenewableCert(file, self._config())

    def get_certs(self):
        """Get all renewable certificates on this machine.

        :return: a list of all the :class:`~certbot.interfaces.RenewableCert`\
            on this machine
        """
        return list(self._cert_iter())

    def cert_else_false(self, domain, force_wildcard=False):
        """Get a certificate matching ``domain`` if there is one, else ``False``

        By default, this will return an exact match if it exists. If one does not exist, then it will search for a wildcard one level above. If that doesn't exist either, returns ``False``.

        :param domain: the domain to match
        :type domain: str
        :param force_wildcard: forcibly search for a wildcard certificate only\
            (defaults to ``False``)
        :type force_wildcard: bool

        :return: the matching :class:`~certbot.interfaces.RenewableCert` if there\
            is one, otherwise ``False``
        """
        domains = [domain, ".".join(["*"] + domain.split(".")[1:])]
        found_wildcard = False
        if force_wildcard:
            domains = domains[1:]
        for cert in self._cert_iter():
            if domains[0] in cert.names():
                return cert
            if domains[-1] in cert.names():
                found_wildcard = cert
        return found_wildcard

    def attach_cert(self, cert, domain, logger=print):
        """Install ``cert`` on ``domain``

        :param cert: the certificate to install
        :type cert: :class:`~certbot.interfaces.RenewableCert`
        :param domain: the domain to install the certificate on
        :type domain: str
        :param logger: the function to stream output to
        :type logger: func
        """
        self.run_bot(
            [domain],
            ["install", "--cert-name", cert.live_dir.split("/")[-1]],
            logger=logger,
        )

    def run_bot(self, domains=[], args=[], logger=print):
        """Run a bot command on ``domains`` using ``args`` and the instance-wide ``args``

        :param domains: the domain names to pass to ``certbot``
        :type domains: list[str]
        :param args: any extra arguments to pass to ``certbot``, such as a command
        :type args: list[str]
        :param logger: the function to stream output to
        :type logger: func
        """
        args = list(args)
        for domain in domains:
            args.extend(["-d", domain])
        args.extend(self.args)
        out = self.sh("certbot", *args, stream=False)
        logger(out)
