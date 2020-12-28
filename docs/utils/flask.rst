
Flask
=======================================================

Logs Client
-----------

The logs client exposes the following endpoints:

* ``/``: an index of all the available logs (doesn't include fallback logger options)
* ``/dna``: DNA's internal log printer (when it hasn't been overriden)
* ``/<service>/docker``: docker container logs for the requested service
* ``/<service>/nginx``: nginx access logs for the requested service
* ``/<service>/error``: nginx error logs for the requested service

.. autofunction:: dna.utils.create_logs_client

API Client
----------

The API client exposes the following endpoints relating to provisioning API keys:

* ``/``: an index of all active API keys
* ``/new_key``: create a new API key
* ``/manage_key?key=<key>``: manage the requested key
* ``/revoke_key/<key>``: revoke the requested key

The API client exposes the following endpoints that call :class:`~dna.DNA` functions:

* ``/pull_image``: pull a docker image
* ``/build_image``: build a docker image
* ``/run_deploy``: deploy a docker image
* ``/propagate_services``: refresh the services list on the current DNA instance
* ``/get_service_info/<name>``: get information about the requested service
* ``/add_domain``: add a domain to a service
* ``/remove_domain``: remove a domain from a service
* ``/delete_service``: delete a service

To see how to format your requests to these endpoints, read the source (pay attention to the calls to ``data.get``)

.. autofunction:: dna.utils.create_api_client
