class Block:
    """Represents a block in an nginx configuration

    :param name: the name of this block
    :type name: str
    :param sections: sub-blocks of this block
    :type sections: list[:class:`~dna.utils.Block`]
    :param options: variables to include in this block
    :type options: kwargs

    .. important::
        If you'd like to include a ``return`` statement
        in your block, pass its value into the constructor
        as ``ret``.
    """

    def __init__(self, name, *sections, **options):
        self.name = name
        self.sections = sections
        self.options = options

        if "ret" in self.options:
            self.options["return"] = self.options["ret"]
            del self.options["ret"]

    def _repr_indent(self, indent=""):
        """Represent this nginx block

        :param indent: the indentation block to preceed every\
            line in this representation with; add 4 indents to\
            sub-blocks
        :type indent: str
        """
        result = indent + self.name + " {\n"
        for block in self.sections:
            result += block._repr_indent(indent="    " + indent)
        for option in self.options:
            result += indent + "    " + option + " " + self.options[option] + ";\n"
        return result + indent + "}\n"

    def __repr__(self):
        return self._repr_indent(indent="")


class Server(Block):
    """A :class:`~dna.utils.Block` called ``server``"""

    def __init__(self, *sections, **options):
        super().__init__("server", *sections, **options)


class Location(Block):
    """A :class:`~dna.utils.Block` called ``location``

    :param location: the location being proxied
    :type location: str
    """

    def __init__(self, location, *sections, **options):
        super().__init__(f"location {location}", *sections, **options)


class Nginx:
    """Various utilities to interface with nginx

    :param default: the url of the default server to proxy to
    :type default: str
    """

    def __init__(self, default):
        self.default = default

    def gen_config_with_port(self, domain, port, logs_pre="/var/log/nginx/"):
        """Generate an nginx config that proxies ``domain`` to ``port``

        :param domain: the domain to proxy
        :type domain: str
        :param port: the port to proxy to
        :type port: str
        :param logs_pre: the location of logs for this proxy pass (defaults to\
            "/var/logs/nginx/")
        :type logs_pre: str

        :return: the generated nginx config, as a string
        """
        return self.gen_config(domain, f"http://127.0.0.1:{port}", logs_pre)

    def gen_config_with_sock(self, domain, sock, logs_pre="/var/log/nginx/"):
        """Generate an nginx config that proxies ``domain`` to ``sock``

        :param domain: the domain to proxy
        :type domain: str
        :param sock: the location of the unix socket file to proxy to
        :type sock: str
        :param logs_pre: the location of logs for this proxy pass (defaults to\
            "/var/logs/nginx/")
        :type logs_pre: str

        :return: the generated nginx config, as a string
        """
        return self.gen_config(domain, f"http://unix:{sock}", logs_pre)

    def gen_config(self, domain, proxy_pass, logs_pre):
        """Generate an nginx config that proxies ``domain`` to ``proxy_pass``

        If ``domain`` is a top-level domain, we include `www.domain``. If
        domain is the instance's ``default`` domain, we include ``default_server``.

        :param domain: the domain to proxy
        :type domain: str
        :param proxy_pass: the destination to pass to
        :type proxy_pass: str
        :param logs_pre: the location of logs for this proxy pass
        :type logs_pre: str

        :return: the generated nginx config, as a string
        """
        is_tld = len(domain.split(".")) == 2

        server_name = f"{domain}"
        if is_tld:
            server_name += f" www.{domain}"
        if domain == self.default:
            server_name += " default_server"

        http = Server(
            Location(
                "/",
                include="proxy_params",
                proxy_pass=proxy_pass,
            ),
            server_name=server_name,
            listen="80",
            access_log=f"{logs_pre}access.log",
            error_log=f"{logs_pre}error.log",
        )

        return str(http)
