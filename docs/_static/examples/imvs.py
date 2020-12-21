import os, subprocess, shutil
from dna import DNA
from dna.utils import Logger, sh
from flask import Flask, jsonify, request, abort
from multiprocessing import Process

CWD = os.getcwd()

DEPLOY = f"{CWD}/deploy/"
STACKS = f"{CWD}/stacks/"
BUILD_LOGS = f"{CWD}/build_logs/"
SECRETS = "/somewhere/only/we/know/"

CERTBOT_ARGS = [
    "--preferred-challenges",
    "dns",
    "--dns-digitalocean",
    "--dns-digitalocean-credentials",
    f"{SECRETS}digitalocean.ini",
]

for path in [DEPLOY, STACKS, LOGS]:
    if not os.path.exists(path):
        os.makedirs(path)


app = Flask(__name__)
dna = DNA("imvs", cb_args=CERTBOT_ARGS)


def logger_fallback(service, log):
    if log == "build":
        contents = open(f"{BUILD_LOGS + service.name}.log").read()
        return "<br />".join(contents.split("\n"))
    abort(404)


def authenticate_user():
    """This is not the actual implementation of this function,
    but for safety reasons the actual implementation is not
    shared.
    """
    return True


dna.attach_logs_to_flask(
    app, "/logs/", fallback=logger_fallback, precheck=authenticate_user
)


@app.route("/")
def list_services():
    if not authenticate_user():
        abort(403)

    return jsonify(
        {
            service.name: {
                "image": service.image,
                "domains": [d.url for d in service.domains],
            }
            for service in dna.services
        }
    )


@app.route("/receive/<stack>", methods=["POST"])
def receive(stack):
    token = request.headers.get("X-Gitlab-Token")
    body = request.json

    if not validate_token(token, body):
        abort(403)

    project = Project(body["project"]["path_with_namespace"].split("/")[-1])

    logger = Logger(f"{BUILD_LOGS + project.name}.log")
    logger.open()

    if not os.path.exists(project.path):
        logger.pipe(
            sh(
                "git",
                "clone",
                body["project"]["git_ssh_url"],
                project.path,
            )
        )
    logger.pipe(sh("git", "fetch", cwd=project.path))
    logger.pipe(sh("git", "checkout", body["after"], cwd=project.path))

    process = Process(
        target=HANDLERS.get(stack, run_dockerfile_deploy),
        kwargs={
            "project": project,
            "stack": stack,
            "logger": logger,
        },
    )

    process.start()
    return f"Started deploy for {project.name}. See build status at /logs/{project.name}/build."


def run_dockerfile_deploy(project, stack, logger):
    logger.write(f"Running dockerfile deploy for {project.name} of type {stack}.")

    internal = "3000" if stack == "next" else "80"

    for fn in os.listdir(STACKS + stack):
        shutil.copy(f"{STACKS + stack}/{fn}", project.path)

    logger.pipe(
        dna.build_image(
            path=project.path,
            tag=project.img,
            stream=True,
        )
    )

    dna.set_print(logger.write)
    dna.run_deploy(project.name, project.img, internal)
    dna.add_domain(project.name, project.url)
    dna.reset_print()

    logger.close()


def run_pypi_deploy(project, stack, logger):
    logger.write(f"Running pypi deploy for {project.name}.")

    shutil.copy(f"{SECRETS}.pypirc", project.path)
    logger.pipe(sh("make", "pypi", cwd=project.path))
    os.remove(f"{project.path}/.pypirc")

    project.path = project.path + "docs/_build/dirhtml/"
    run_dockerfile_deploy(project, "cdn", logger)


def validate_token(token, body):
    """This is not the actual implementation of this function,
    but for safety reasons the actual implementation is not
    shared.
    """
    return False


HANDLERS = {
    "pypi": run_pypi_deploy,
}

DOMAINS = {
    "link": "imvs.me",
    "me": "vanshaj.dev",
}


class Project:
    def __init__(self, name):
        self.name = name
        self.path = DEPLOY + name + "/"
        self.img = f"imvs/{name}"
        self.url = DOMAINS.get(name, f"{name}.vanshaj.dev")
