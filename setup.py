from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()

setup(
    name="docker-dna",
    version="0.4.2",
    author="Vanshaj Singhania",
    author_email="vanshaj@berkeley.edu",
    long_description=readme,
    long_description_content_type="text/markdown",
    license="Apache License 2.0",
    packages=find_packages(include=["dna", "dna.utils"]),
    package_data={"": ["**/*.tex"]},
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "certbot==1.10.1",
        "certbot-nginx==1.10.1",
        "docker==4.4.0",
        "SQLAlchemy==1.3.22",
    ],
)
