from typing import Dict
from random import choice
import redis
from celery import Celery
from celery.exceptions import TimeoutError
from django.core.management.base import BaseCommand, CommandParser
from django.test import Client

from pymap.celery import app
from scripts.utils import generate_line_creds

class Command(BaseCommand):
    help = 'Populates the database by simulating sync requests'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--count", type=int, default=5, help="Number of operations")
        parser.add_argument("--user", type=str, default="", help="The user that will make the post requests (will be assigned as task.owner)")
        parser.add_argument("--password", type=str, default="", help="The password for the user")
        return super().add_arguments(parser)

    def generate_data(self) -> Dict[str,str]:
        source = f"vps{choice(range(100))}.pymap.tld"
        destination = f"vps{choice(range(100))}.pymap.tld"
        input_data = "\n".join(generate_line_creds(choice(range(1,10)), choice(["s", "d"])))
        data = {
            "source": source,
            "destination": destination,
            "input_text": input_data,
            "additional_arguments": "",
            "dry_run": choice([True,False])
        }

        return data
    
    def redis_is_running(self) -> bool:
        try:
            # Connect to Redis server
            client = redis.StrictRedis(host='localhost', port=6379)
            client.ping()  # Test connection
            return True
        except Exception as e:
            # Connection failed
            return False
        
    def celery_worker_is_running(self) -> bool:
        try:
            # Connect to Celery app
            # Inspect workers
            inspector = app.control.inspect()
            active = inspector.active()
            if active:
                return True
            return False
        except TimeoutError:
            # Connection timed out
            return False

    def handle(self, *args, **options) -> None:
        if not self.redis_is_running():
            self.stdout.write(self.style.ERROR(f"Error: Redis is not running"))
            return
        if not self.celery_worker_is_running():
            self.stdout.write(self.style.ERROR(f"Error: Celery worker is not running"))
            return
        count = options["count"]
        # Check the arguments, (defaults to superuser, password may need to be updated/provided)
        username = "pymin" if options["user"] == "" else options["user"]
        password = "Pymin" if options["password"] == "" else options["password"]
        # Create a Django test client
        client = Client(HTTP_HOST="localhost")

        # Login to the application 
        client.login(username=username, password=password)

        # Define the URL of the endpoint
        url = '/sync/'

        # Define the data to be sent in the request
        for _ in range(1,count):
            data = self.generate_data()
            # Send a POST request to the endpoint with session authentication
            response = client.post(url, data=data)
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('Sync request successful.'))
            else:
                self.stderr.write(self.style.ERROR(f'Error: {response.status_code}'))
