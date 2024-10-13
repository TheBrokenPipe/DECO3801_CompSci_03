import os
import time
import logging

import docker
from docker.models.volumes import Volume
from docker.models.containers import Container
from docker.errors import NotFound

import psycopg  # Import psycopg3
from dotenv import load_dotenv

load_dotenv()

# Initialize Docker client
client = docker.from_env()


class DockerManager:

    def __init__(self, stop_when_done=False, remove_when_done=False):
        self.volume: Volume | None = None
        self.container: Container | None = None
        self.remove_when_done = remove_when_done
        self.stop_when_done = stop_when_done
        self.logger = logging.getLogger(__name__)

    def create_volume(self):
        volume_name = os.getenv("VOLUME_NAME")
        # Create a Docker volume for persistent storage, if it doesn't exist
        try:
            self.volume = client.volumes.get(volume_name)
            self.logger.debug(f"Volume '{volume_name}' already exists.")
        except NotFound:
            self.volume = client.volumes.create(name=volume_name)
            self.logger.debug(f"Volume '{volume_name}' created.")

    def create_container(self):
        container_name = os.getenv("CONTAINER_NAME")
        volume_name = os.getenv("VOLUME_NAME")
        self.logger.debug(f"Creating container '{container_name}'...")
        # Run a new PostgreSQL container with the persistent volume
        environment = {
                "POSTGRES_USER": os.getenv("DB_USER"),
                "POSTGRES_PASSWORD": os.getenv("DB_PASSWORD"),
                "POSTGRES_DB": os.getenv("DB_NAME"),
            }
        self.logger.debug(environment)
        self.container = client.containers.run(
            image="pgvector/pgvector:pg16",
            name=container_name,
            environment=environment,
            # Expose PostgreSQL port 5432
            ports={"5432/tcp": os.getenv("PORT")},
            # Mount volume to persist data
            volumes={
                volume_name: {'bind': '/var/lib/postgresql/data',
                              'mode': 'rw'}
            },
            # Run container in the background
            detach=True,
        )
        while True:
            try:
                time.sleep(5)
                conn = psycopg.connect(
                    # Usually 'localhost' to connect to a Docker container
                    host=os.getenv("HOSTNAME"),
                    # Port that PostgreSQL is exposed on
                    port=os.getenv("PORT"),
                    dbname=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD")
                )
                conn.close()
                self.logger.debug("PostgreSQL is ready for operation.")
                break
            except psycopg.OperationalError:
                self.logger.debug("PostgreSQL not ready, retrying in 5s ...")

    def setup_container(self):
        # Check if the container already exists
        container_name = os.getenv("CONTAINER_NAME")
        try:
            self.container = client.containers.get(container_name)
            self.logger.debug(f"Starting container '{container_name}'...")
            self.container.start()
        except docker.errors.NotFound:
            self.create_container()

        self.logger.info("Container running.")

    def cleanup(self, stop=False, remove=False):
        if stop:
            self.container.stop()
            self.logger.debug("Container stopped.")
            if remove:
                self.container.remove()
                self.logger.debug("Container removed.")
                self.volume.remove()
                self.logger.debug("Volume removed.")

    def full_setup(self):
        self.create_volume()
        self.setup_container()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup(stop=self.stop_when_done, remove=self.remove_when_done)
        pass

    def __enter__(self):
        return self
