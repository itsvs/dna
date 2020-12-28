import os

def create_api_client(dna, precheck=lambda: False):
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
    from flask import request, Response, stream_with_context, jsonify, abort, Blueprint

    api = Blueprint('dna_api', __name__)

    @api.route("/gen_key")
    def gen_key():
        if not precheck():
            abort(403)
        key = dna.db.new_api_key(
            os.urandom(24).hex(),
            request.environ.get("HTTP_X_FORWARDED_FOR", "0.0.0.0"),
        )

        return jsonify(
            success=True,
            api_key=key.key, 
            expires_at=(key.issued_at + key.expires_in), 
            authorized_ip=key.ip
        )
    
    @api.route("/revoke_key/<key>")
    def revoke_key(key):
        if not precheck():
            abort(403)
        return jsonify(success=dna.db.revoke_api_key(key))
    
    def _check_key():
        key = request.headers.get("App-Key-DNA", "")
        ip = request.environ.get("HTTP_X_FORWARDED_FOR", "0.0.0.0")
        if not dna.db.check_api_key(key, ip):
            abort(403)
        return True

    @api.route("/pull_image", methods=["POST"])
    def pull_image():
        if not precheck():
            _check_key()
        data = request.get_json()
        
        image = data.get("image")
        tag = data.get("tag", None)

        return Response(stream_with_context(dna.pull_image(image, tag, stream=True)))
    
    @api.route("/build_image", methods=["POST"])
    def build_image():
        if not precheck():
            _check_key()
        data = request.get_json()
        options = data.get("options")

        return Response(stream_with_context(dna.build_image(stream=True, **options)))
    
    @api.route("/run_deploy", methods=["POST"])
    def run_deploy():
        if not precheck():
            _check_key()
        data = request.get_json()

        service = data.get("service")
        image = data.get("image")
        port = data.get("port")
        options = data.get("options")

        dna.run_deploy(service, image, port, **options)
        return jsonify({"success": True})
    
    @api.route("/propagate_services", methods=["POST"])
    def propagate_services():
        if not precheck():
            _check_key()
        dna.propagate_services()
        return jsonify({"success": True})
    
    @api.route("/get_service_info/<name>")
    def get_service_info(name):
        if not precheck():
            _check_key()
        return jsonify(dna.get_service_info(name).to_json())
    
    @api.route("/add_domain", methods=["POST"])
    def add_domain():
        if not precheck():
            _check_key()
        data = request.get_json()

        service = data.get("service")
        domain = data.get("domain")
        force_wildcard = data.get("force_wildcard", False)

        dna.add_domain(service, domain, force_wildcard)
        return jsonify({"success": True})

    @api.route("/delete_service", methods=["DELETE"])
    def delete_service():
        if not precheck():
            _check_key()
        data = request.get_json()
        service = data.get("service")

        dna.delete_service(service)
        return jsonify({"success": True})
    
    return api

def create_logs_client(dna, fallback=None, precheck=lambda: True):
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
    from flask import abort, url_for, Blueprint
    logs = Blueprint('dna_logs', __name__)

    def _spcss(content=""):
        return '<link rel="stylesheet" href="https://unpkg.com/spcss">\n' + content
    
    def _link(service, log, title):
        return f"""<a href={
                url_for("dna_logs.servlog", service=service.name, log=log)
            }>{title}</a>"""

    @logs.route("/")
    def logs_index():
        if not precheck():
            abort(403)

        content = _spcss("<h1>DNA Service Logs</h1>")
        content += "<p>See nginx and docker logs for all your running services! "
        content += "Note that custom log types are currently not listed.</p>"
        content += f'<a href={url_for("dna_logs.dnalog")}>View Internal DNA Logs</a>'

        for service in dna.services:
            content += "<h3>" + service.name + "</h3>\n<ul>\n"
            content += f'<li>{_link(service, "nginx", "Nginx Access")}</li>\n'
            content += f'<li>{_link(service, "error", "Nginx Errors")}</li>\n'
            content += f'<li>{_link(service, "docker", "Container")}</li>\n'
            content += "</ul>\n"

        return content
    
    @logs.route("/dna")
    def dnalog():
        if not precheck():
            abort(403)
        return "<br />".join(dna.dna_logs().split("\n"))

    @logs.route("/<service>/<log>")
    def servlog(service, log):
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
    
    return logs
