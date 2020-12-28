from sqlalchemy import Column, String, Integer, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, backref
import time

Base = declarative_base()


class Domain(Base):
    """Represents a domain, storing the :class:`~dna.utils.Service`
    it's bound to (if any)

    :param url: the domain itself
    :type url: str
    :param service: the service connected to this domain
    :type service: :class:`~dna.utils.Service`
    :ivar service_name: the name of the service the domain is bound to

    .. warning::
        Do `not` set ``service_name`` manually! It is a foreign key that
        depends on the ``service``, which is the parameter you should set.
    """

    __tablename__ = "domain"
    url = Column(String, primary_key=True)
    service_name = Column(String, ForeignKey("service.name"))

    def __repr__(self):
        return f"Domain({self.url}" + (
            f", {self.service_name})" if self.service_name else ")"
        )


class Service(Base):
    """Represents a service, as well any domains bound to it

    :param name: the name of the service
    :type name: str
    :param image: the name of the docker image containing this image
    :type image: str
    :param port: the container port running the front-end of this service
    :type port: str
    :param domains: a list of all the domains bound to this service
    :type domains: list[:class:`~dna.utils.Domain`]
    """

    __tablename__ = "service"
    name = Column(String, primary_key=True)
    image = Column(String)
    port = Column(String)
    domains = relationship("Domain", backref=backref("service"))

    def __repr__(self):
        res = f"Service({self.name}, {self.image}, {self.port}"
        for d in self.domains:
            res += f", {d.url}"
        return res + ")"
    
    def to_json(self):
        return {
            "name": self.name,
            "image": self.image,
            "port": self.port,
            "domains": [
                {
                    "url": d.url,
                } for d in self.domains
            ],
        }


class ApiKey(Base):
    __tablename__ = "apikey"
    id = Column(Integer, primary_key=True)
    key = Column(String)
    ip = Column(String)
    issued_at = Column(Integer)
    expires_in = Column(Integer)

    def is_expired(self):
        return self.issued_at + self.expires_in <= time.time() + 10


class SQLite:
    """Various utilities to interface with SQLite

    :param rel: the relative path to the location to store the database
    :type rel: str
    :param name: the name of the database file (minus the ``.db`` extension)
    :type name: str
    """

    def __init__(self, rel="/", name="app"):
        if not rel.endswith("/"):
            rel = rel + "/"
        engine = create_engine(f"sqlite://{rel}{name}.db?check_same_thread=False")
        Base.metadata.create_all(engine)
        self.s = Session(engine)

    def create_service(self, name, image, port):
        """Create a new service with the given parameters

        :param name: the name of the service
        :type name: str
        :param image: the docker image holding the service
        :type image: str
        :param port: the container port running the front-end of the
        :type port: str

        :return: the created :class:`~dna.utils.Service`
        """
        s = Service(name=name, image=image, port=port)
        self._add(s)
        return s

    def add_domain_to_service(self, domain, service):
        """Bind ``domain`` to ``service`` if it is not bound elsewhere

        :param domain: the (url of the) domain to bind
        :type domain: str or :class:`~dna.utils.Domain`
        :param service: the (name of the) service to bind to
        :type service: str or :class:`~dna.utils.Service`

        :return: a boolean representing whether ``domain`` was\
            successfully bound to ``service``
        """
        if isinstance(service, str):
            service = self.get_service_by_name(service)
        if isinstance(domain, str):
            domain = self.get_domain_by_url(domain, create=True)

        if domain.service:
            return domain.service == service

        service.domains.append(domain)
        self.s.commit()
        return True

    def delete_service(self, service):
        """Remove all records related to ``service``, including
        the associated :class:`~dna.utils.Service` object and any
        associated :class:`~dna.utils.Domain` objects

        :param service: the (name of the) service to delete
        :type service: str or :class:`~dna.utils.Service`
        """
        if isinstance(service, str):
            service = self.get_service_by_name(service)
        for domain in service.domains:
            self.s.delete(domain)
        self.s.delete(service)
        self.s.commit()

    def get_services(self):
        """Get all the services stored in this database

        :return: a list of :class:`~dna.utils.Service` objects
        """
        return self.s.query(Service).all()

    def get_service_by_name(self, name):
        """Get information on the service called ``name``

        :param name: the name to query on
        :type name: str

        :return: the requested :class:`~dna.utils.Service`, if it\
            exists (else ``None``)
        """
        return self.s.query(Service).filter(Service.name == name).one_or_none()

    def get_service_by_domain(self, domain):
        """Get information on the service that ``domain`` is bound to

        :param domain: the (url of the) domain to query on
        :type domain: str or :class:`~dna.utils.Domain`

        :return: the requested :class:`~dna.utils.Service`, if it\
            exists (else ``None``)
        """
        if isinstance(domain, str):
            return (
                self.s.query(Service)
                .filter(any(d.url == domain for d in Service.domains))
                .one_or_none()
            )
        return (
            self.s.query(Service)
            .filter(any(d == domain for d in Service.domains))
            .one_or_none()
        )

    def get_domains(self):
        """Get all the domains stored in this database

        :return: a list of :class:`~dna.utils.Domain` objects
        """
        return self.s.query(Domain).all()

    def get_domain_by_url(self, url, create=False):
        """Get information on the domain pointing to ``url``

        :param url: the url to query on
        :type url: str
        :param create: flag to create the domain if it doesn't exist\
            (defaults to ``False``)
        :type create: bool

        :return: the requested :class:`~dna.utils.Domain` if it\
            exists (else ``None``)
        """
        get = self.s.query(Domain).filter(Domain.url == url).one_or_none()
        if get or not create:
            return get
        domain = Domain(url=url)
        self._add(domain)
        return domain
    
    def get_active_keys(self):
        keys = self.s.query(ApiKey).all()
        keys = [k for k in keys if not k.is_expired()]
        return keys

    def get_key_info(self, key):
        get = self.s.query(ApiKey).filter(ApiKey.key == key).one_or_none()
        return get

    def new_api_key(self, key, ip):
        key_obj = ApiKey(key=key, ip=ip, issued_at=time.time(), expires_in=3600)
        self._add(key_obj)
        return key_obj
    
    def check_api_key(self, key, ip):
        get = self.s.query(ApiKey).filter(ApiKey.key == key).one_or_none()
        if not get:
            return False
        return get.ip == ip and not get.is_expired()
    
    def revoke_api_key(self, key):
        get = self.s.query(ApiKey).filter(ApiKey.key == key).one_or_none()
        if not get:
            return False
        get.expires_in = 0
        
        self.s.commit()
        return get.is_expired()

    def _add(self, obj):
        """Add and commit the specified object to the database

        :param obj: the object to add
        :type obj: :class:`~dna.utils.Service` or :class:`~dna.utils.Domain`
        """
        self.s.add(obj)
        self.s.commit()
