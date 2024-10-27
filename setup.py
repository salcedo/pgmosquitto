import setuptools


setuptools.setup(
    name="pgmosquitto",
    version="0.1.0",
    author="Brian Salcedo",
    author_email="brian@salce.do",
    description="Tool for managing Mosquitto SQL tables",
    url="https://github.com/salcedo/pgmosquitto.git",
    packages=setuptools.find_packages(),
    install_requires=["sqlalchemy", "psycopg2-binary", "passlib"],
    entry_points={"console_scripts": ["pgmosquitto = pgmosquitto.app:main"]},
)
