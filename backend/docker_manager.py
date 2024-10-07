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

    def create_container(self):  # Check if the container already exists
        container_name = os.getenv("CONTAINER_NAME")
        try:
            self.container = client.containers.get(container_name)
            self.logger.debug(f"Container '{container_name}' already exists. Starting...")
            self.container.start()
        except docker.errors.NotFound:
            self.logger.debug(f"Container '{container_name}' does not exist. Proceeding to create...")
            # If the container does not exist, run a new PostgreSQL container with the persistent volume
            try:
                environment={
                        "POSTGRES_USER": os.getenv("DB_USER"),
                        "POSTGRES_PASSWORD": os.getenv("DB_PASSWORD"),
                        "POSTGRES_DB": os.getenv("DB_NAME"),
                    }
                self.logger.debug(environment)
                self.container = client.containers.run(
                    image="pgvector/pgvector:pg16",
                    name=container_name,
                    environment=environment,
                    ports={"5432/tcp": os.getenv("PORT")},  # Expose PostgreSQL port 5432
                    volumes={
                        os.getenv("VOLUME_NAME"): {'bind': '/var/lib/postgresql/data', 'mode': 'rw'}
                    },  # Mount volume to persist data
                    detach=True,  # Run container in the background
                )
                time.sleep(5)
                while True:
                    try:
                        conn = psycopg.connect(
                            host=os.getenv("HOSTNAME"),  # Use 'localhost' since we're connecting to the Docker container
                            port=os.getenv("PORT"),  # Port that PostgreSQL is exposed on
                            dbname=os.getenv("DB_NAME"),
                            user=os.getenv("DB_USER"),
                            password=os.getenv("DB_PASSWORD")
                        )
                        conn.close()
                        self.logger.debug("PostgreSQL is ready for operation.")
                        break
                    except psycopg.OperationalError:
                        self.logger.debug("PostgreSQL is not ready yet, retrying in 5 seconds...")
                        time.sleep(5)

            except Exception as e:
                self.logger.error(f"An error occurred: {e}")
                exit(1)

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
        self.create_container()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup(stop=self.stop_when_done, remove=self.remove_when_done)
        pass

    def __enter__(self):
        return self
