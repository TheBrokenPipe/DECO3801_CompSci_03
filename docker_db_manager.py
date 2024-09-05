import os
import docker
from docker.models.volumes import Volume
from docker.models.containers import Container
from docker.errors import NotFound
import time
import psycopg  # Import psycopg3
from psycopg import sql
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Initialize Docker client
client = docker.from_env()


class PG_Manager:

    def __init__(self):
        self.volume: Volume | None = None
        self.container: Container | None = None

    def create_volume(self, verbose=False):
        volume_name = os.getenv("VOLUME_NAME")
        # Create a Docker volume for persistent storage, if it doesn't exist
        try:
            self.volume = client.volumes.get(volume_name)
            if verbose: print(f"Volume '{volume_name}' already exists.")
        except NotFound:
            self.volume = client.volumes.create(name=volume_name)
            if verbose: print(f"Volume '{volume_name}' created.")

    def create_container(self, verbose=False):  # Check if the container already exists
        container_name = os.getenv("CONTAINER_NAME")
        try:
            self.container = client.containers.get(container_name)
            if verbose: print(f"Container '{container_name}' already exists. Starting...")
            self.container.start()
        except docker.errors.NotFound:
            if verbose: print(f"Container '{container_name}' does not exist. Proceeding to create...")
            # If the container does not exist, run a new PostgreSQL container with the persistent volume
            try:
                self.container = client.containers.run(
                    image="pgvector/pgvector:pg16",
                    name=container_name,
                    environment={
                        "POSTGRES_USER": os.getenv("DB_USER"),
                        "POSTGRES_PASSWORD": os.getenv("DB_PASSWORD"),
                        "POSTGRES_DB": os.getenv("DB_NAME"),
                    },
                    ports={f"{os.getenv('PORT')}/tcp": os.getenv("PORT")},  # Expose PostgreSQL port 5432
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
                        if verbose: print("PostgreSQL is ready for operation.")
                        break
                    except psycopg.OperationalError:
                        if verbose: print("PostgreSQL is not ready yet, retrying in 5 seconds...")
                        time.sleep(5)

            except Exception as e:
                print(f"An error occurred: {e}")
                exit(1)

        if verbose:
            print("Container running.")

    def cleanup(self, remove=False, verbose=False):
        self.container.stop()
        if verbose: print("Container stopped.")
        if remove:
            self.container.remove()
            if verbose: print("Container removed.")
            self.volume.remove()
            if verbose: print("Volume removed.")

    def full_setup(self, verbose=False):
        self.create_volume(verbose)
        self.create_container(verbose)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup(remove=True)
        pass

    def __enter__(self):
        return self
