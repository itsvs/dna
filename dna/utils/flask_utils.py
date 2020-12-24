
def create_api_client(dna, app, base="/api/", precheck=lambda: False):
    """Expose DNA functions at the given endpoint on the given Flask app

    Since these functions control deployment, the ``precheck`` is restrictive
    by default. Please make sure to pass in a function that properly validates
    authenticated users and allows them to use the API endpoints.

    :param app: the Flask app to expose functions to
    :type app: :class:`~flask.Flask`
    :param base: the base endpoint for the API (defaults to "/api/")
    :type base: str
    :param precheck: an optional precursor function that must return ``True``\
        for execution to continue (good for things like authentication)
    :type precheck: func
    """
    from flask import request, Response, stream_with_context, jsonify, abort

    @app.route(base + "pull_image", methods=["POST"])
    def pull_image():
        if not precheck():
            abort(403)
        data = request.get_json()
        
        image = data.get("image")
        tag = data.get("tag", None)

        return Response(stream_with_context(dna.pull_image(image, tag, True)))
    
    @app.route(base + "build_image", methods=["POST"])
    def build_image():
        if not precheck():
            abort(403)
        data = request.get_json()
        options = data.get("options")

        return Response(stream_with_context(dna.pull_image(True, **options)))
    
    @app.route(base + "run_deploy", methods=["POST"])
    def run_deploy():
        if not precheck():
            abort(403)
        data = request.get_json()

        service = data.get("service")
        image = data.get("image")
        port = data.get("port")
        options = data.get("options")

        dna.run_deploy(service, image, port, **options)
        return jsonify({"success": True})
    
    @app.route(base + "propagate_services", methods=["POST"])
    def propagate_services():
        if not precheck():
            abort(403)
        dna.propagate_services()
        return jsonify({"success": True})
    
    @app.route(base + "get_service_info/<name>")
    def get_service_info(name):
        if not precheck():
            abort(403)
        return jsonify(dna.get_service_info(name).to_json())
    
    @app.route(base + "add_domain", methods=["POST"])
    def add_domain():
        if not precheck():
            abort(403)
        data = request.get_json()

        service = data.get("service")
        domain = data.get("domain")
        force_wildcard = data.get("force_wildcard", False)

        dna.add_domain(service, domain, force_wildcard)
        return jsonify({"success": True})

    @app.route(base + "delete_service", methods=["DELETE"])
    def delete_service():
        if not precheck():
            abort(403)
        data = request.get_json()
        service = data.get("service")

        dna.delete_service(service)
        return jsonify({"success": True})

def create_logs_client(dna, app, base="/logs/", fallback=None, precheck=lambda: True):
    """Display logs at the given endpoint on the given Flask app

    Since logs are typically not sensitive, the ``precheck`` is permissive by
    default. Please make sure to change this functionality if you don't want
    it to be publicly accessible.

    :param app: the Flask app to forward logs to
    :type app: :class:`~flask.Flask`
    :param base: the base endpoint for logs (defaults to "/logs/")
    :type base: str
    :param fallback: an optional fallback function if DNA can't handle logs\
        such as if you want to display a type of logs that DNA isn't familiar\
        with (ex. image build logs)
    :type fallback: func
    :param precheck: an optional precursor function that must return ``True``\
        for execution to continue (good for things like authentication)
    :type precheck: func
    """
    from flask import abort, url_for

    if not base.startswith("/"):
        base = "/" + base
    if not base.endswith("/"):
        base = base + "/"

    def _spcss(content=""):
        return '<link rel="stylesheet" href="https://unpkg.com/spcss">\n' + content
    
    def _link(service, log, title):
        return f"""<a href={
                url_for("attach_servlog", service=service.name, log=log)
            }>{title}</a>"""

    @app.route(base)
    def logs_index():
        if not precheck():
            abort(403)

        content = _spcss("<h1>DNA Service Logs</h1>")
        content += "<p>See nginx and docker logs for all your running services! "
        content += "Note that custom log types are currently not listed.</p>"
        content += f'<a href={url_for("attach_dna")}>View Internal DNA Logs</a>'

        for service in dna.services:
            content += "<h3>" + service.name + "</h3>\n<ul>\n"
            content += f'<li>{_link(service, "nginx", "Nginx Access")}</li>\n'
            content += f'<li>{_link(service, "error", "Nginx Errors")}</li>\n'
            content += f'<li>{_link(service, "docker", "Container")}</li>\n'
            content += "</ul>\n"

        return content
    
    @app.route(base + "dna")
    def attach_dna():
        if not precheck():
            abort(403)
        return "<br />".join(dna.dna_logs().split("\n"))

    @app.route(base + "<service>/<log>")
    def attach_servlog(service, log):
        if not precheck():
            abort(403)

        service, service_name = dna.get_service_info(service), service
        if not service and fallback:
            return fallback(service_name, log)
        if not service:
            abort(404)

        if log == "nginx":
            return "<br />".join(dna.nginx_logs(service.name).split("\n"))
        if log == "error":
            return "<br />".join(
                dna.nginx_logs(service.name, error=True).split("\n")
            )
        if log == "docker":
            return "<br />".join(dna.docker_logs(service.name).split("\n"))

        if fallback:
            return fallback(service.name, log)
        abort(404)
