import docker
from docker.types import Mount


class Docker:
    """Various utilities to interface with Docker"""

    def __init__(self):
        self.client = docker.from_env()
        self.api = docker.APIClient(base_url="unix://var/run/docker.sock")

    def network_exists(self, name):
        """Return whether the internal network called ``name`` exists

        :param name: the network name to search for
        :type name: str

        :return: a boolean representing whether the network exists
        """
        return name in [net.name for net in self.client.networks.list()]

    def create_network(self, name):
        """Return an internal network called ``name``, creating it if
        it doesn't already exist

        :param name: the name of the network to create
        :type name: str

        :return: the created :class:`~docker.models.networks.Network`
        """
        if self.network_exists(name):
            return self.get_network(name)
        return self.client.networks.create(name)

    def get_network(self, name, low_level=False):
        """Return the requested network, or its details

        :param name: the name of the network to return
        :type name: str
        :param low_level: flag to return a details dictionary\
            instead of a :class:`~docker.models.networks.Network`\
            object
        
        :return: the requested :class:`~docker.models.networks.Network`,\
            or a dictionary representing it
        """
        for net in self.client.networks.list():
            if net.name == name:
                if low_level:
                    return self.api.inspect_network(net.id)
                return net

    def make_mount(self, host, internal):
        """Create a mount object representing a binding between ``host``
        and ``internal``

        :param host: the path on the host machine to bind
        :type host: str
        :param internal: the path inside the container to bind to
        :type internal: str

        :return: a relevant :class:`~docker.types.Mount` object
        """
        return Mount(internal, host, type="bind")

    def image_exists(self, name):
        """Return whether the image tagged ``name`` exists

        :param name: the image tag to search for
        :type name: str

        .. note::
            If ``name`` does not contain a tag, the ``:latest``
            tag is automatically used.

        :return: a boolean representing whether the image exists
        """
        if not ":" in name:
            name = name + ":latest"

        for img in self.client.images.list():
            if name in img.tags:
                return True
        return False

    def pull_image(self, image, tag=None):
        """Pull and save a Docker image by name or URL

        :param image: the name or url of the image to pull
        :type image: str
        :param tag: the initial tag to assign to the image (defaults to ``None``,\
            which assigns that tag ``latest``)
        :type tag: str
        """
        self.client.images.pull(image, tag=tag)

    def pull_image_stream(self, image, tag=None):
        """Pull and save a Docker image by name or URL and stream the output

        :param image: the name or url of the image to pull
        :type image: str
        :param tag: the initial tag to assign to the image (defaults to ``None``,\
            which assigns that tag ``latest``)
        :type tag: str

        :yields: dictionaries representing each streamed output line
        """
        yield from self.api.pull(image, tag, stream=True, decode=True)

    def build_image(self, **options):
        """Build a Docker image using the given options

        :param options: options to use to the build the image (ideally contains\
            at least a path to a build context, as well as a Dockerfile)
        :type options: kwargs
        """
        self.client.images.build(**options)

    def build_image_stream(self, **options):
        """Build a Docker image using the given options and stream the output

        :param options: options to use to the build the image (ideally contains\
            at least a path to a build context, as well as a Dockerfile)
        :type options: kwargs

        :yields: dictionaries representing each streamed output line
        """
        yield from self.api.build(decode=True, **options)

    def prune_images(self):
        """Remove all images older than 10 days"""
        self.client.images.prune({"until": "240h"})

    def container_exists(self, name):
        """Return whether the container called ``name`` exists

        :param name: the container name to search for
        :type name: str

        :return: a boolean representing whether the container exists
        """
        return name in [con.name for con in self.client.containers.list(all=True)]

    def run_image(self, img, name, **options):
        """Run the requested image as a container

        :param img: the name of the image to run
        :type img: str
        :param name: the name to assign to the target container
        :type name: str
        :param options: additional options to pass into Docker
        :type options: kwargs

        :return: the created :class:`~docker.models.containers.Container`
        """
        return self.client.containers.run(img, name=name, **options)

    def wipe_container(self, name):
        """Kill and remove the container named ``name``, if needed,
        and return it if it existed

        :param name: the name of the container to act on
        :type name: str

        :return: the removed :class:`~docker.models.containers.Container`\
            if it existed, else the string "not found"
        """
        for con in self.client.containers.list(all=True):
            if name == con.name:
                if con.status == "running":
                    con.kill()
                con.remove()
                return name
        return "not found"

    def exec_command(self, con, command, **options):
        """Run a command on the given container

        :param con: the (name of the) container to run the command on
        :type con: str or :class:`~docker.models.containers.Container`
        :param command: the command to run
        :type command: str
        :param options: additional options to pass into Docker
        :type options: kwargs

        :return: ``namedtuple('ExecResult', 'exit_code,output')``
        """
        if isinstance(con, str):
            con = self.client.containers.get(con)
        return con.exec_run(command, **options)

    def service_logs(self, con):
        """Get the most recent 100 logs for ``con``

        :param con: the name of the container
        :type con: str

        :return: a string of log messages
        """
        if isinstance(con, str):
            con = self.client.containers.get(con)
        return con.logs(tail=100, timestamps=True).decode("utf-8")
