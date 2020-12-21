import os
from dna import DNA
from flask import Flask

from common.rpc.hosted import (
    add_domain,
    delete,
    list_apps,
    new,
    run,
    stop,
    service_log,
    container_log,
)
from common.rpc.secrets import only

app = Flask(__name__)
dna = DNA("hosted")

if not os.path.exists("data"):
    os.makedirs("data")


@list_apps.bind(app)
@only("buildserver")
def list_apps():
    return {
        service.name: {
            "image": service.image,
            "domains": [d.url for d in service.domains],
        }
        for service in dna.services
    }


@new.bind(app)
@only("buildserver")
def new(img, name=None, env={}):
    name = name if name else img.split("/")[-1]

    img_name = f"{name}-img"
    dna.pull_image(img, img_name)

    if "ENV" not in env:
        env["ENV"] = "prod"
    if "PORT" not in env:
        env["PORT"] = 8001

    volumes = {
        f"{os.getcwd()}/data/saves/{name}": {
            "bind": "/save",
            "mode": "rw",
        },
    }

    dna.run_deploy(
        name,
        img_name,
        "8001",
        environment=env,
        volumes=volumes,
    )
    dna.add_domain(
        name,
        f"{name}.hosted.cs61a.org",
    )


@delete.bind(app)
@only("buildserver")
def delete(name):
    dna.delete_service(name)


@add_domain.bind(app)
@only(["buildserver", "sandbox"])
def add_domain(name, domain, force=False):
    dna.add_domain(name, domain)


@service_log.bind(app)
@only("logs")
def service_log():
    logs = sh("journalctl", "-u", "dockerapi", "-n", "100", quiet=True).decode("utf-8")
    return dict(success=True, logs=logs)


@container_log.bind(app)
@only("logs")
def container_log(name):
    return dict(success=True, logs=dna.docker_logs(name))


if __name__ == "__main__":
    app.run(host="0.0.0.0")
