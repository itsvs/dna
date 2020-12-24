import time, os
from io import BytesIO
from threading import Thread
from dna.utils import sh


class SocatHelper:
    """The ``socat`` helper class that binds container ports to unix sockets

    The motivation behind using ``socat`` is that simply having docker publish
    ports and having nginx proxy to them would result in host ports having to be
    defined and occupied. The better solution is to have an additional lightweight
    container that can bridge to each service and bind its port to a socket. This
    socket is created in a folder that is located on the host but mounted to the
    ``socat`` container, so that the host's nginx webserver may proxy to it.

    :param dna: the DNA instance
    :type dna: :class:`~dna.DNA`

    The ``socat`` container for a DNA instance ``inst`` is called ``inst-socat``.
    The bridge network for a DNA instance ``inst`` is called ``inst``.
    """

    #: The command to bind ``port`` in the ``service`` container to a socket named ``service.sock``
    SOCAT_CMD = "socat unix-listen:/socks/{service}.sock,fork,reuseaddr tcp-connect:{service}:{port}"

    #: The Dockerfile for ``socat```
    DOCKERFILE = """FROM alpine:edge\nARG VERSION=1.7.3.4-r1\nRUN apk --no-cache add socat=${VERSION}\n"""

    def __init__(self, dna):
        self.dna = dna
        self.service = dna.service_name
        self.bridge = self.service
        self.container = f"{self.service}-socat"
        self.docker = dna.docker
        self.path = dna.path
        self.socks = dna.path + "/socks"

        self._setup()

    def _fix_permissions(self, service, port):
        """Wait for the socket binding to complete, then make the
        socket visible to nginx

        :param service: the name of the service
        :type service: str
        :param port: the port to be bound
        :type port: str
        """
        path = f"{self.socks}/{service}.sock"
        while not os.path.exists(path):
            time.sleep(1)

        out = sh("chmod", "666", path, stream=False)
        self.dna.print(out.stdout)

        self.dna.print(f"Bound {service}:{port} to {service}.sock.")

    def bind(self, service, port):
        """Bind ``port`` inside the ``service`` container to a socket called ``service.sock``

        :param service: the name of the service
        :type service: str
        :param port: the port to be bound
        :type port: str
        """
        self.docker.exec_command(
            self.container,
            f"/bin/sh -c '{SocatHelper.SOCAT_CMD.format(service=service, port = port)}'",
            detach=True,
        )

        Thread(
            target=self._fix_permissions,
            kwargs={
                "service": service,
                "port": port,
            },
        ).start()

    def unbind(self, service, port):
        """Unbind ``port`` inside the ``service`` container from ``service.sock``

        The ``port`` is required here to determine which ``socat`` process to terminate
        on the ``socat`` container for this DNA instance.

        :param service: the name of the service
        :type service: str
        :param port: the port to be unbound
        :type port: str
        """
        pid = self.docker.exec_command(
            self.container,
            f"/bin/sh -c 'pgrep -f \"{SocatHelper.SOCAT_CMD.format(service=service, port = port)}\"'",
        ).output.decode("utf-8")[:-1]
        self.docker.exec_command(self.container, f"/bin/sh -c 'kill {pid}'")

        self.dna.print(f"Unbound {service}:{port} from {service}.sock.")

    def bind_all(self, services):
        """Bind all the ``services`` to their respective ports

        :param services: the services to bind
        :type services: list[:class:`~dna.utils.Service`]
        """
        for service in services:
            self.bind(service.name, service.port)

    def _setup(self, force=False):
        """Set up the ``socat`` container for this DNA instance, if needed

        If the bridge network doesn't exist, create it. If the ``socat``
        image doesn't exist or we want to ``force`` it to rebuild, build it.
        If the image was rebuilt, kill and remove the ``socat`` container
        for this DNA instance. Lastly, if the ``socat`` container for this
        DNA instance doesn't exist, create and start it.

        :param force: flag to force the ``socat`` image to rebuild (defaults\
            to ``False``)
        :type force: bool
        """
        self.dna.print("Setting up socat, if needed...")

        docker = self.docker
        mounts = [docker.make_mount(self.socks, "/socks")]

        if not docker.network_exists(self.bridge):
            self.dna.print(f"Creating {self.bridge} bridge network...")
            docker.create_network(self.bridge)

        if force or not docker.image_exists("socat:latest"):
            self.dna.print("Building socat image...")

            f = BytesIO(SocatHelper.DOCKERFILE.encode("utf-8"))

            for line in docker.build_image_stream(
                path=self.path, fileobj=f, tag="socat:latest"
            ):
                self.dna.print(line.get("stream", ""))
            docker.wipe_container(self.container)

        if not docker.container_exists(self.container):
            self.dna.print(f"Starting socat container at {self.container}...")
            con = docker.run_image(
                "socat",
                self.container,
                tty=True,
                detach=True,
                network=self.bridge,
                mounts=mounts,
            )

        self.dna.print("Done! Socat setup complete.")
