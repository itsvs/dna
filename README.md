# docker-dna

<!-- begin readme -->

See this project on [GitHub](https://github.com/itsvs/dna). Current version is 0.4.6
([PyPI](https://pypi.org/project/docker-dna/)).

## Motivation

The `docker-dna` library is a collection of utilities that together simplify the process
of deploying webapps inside containers, all the while making sure the process is efficient,
customizable, and extensible.

## Without `docker-dna`

The standard procedure for accomplishing the task of deploying webapps inside containers may
look something like this:

1. Copy the relevant files to your webserver
2. Build and tag the container image
3. Find an open port on your machine to use in the next step
4. Run the container image you just built, exposing whatever port the front-end runs on
5. Write the webserver configuration to proxy your domain endpoint to the port you just exposed
6. Reload the webserver to host your front-end
7. Run certbot to get an SSL certificate for your domain endpoint

This sounds tedious, and even if you were to script it, it'd be a lot of scripting to do and
chances are it'd be hard to maintain if something goes wrong in the future (which, you know
it will in this field of work).

## With `docker-dna`

The process boils down to the following:

1. Receive a git webhook, and checkout the referenced commit
2. Call `dna.build_image`
3. Figure out what domain(s) you want to deploy this app to
4. Call `dna.run_deploy`

That's it! That handles your first deploy, second deploy, one hundredth deploy... you get the idea.

## What you need

To use this library, you need to install `docker`, `nginx`, and `certbot` on your machine. Then,
read the quickstart to see an example of how to get up and running with the `docker-dna` library!

<!-- end readme -->

You may also want to check out the `dna.utils.Logger` class for some logging utilities.

## Quickstart

A rudimentary example of how the `docker-dna` library may be used. We will demonstrate the basic
features of the app by creating a simple Flask app.

<!-- begin quickstart -->

First, create a `venv` and activate it.

```sh
python3 -m venv env
source env/bin/activate
```

Install `docker-dna` and whatever other tools you need.

```sh
env/bin/pip install docker-dna flask gunicorn
```

Write a simple Flask app that accepts the URL to an image and deploys it.

**app.py**
```python
from flask import Flask, jsonify
from dna import DNA

app = Flask(__name__)
dna = DNA("demo_dna")

@app.route("/deploy/<image>/<name>")
def deploy(image, name):
    """Pulls the ``image`` and deploys it to a service called ``name``.
    Sets up a webserver configuration to forward ``name``.example.com to
    the deployed app. Assumes the front-end runs on port 80.

    :param image: the name/url of the image to pull and deploy
    :type image: str
    :param name: the name to give this service
    :type name: str
    """
    
    dna.pull_image(image, name)
    dna.run_deploy(name, image, port="80")
    dna.add_domain(name, f"{name}.example.com")

    return jsonify({
        "success": True,
        "url": f"{name}.example.com",
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0")
```

Run your app. Note that `DNA` requires elevated privileges as of now to interface
with docker, nginx, and certbot, as all of these are privileged applications.

```sh
sudo env/bin/python app.py
```

Deploy an empty `nginx` container.

```sh
curl http://example.com:5000/nginx/dna-nginx
```

Visit `https://dna-nginx.example.com/` to see your shiny new `nginx` service!

<!-- end quickstart -->

For more complete sample implementations, see Sample Usages in the docs.

## Contributing

Guide coming soon, for now just use common sense! And the [GitHub Flow](https://guides.github.com/introduction/flow/).

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE.md) for more information.
