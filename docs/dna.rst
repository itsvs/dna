
DNA
=======================================================

Initialization
--------------

When an instance is created for the first time, it is initialized by
creating a ``.dna`` folder in the current working directory. An nginx
mapping is added to include configs in ``.dna/nginx``, a socat container
is created to proxy requests made to services managed by this DNA instance
(the containers are connected via an internal bridge network), and a
:class:`~dna.utils.SQLite` database is created inside ``.dna``.

``dna.DNA``
-----------

.. autoclass:: dna.DNA
    :members:
