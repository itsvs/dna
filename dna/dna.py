import os, shutil, threading, subprocess
import dna.utils as utils
from dna.socat import SocatHelper
import time


class DNA:
    """This is the main DNA class, which does all the heavy lifting

    :param service_name: the name of this DNA instance (up to you)
    :type service_name: str
    :param default: the default domain this DNA instance runs on (used by ``nginx``)
    :type default: str
    :param cb_args: additional arguments to be used whenever ``certbot`` is called
    :type cb_args: list[str]
    """

    ###########################################################
    ##
    ## Configuring DNA
    ##
    ###########################################################

    def __init__(self, service_name, default=None, cb_args=[]):
        self._configure(service_name)

        self.nginx = utils.Nginx(default)
        self.docker = utils.Docker()
        self.certbot = utils.Certbot(cb_args + ["-i", "nginx"])

        self.internal_logger = utils.Logger(self.logs + "/dna.log")
        self.internal_logger.open()

        self.print = self.internal_logger.write
        self.print(f"Starting DNA...")
        self.socat = SocatHelper(self)

        self.propagate_services()
        self.socat.bind_all(self.services)

        self.print(f"Successfully started DNA instance in {self.path}.")

    def __del__(self):
        self.internal_logger.close()

    def _make_dir(self, path):
        """If the folder at ``path`` doesn't exist, create it

        :param path: the path to the folder
        :type path: str
        """
        if not os.path.exists(path):
            os.makedirs(path)

    def _configure(self, service_name):
        """Configures the DNA instance called ``service_name`` for use

        :param service_name: the name of the DNA instance
        :type service_name: str

        * Creates the ``.dna`` folder and relevant subfolders as needed
        * Modify nginx to include configs made under this DNA instance
        * Creates a :class:`~dna.utils.SQLite` database for this DNA instance
        """
        self.service_name = service_name
        self.path = os.getcwd() + "/.dna"
        self.socks = self.path + "/socks"
        self.confs = self.path + "/nginx"
        self.logs = self.path + "/logs"

        for path in [self.path, self.socks, self.confs, self.logs]:
            self._make_dir(path)
        with open(f"/etc/nginx/conf.d/{self.service_name}.conf", "w") as nconf:
            nconf.write(f"include {self.confs}/*.conf;")

        self.db = utils.SQLite(rel="/.dna/", name=service_name)

    def set_print(self, func):
        """Set the print function to ``func``

        :param func: a print-like function
        :type func: func
        """
        self.print = func

    def reset_print(self):
        """Reset the print function to the internal logger"""
        self.print = self.internal_logger.write

    ###########################################################
    ##
    ## Preparing for Service Deploys
    ##
    ###########################################################

    def pull_image(self, image, tag=None, stream=False):
        """Pull and save a Docker image by name or URL

        :param image: the name or url of the image to pull
        :type image: str
        :param tag: the initial tag to assign to the image (defaults to ``None``,\
            which assigns that tag ``latest``)
        :type tag: str
        :param stream: flag to yield pull output (defaults to ``False``)
        :type stream: bool
        """
        if stream:
            for line in self.docker.pull_image_stream(image, tag):
                yield line.get("stream", "")
        else:
            self.docker.pull_image(image, tag)

    def build_image(self, stream=False, **options):
        """Build a Docker image using the given options

        :param stream: flag to yield build output (defaults to ``False``)
        :type stream: bool
        :param options: options to use to the build the image (ideally contains\
            at least a path to a build context, as well as a Dockerfile)
        :type options: kwargs
        """
        if stream:
            for line in self.docker.build_image_stream(rm=True, **options):
                yield line.get("stream", "")
        else:
            self.docker.build_image(rm=True, **options)

    ###########################################################
    ##
    ## Deploying a Service
    ##
    ###########################################################

    def _do_docker_deploy(self, service, image, **options):
        """Deploys the image named ``image`` to a container named ``service``

        :param service: the name of the service being launched
        :type service: str
        :param image: the name of the image holding the service
        :type image: str
        :param options: other options to pass to docker on deploy
        :type options: kwargs
        """
        self.print("Finding and killing container, if it exists...")
        self.docker.wipe_container(service)

        self.print("Starting container...")
        con = self.docker.run_image(
            image, service, detach=True, network=self.socat.bridge, **options
        )

        self.print("Pruning images...")
        self.docker.prune_images()

        self.print(f"Done! Successfully deployed {image} as {service}.")

    def _do_nginx_deploy(self, service, domain):
        """Adds an nginx proxy from the ``domain`` to the ``service``

        :param service: the name of the service to point to
        :type service: str
        :param domain: the url to proxy
        :type domain: str
        """
        self.print("Doing nginx deploy...")
        if os.path.exists(f"{self.confs}/{domain}.conf"):
            self.print(f"An nginx config for {domain} already exists!")
            return

        socket = f"{self.socks}/{service}.sock"
        with open(f"{self.confs}/{domain}.conf", "w") as out:
            out.write(
                self.nginx.gen_config_with_sock(
                    domain, socket, logs_pre=f"{self.logs}/{service}-"
                )
            )
        out = utils.sh("nginx", "-s", "reload", stream=False)
        self.print(out)

        self.print("Installing or provisioning certificate, as needed...")
        for _ in range(12):
            try:
                cert = self.certbot.cert_else_false(domain)
                if cert:
                    self.print(f"Attaching an existing certificate that matches {domain}...")
                    self.certbot.attach_cert(cert, domain, logfile=self.internal_logger.file())
                else:
                    self.print("Provisioning a new certificate...")
                    self.certbot.run_bot([domain], logfile=self.internal_logger.file())
            except utils.LockError:
                time.sleep(5)
                continue
            
            self.print(f"Done! Sucessfully proxied https://{domain} to {service}.")
            return
        self.print(f"Failed to acquire Certbot lock 12 times. Could not secure {domain}.")
        self.print(f"Done! Sucessfully proxied http://{domain} to {service}.")
        

    def _do_db_deploy(self, service, image, port):
        """Saves the service to the :class:`~dna.utils.SQLite` database for this DNA instance

        :param service: the name of the service
        :type service: str
        :param image: the name of the Docker image containing this service
        :type image: str
        :param port: the port inside the container that the service front-end runs on
        :type port: str
        """
        self.print("Doing database deploy...")
        if not self.db.get_service_by_name(service):
            self.db.create_service(service, image, port)
            self.print("Done!")
        else:
            self.print("Service already exists in database!")

    def run_deploy(self, service, image, port, **docker_options):
        """Deploys a service to a container, binds that container port to socat, saves
        the service in the database, and re-propagates the services in this DNA instance.

        :param service: the name of the service
        :type service: str
        :param image: the name of the Docker image containing this service
        :type image: str
        :param port: the port inside the container that the service front-end runs on
        :type port: str
        :param docker_options: other options to pass to docker on deploy
        :type docker_options: kwargs
        """
        self._do_docker_deploy(service, image, **docker_options)
        self.socat.bind(service, port)
        self._do_db_deploy(service, image, port)

        self.propagate_services()

    ###########################################################
    ##
    ## Managing Services
    ##
    ###########################################################

    def propagate_services(self):
        """Populates ``self.services`` with the services managed by this DNA\
            instance
        
        For the names of all the docker containers connected to this\
            service's socat bridge, calls :meth:`~dna.DNA.get_service_info`
        """
        dna = self.docker.get_network(self.socat.bridge, low_level=True)
        self.services = []
        for con in dna["Containers"]:
            if dna["Containers"][con]["Name"] == self.socat.container:
                continue
            service = self.get_service_info(dna["Containers"][con]["Name"])
            if not service:
                continue
            self.services.append(service)

    def get_service_info(self, service):
        """Gets the requested service

        :param service: the name of the service to find
        :type service: str

        :return: a :class:`~dna.utils.Service` object\
            representing the requested service
        """
        return self.db.get_service_by_name(service)

    def add_domain(self, service, domain):
        """Proxy ``domain`` to ``service``, if it is not already bound to another service

        :param service: the name of the service
        :type service: str
        :param domain: the url to proxy to the service front-end
        :type domain: str
        """
        if self.db.add_domain_to_service(domain, service):
            self._do_nginx_deploy(service, domain)
        self.propagate_services()

    def delete_service(self, service):
        """Unproxy all domains attached to ``service``, unbind ``service`` from socat,
        stop and delete the ``service``'s Docker container, and remove it from the
        database.

        :param service: the name of the service
        :type service: str
        """
        service = self.db.get_service_by_name(service)

        if not service:
            return

        for domain in service.domains:
            os.remove(f"{self.confs}/{domain.url}.conf")
        out = subprocess.run(["nginx", "-s", "reload"], capture_output=True)
        self.print(out.stdout)

        self.socat.unbind(service.name, service.port)
        self.docker.wipe_container(service.name)

        self.db.delete_service(service)
        self.propagate_services()

    ###########################################################
    ##
    ## Accessing Logs
    ##
    ###########################################################

    def docker_logs(self, service):
        """Get the docker logs for ``service``

        :param service: the name of the service
        :type service: str

        :return: a string of log messages
        """
        return self.docker.service_logs(service)

    def nginx_logs(self, service, error=False):
        """Get the nginx logs for ``service``

        :param service: the name of the service
        :type service: str
        :param error: return the nginx error logs instead of access (defaults to ``False``)
        :type error: bool

        :return: a string of log messages
        """
        path = f'{self.logs}/{service}-{"error" if error else "access"}.log'
        with open(path) as f:
            return f.read()

    def dna_logs(self):
        """Get dna's own logs"""
        with open(self.logs + "/dna.log") as f:
            return f.read()

    def attach_logs_to_flask(self, app, endpoint, fallback=None, precheck=None):
        """Display logs at the given endpoint on the given Flask app

        :param app: the Flask app to forward logs to
        :type app: :class:`~flask.Flask`
        :param endpoint: the base endpoint for logs
        :type endpoint: str
        :param fallback: an optional fallback function if DNA can't handle logs\
            such as if you want to display a type of logs that DNA isn't familiar\
            with (ex. image build logs)
        :type fallback: func
        :param precheck: an optional precursor function that must return ``True``\
            for execution to continue (good for things like authentication)
        :type precheck: func
        """
        from flask import abort

        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        if not endpoint.endswith("/"):
            endpoint = endpoint + "/"

        @app.route(endpoint + "dna")
        def attach_dna():
            if precheck and not precheck():
                abort(403)
            return "<br />".join(self.dna_logs().split("\n"))

        @app.route(endpoint + "<service>/<log>")
        def attach_servlog(service, log):
            if precheck and not precheck():
                abort(403)

            service, service_name = self.get_service_info(service), service
            if not service and fallback:
                return fallback(service_name, log)
            if not service:
                abort(404)

            if log == "nginx":
                return "<br />".join(self.nginx_logs(service.name).split("\n"))
            if log == "error":
                return "<br />".join(
                    self.nginx_logs(service.name, error=True).split("\n")
                )
            if log == "docker":
                return "<br />".join(self.docker_logs(service.name).split("\n"))

            if fallback:
                return fallback(service.name, log)
            abort(404)
