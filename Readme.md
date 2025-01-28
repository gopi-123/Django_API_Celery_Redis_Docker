GAN


## Step 1: Setting Up the Environment
	1. Create a Python environment:

		python -m venv env
		source env/bin/activate  # or .\env\Scripts\activate on Windows (If required in Powershell run as Admin with command:  Set-ExecutionPolicy RemoteSigned )
		
		#Example: PS:Send_cloud_Assignment_implementation> .\env\Scripts\activate  
		

	2. Install dependencies:

		pip install django djangorestframework celery redis docker
		
		#Generate requirements.txt: (Use pip to create the requirements.txt file. This file will list all the installed packages and their versions.)
		pip freeze > requirements.txt

	3. Create a Django project and app:
		django-admin startproject schedule_tasks
		cd schedule_tasks
		python manage.py startapp timers


	4. Update settings.py (Open the settings.py file in your Django project's main directory Ex: schedule_tasks\schedule_tasks\settings.py, Locate the INSTALLED_APPS list. This is where you define all the applications that are enabled in your Django project.

	   i)Add 'timers' and 'rest_framework' to the INSTALLED_APPS list. It should look something like thi:
				#schedule_tasks\schedule_tasks\settings.py
				INSTALLED_APPS = [
					'django.contrib.admin',
					'django.contrib.auth',
					'django.contrib.contenttypes',
					'django.contrib.sessions',
					'django.contrib.messages',
					'django.contrib.staticfiles',
					
					# Add your apps here
					'timers',
					'rest_framework',
				]




		ii)Configure Celery in settings.py: (our Django project will be set up to use Celery with Redis as the message broker. This enables you to manage background tasks effectively.) 
				# Scroll to the bottom of the file, or to a section where other configurations are defined. , Add the following Celery configuration:
				#schedule_tasks\schedule_tasks\settings.py
				
				# Celery configuration
				CELERY_BROKER_URL = 'redis://redis:6379/0'
				CELERY_ACCEPT_CONTENT = ['json']
				CELERY_TASK_SERIALIZER = 'json'







	5. Run initial migrations:


		python manage.py makemigrations
		python manage.py migrate
	
	


## Step 2: Model for Timers
Timers need persistence to survive application restarts.

	# timer/models.py
	from django.db import models
	import uuid

	class Timer(models.Model):
		id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
		url = models.URLField()
		scheduled_time = models.DateTimeField()
		is_fired = models.BooleanField(default=False)

		def __str__(self):
			return f"Timer {self.id} - Fired: {self.is_fired}"

	
	Run migrations:
	python manage.py makemigrations
	python manage.py migrate


## Step 3: Serializer for Validations
	This will handle user input validation, including invalid inputs.

	# timers/serializers.py
	# Serializer for Validations, This will handle user input validation, including invalid inputs.
	from rest_framework import serializers
	from .models import Timer
	from datetime import datetime, timedelta, timezone

	class TimerSerializer(serializers.ModelSerializer):
		#Serializer Fields:
		hours = serializers.IntegerField(write_only=True, min_value=0, required=True)
		minutes = serializers.IntegerField(write_only=True, min_value=0, required=True)
		seconds = serializers.IntegerField(write_only=True, min_value=0, required=True)

		class Meta:
			"""
			Meta class Defines the model to serialize and the fields to include.
			"""
			model = Timer
			fields = ['id', 'url', 'scheduled_time', 'is_fired', 'hours', 'minutes', 'seconds']

		def validate(self, data):
			# Ensures that the timer duration cannot be zero
			if data['hours'] == 0 and data['minutes'] == 0 and data['seconds'] == 0:
				raise serializers.ValidationError("Timer duration cannot be zero.")
			return data

		def create(self, validated_data):
			"""
			Create Method Calculates the total delay in seconds.
			Sets the scheduled_time based on the current time plus the delay.
			"""
			total_seconds = validated_data.pop('hours') * 3600 + validated_data.pop('minutes') * 60 + validated_data.pop('seconds')
			validated_data['scheduled_time'] = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)
			return Timer.objects.create(**validated_data)




## Step 4: API Views
	We need endpoints for creating timers and querying their status.
	
	# timer/views.py
		from rest_framework.views import APIView
		from rest_framework.response import Response
		from rest_framework import status
		from .models import Timer
		from .serializers import TimerSerializer
		from django.utils.timezone import now
		from .tasks import fire_webhook

		class TimerView(APIView):
			"""
			Handles the creation of timers.
			"""
			def post(self, request):
				serializer = TimerSerializer(data=request.data)
				if serializer.is_valid():
					timer = serializer.save()
					self.schedule_webhook(timer)
					return Response({'id': timer.id}, status=status.HTTP_201_CREATED)
				return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

			def schedule_webhook(self, timer):
				"""
				Schedule webhook firing using Celery.
				"""
				delay = max((timer.scheduled_time - now()).total_seconds(), 0)
				fire_webhook.apply_async((str(timer.id),), countdown=delay)


		class TimerDetailView(APIView):
			"""
			Handles querying a timer's status.
			"""
			def get(self, request, timer_id):
				try:
					timer = Timer.objects.get(id=timer_id)
					time_left = max((timer.scheduled_time - now()).total_seconds(), 0) if not timer.is_fired else 0
					return Response({'id': timer.id, 'time_left': time_left, 'fired': timer.is_fired})
				except Timer.DoesNotExist:
					return Response({'error': 'Timer not found'}, status=status.HTTP_404_NOT_FOUND)


## Step 5: Celery Task for Webhook
	Summary:
	- Create Celery instance, Refer - schedule_tasks/celery.py
	- Define the Task: In tasks.py, create a task to fire the webhook. Refer - timers/tasks.py
	- Schedule the Task: In the view, schedule the task when creating a timer. Refer  -  timer/views.py
	- Run the Worker: Ensure the Celery worker is running to execute the tasks. In terminal  Refer - 
	
	This ensures webhooks are fired reliably, even after restarts.
	### 5.1.1. Create Celery instance:
	
		# schedule_tasks/celery.py
		from celery import Celery

		app = Celery('timer_service', broker='redis://redis:6379/0')
		app.config_from_object('django.conf:settings', namespace='CELERY')
		app.autodiscover_tasks()


		
	### 5.1.2. Ensure Celery is Imported in __init__.py
	
		# schedule_tasks/__init__.py
		from __future__ import absolute_import, unicode_literals

		from .celery import app as celery_app

		__all__ = ('celery_app',)

	### 5.1.3. Install Required Packages (if not installed before, please install)
			pip install celery redis


	


	
	### 5.2. Create Celery task:
		
		# 5.2.1 timers/tasks.py  (Define the Task: In tasks.py, create a task to fire the webhook.)
		from celery import shared_task
		from .models import Timer
		import requests

		@shared_task
		def fire_webhook(timer_id):
			"""
			Fire the webhook for a given timer.
			"""
			try:
				timer = Timer.objects.get(id=timer_id, is_fired=False)
				requests.post(timer.url, json={'id': str(timer.id)})
				timer.is_fired = True
				timer.save()
			except Timer.DoesNotExist:
				pass
				
		## 5.2.2 Integrating the Task with Views  -- # timer/views.py -- Update the view that handles the creation of timers to schedule the fire_webhook task.
			###Schedule the Task When Creating a Timer: -- U already implemented above


   ### 5.3 Running the Celery Worker
   
   # Start the Celery Worker:  (Ensure the Celery worker is running to process the tasks. Open a terminal and run:)
   celery -A schedule_tasks worker --loglevel=info


## Step 6: Dockerize the Application
	## 1. Create Dockerfile:

	FROM python:3.9
	WORKDIR /app
	COPY requirements.txt .
	RUN pip install -r requirements.txt
	COPY . .
	CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

	## 2. Create docker-compose.yml:
	
	version: '3.8'
	services:
	  web:
		build: .
		ports:
		  - "8000:8000"
		depends_on:
		  - redis
	  redis:
		image: redis:6.2


## Step 7: Tests
	Write tests to validate the functionality.
	
	# timer/tests.py
	from django.test import TestCase
	from rest_framework.test import APIClient
	from .models import Timer
	from django.utils.timezone import now
	from datetime import timedelta

	class TimerTests(TestCase):
		def setUp(self):
			self.client = APIClient()

		def test_create_timer(self):
			response = self.client.post('/timer', {
				"hours": 0, "minutes": 1, "seconds": 0, "url": "https://example.com"
			}, format='json')
			self.assertEqual(response.status_code, 201)

		def test_get_timer(self):
			timer = Timer.objects.create(
				url="https://example.com",
				scheduled_time=now() + timedelta(seconds=60)
			)
			response = self.client.get(f'/timer/{timer.id}')
			self.assertEqual(response.status_code, 200)


## Step 8: README File
	Document build and run steps.
	
	# Timer Service

	## Setup
	1. Build the Docker image:
	   ```bash```
	   docker-compose build
	
	
	2. Run the service:	
	   docker-compose up
	   
	

 
## Step 9: API Endpoints
	1. Create a timer: POST /timer
	2. Query timer: GET /timer/<uuid:timer_id>



## Step 10: Tests - Run tests using
	python manage.py test


---

This  meets all the requirements, including invalid input handling, persistence across restarts, scalability, and testing. 



localhost:8000/hello/



http://localhost:8000/timer



Using Postman
Open Postman.

Create a New Request:

Click on the "New" button and select "Request".

Set the HTTP Method to POST:

Select POST from the dropdown menu.

Enter the Request URL:

Enter the URL of your Django endpoint, for example, http://localhost:8000/api/timer/.

Set Headers:

Go to the "Headers" tab.

Add a header with Key: Content-Type and Value: application/json.

Add the JSON Body:

Go to the "Body" tab.

Select "raw" and choose "JSON" from the dropdown menu.

Enter your JSON data. For example:

json
{
  "url": "http://example.com",
  "scheduled_time": "2025-01-25T12:00:00Z"
}
Send the Request:

Click the "Send" button.

Check the response to see if the request was successful.


{
  
  "scheduled_time": "2025-01-25T06:00:00",
  "hours": 4,
 "minutes": 0,
 "seconds": 1,
 "url": "https://twitter.com/"
}



gopi@GAN:/usr/bin$ sudo service redis-server start
[sudo] password for gopi:
gopi@GAN:/usr/bin$ redis-cli ping
PONG



curl --location 'http://localhost:8000/timer' \
--header 'Content-Type: application/json' \
--data '{
"scheduled_time": "2025-01-26T00:00:00",
"hours": 4,
"minutes": 0,
"seconds": 1,
"url": "https://twitter.com/"
}



POST: http://localhost:8000/timer
HEADERS:  Content-Type: application/json
raw:
{
"scheduled_time": "2025-01-26T00:00:00",
"hours": 4,
"minutes": 0,
"seconds": 1,
"url": "https://twitter.com/"
}



 File "C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation\env\Lib\site-packages\billiard\pool.py", line 406, in _ensure_messages_consumed
    if self.on_ready_counter.value >= completed:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<string>", line 7, in getvalue
OSError: [WinError 6] The handle is invalid
[2025-01-25 23:07:44,246: INFO/MainProcess] Task timers.tasks.fire_webhook[fd83ff1a-1831-448f-8011-76a4b1b3b53a] received
[2025-01-25 23:08:13,337: INFO/MainProcess] Task timers.tasks.fire_webhook[45bb06e0-b711-43a8-8303-cc42b72a8679] received



timer:Timer d29cbe47-73f1-46f0-a1ab-478b15832ca9 - Fired: False

Serializer:TimerSerializer(data={'scheduled_time': '2025-01-26T00:01:00', 'hours': 4, 'minutes': 0, 'seconds': 1, 'url': 'https://twitter.com/'}):
    id = UUIDField(read_only=True)
    url = URLField(max_length=200)
    scheduled_time = DateTimeField()
    is_fired = BooleanField(required=False)
    hours = IntegerField(min_value=0, required=True, write_only=True)
    minutes = IntegerField(min_value=0, required=True, write_only=True)
    seconds = IntegerField(min_value=0, required=True, write_only=True)


 data:{'scheduled_time': '2025-01-26T00:01:00', 'hours': 4, 'minutes': 0, 'seconds': 1, 'url': 'https://twitter.com/'}


[25/Jan/2025 23:44:00] "POST /timer HTTP/1.1" 201 45




++++++=

GET- /timer/be18064e-d265-4cb5-9716-34f249029a79

GET- /timer/d29cbe47-73f1-46f0-a1ab-478b15832ca9

{
    "id": "d29cbe47-73f1-46f0-a1ab-478b15832ca9",
    "time_left": 13347.326529,
    "fired": false
}



+++++
POST: 
http://localhost:8000/timer

{
"scheduled_time": "2025-01-26T00:40:00",
"hours": 4,
"minutes": 0,
"seconds": 1,
"url": "https://twitter.com/"
}

OUTPUt response:

{
    "id": "229d9660-20a3-49ad-961a-09188fd4d140",
    "time_left": 14400.902016
}

-----------
POST:


{
"scheduled_time": "2025-01-26T00:40:00",
"hours": 0,
"minutes": 5,
"seconds": 0,
"url": "https://twitter.com/"
}

-- 5 minutes ==300 seconds

output:

{
    "id": "1c2a8e26-417c-459a-99dd-1f5ca27bd067",
    "time_left": 299.975284
}



+++

output as 3min that is 212 second (from actual 300 - 60 sec == 212 --) 
GET:

http://localhost:8000/timer/1c2a8e26-417c-459a-99dd-1f5ca27bd067

{
    "id": "1c2a8e26-417c-459a-99dd-1f5ca27bd067",
    "time_left": 212.562094,
    "fired": false
}



# Steps to run Django Project , Celery and Redis-server

++++ New terminal : Djanog run:

PS C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation> .\env\Scripts\activate
(env) PS C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation> ls 

(env) PS C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation> cd .\schedule_tasks\      
(env) PS C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation\schedule_tasks> python manage.py runserver



+++ Note Trun off Mcaffe Anti virus, Firewall setting etc.

++++ New terminal: Celery run
PS C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation> .\env\Scripts\activate
(env) PS C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation> cd .\schedule_tasks\
(env) PS C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation\schedule_tasks> celery -A schedule_tasks worker --loglevel=info --pool=solo  



++++ New Terminal: redis-server
PS C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation> wsl
gopi@GAN:/mnt/c/Users/gopin/Documents/Jobs_2025/Sendcloud/Gan_Send_cloud_Assignment_implementation$ 
gopi@GAN:/mnt/c/Users/gopin/Documents/Jobs_2025/Sendcloud/Gan_Send_cloud_Assignment_implementation$  redis-server


Optional (Start Redis Server: If Redis is not running, you can start it with:):
gopi@GAN:/usr/bin$ sudo service redis-server start
[sudo] password for gopi:
gopi@GAN:/usr/bin$ redis-cli ping
PONG


++++


  
  schedule_tasks/
  ├── Dockerfile
  ├── docker-compose.yml
  ├── manage.py
  ├── requirements.txt
  ├── schedule_tasks/
  │   ├── __init__.py
  │   ├── settings.py
  │   ├── urls.py
  │   ├── wsgi.py
  ├── timers/
  │   ├── migrations/
  │   │   ├── __init__.py
  │   ├── __init__.py
  │   ├── models.py
  │   ├── serializers.py
  │   ├── views.py
  ├── ...


Install waitress (if not already installed):

sh
pip install waitress
Run your application with waitress (command used to run your Django application using the Waitress WSGI server. It tells Waitress to serve your Django app on port 8000.):
 
 waitress-serve --port=8000 schedule_tasks.wsgi:application



env) PS C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation\schedule_tasks> cd C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation\schedule_tasks
(env) PS C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation\schedule_tasks> waitress-serve --port=8000 schedule_tasks.wsgi:application
INFO:waitress:Serving on http://0.0.0.0:8000



docker-compose build

docker-compose up



Access Your Application:

Once the containers are up and running, you can access your Django application at http://localhost:8000


Simplified Workflow:
Build Docker Images:

Docker Compose uses the Dockerfile to build images for your services.

sh
docker-compose build
Start Containers:

Docker Compose starts the services (web, db, redis, celery) as defined in the docker-compose.yml.

sh
docker-compose up
Summary:
waitress-serve: Command to serve the Django app using Waitress.

Dockerfile: Defines steps to create a Docker image.

docker-compose.yml: Configures and runs multiple Docker containers for your application and its dependencies.


Instead of running:
python manage.py runserver
celery -A schedule_tasks worker --loglevel=info
redis-server


You simply run:

1) Start Docker Desktop: Ensure Docker Desktop is running.




Step 1: Navigate to the Project Directory using cd command , where the docker-compose.yml and Dockerfile , requirments.txt are located

Example: cd "C:\Users\gopin\Documents\Sendcloud\Send_cloud_Assignment_implementation\schedule_tasks"

Step 2: Build the Docker Images : Build the Docker images for your services (web, celery, etc.) as defined in the Dockerfile and docker-compose.yml. , following command will read the  docker-compose.yml file, use the Dockerfile to create the necessary images, and pull the required base images if they are not already available.
command below:

docker-compose build

Step 3: Start the Containers (Start all the services defined in your docker-compose.yml file, command below)
command below (Note to check logs u can use Examples : docker-compose logs or docker-compose logs celery:

docker-compose up

If you want to run the services in the background (detached mode), use the -d flag:
docker-compose up -d



Step 4: Access Your Application
Once the containers are up and running, you can access your Django application at http://localhost:8000. 
All the necessary services like PostgreSQL, Redis, and Celery will be running in the background, managed by Docker Compose.


Step5(optional) : Use POSTMAN, test your endpoints



Step 5: Run Migrations (if needed)
If you need to run migrations, you can do so by running the commands inside the web container:

docker-compose exec web python manage.py migrate


Step 6: Create a Superuser (if needed)
To create a superuser, run the following command inside the web container:

docker-compose exec web python manage.py createsuperuser


Step 7: Stop the Containers
When you're done, you can stop all the running containers with:

docker-compose down



1. docker-compose build

2. docker-compose up

3. docker-compose down

Access Your Application at http://localhost:8000
Your Django application will be accessible at http://localhost:8000, and all the necessary services like PostgreSQL, Redis, and Celery will be running in the background, managed by Docker Compose.

By using Docker and Docker Compose, you simplify the process of managing and running your application and its dependencies, making development and deployment much easier.


You now have a functional setup with Django, Celery, Redis, and PostgreSQL running in Docker containers. With this  application should be ready to handle asynchronous tasks efficiently.


++++ Helpful commands for docker run:


C:\Users\gopin\Documents\Jobs_2025\Sendcloud\Gan_Send_cloud_Assignment_implementation\schedule_tasks> ./format_code.sh 

./format_code.sh 
.\format_code.ps1

\schedule_tasks> .\format_code.ps1

docker-compose logs
docker ps


docker-compose exec web date
docker-compose exec celery date
docker-compose exec celery-beat date
docker-compose exec db date


./format_code.sh 

1) docker-compose build
2) docker-compose up -d
3) docker ps


docker-compose logs -f --tail="100" web

docker-compose logs -f --tail="100" celery
docker-compose logs -f --tail="100" celery-beat


docker-compose down


+++
Run Tests:

To run the tests, start the tests service:

sh
docker-compose run tests



docker-compose exec web python manage.py test



 docker-compose exec web coverage run --source='.' manage.py test
 docker-compose exec web coverage report
docker-compose exec web coverage html

docker cp <container_id>:/app/htmlcov ./htmlcov


++++++

tion\schedule_tasks> ruff check . --fix


Celery Beat will handle periodic tasks and ensure that your scheduled tasks are sent to Celery workers. This will help in managing timers and firing webhooks.


Webhook.site

https://webhook.site/c91aafb2-0e75-4cc6-bd1f-bc3888b1f629

Test website to see if really post was triggered after timer expiry : https://webhook.site/c91aafb2-0e75-4cc6-bd1f-bc3888b1f629



1) docker-compose build
2) docker-compose up -d
3) docker ps


4)  POST-  http://localhost:8000/timer


{
"hours": 0,
"minutes": 1,
"seconds": 0,
"url": "https://webhook.site/c91aafb2-0e75-4cc6-bd1f-bc3888b1f629"
}







Response:
{
    "id": "f9eeddad-ebc2-4dbc-82f8-c6d4378473d0",
    "time_left": 61
}




## 5) Wait for 5 sec  and do 

docker-compose down

Let the time expire for 2 mina



6)  docker-compose up -d
3) docker ps


+++++++++

GET 

http://localhost:8000/timer/f9eeddad-ebc2-4dbc-82f8-c6d4378473d0



{
    "id": "f9eeddad-ebc2-4dbc-82f8-c6d4378473d0",
    "time_left": 0
}



## Log of web 
docker-compose logs -f --tail="100" web


 def post(self, request):
 
 
web-1  | Operations to perform:
web-1  |   Apply all migrations: admin, auth, contenttypes, django_celery_beat, sessions, timers
web-1  | Running migrations:
web-1  |   No migrations to apply.
web-1  | INFO:waitress:Serving on http://0.0.0.0:8000
web-1  | ++ timer:Timer_id f9eeddad-ebc2-4dbc-82f8-c6d4378473d0 - Fired_status: True
web-1  | timer:Timer_id 02b8ec7e-f5b9-4dc6-8097-39c13ec99d31 - Fired_status: False 
web-1  | Serializer:TimerSerializer(data={'hours': 0, 'minutes': 0, 'seconds': 10, 'url': 'https://webhook.site/c91aafb2-0e75-4cc6-bd1f-bc3888b1f629'}):
web-1  |     id = UUIDField(read_only=True)
web-1  |     url = URLField(max_length=200)
web-1  |     scheduled_time = DateTimeField(read_only=True)
web-1  |     is_fired = BooleanField(read_only=True)
web-1  |     hours = IntegerField(min_value=0, required=True, write_only=True)
web-1  |     minutes = IntegerField(min_value=0, required=True, write_only=True)
web-1  |     seconds = IntegerField(min_value=0, required=True, write_only=True)
web-1  |  data:{'hours': 0, 'minutes': 0, 'seconds': 10, 'url': 'https://webhook.site/c91aafb2-0e75-4cc6-bd1f-bc3888b1f629'}
web-1  |  time_left:9
web-1  | Bad Request: /timer




### Log of celery -- fire_webhook:
docker-compose logs -f --tail="100" celery

@shared_task
def check_expired_timers():

elery-1  | [2025-01-27 03:49:00,003: INFO/MainProcess] Task timers.tasks.check_expired_timers[70bc08d9-0c09-45b5-b269-6f2bee4fd38f] received
celery-1  | [2025-01-27 03:49:00,004: INFO/ForkPoolWorker-16] Executing check_expired_timers task.
celery-1  | [2025-01-27 03:49:00,007: INFO/ForkPoolWorker-16] ++ Expired_timers list:<QuerySet []>
celery-1  | [2025-01-27 03:49:00,007: INFO/ForkPoolWorker-16] Completed check_expired_timers task.


### Log of celery-beat :  elery Beat will handle periodic tasks and ensure that your scheduled tasks are sent to Celery workers. This will help in managing timers and firing webhooks.
docker-compose logs -f --tail="100" celery-beat


docker-compose logs -f --tail="100" celery-beat
celery-beat-1  | Configuration ->
celery-beat-1  |     . broker -> redis://redis:6379/0
celery-beat-1  |     . loader -> celery.loaders.app.AppLoader
celery-beat-1  |     . scheduler -> django_celery_beat.schedulers.DatabaseScheduler



By implementing these changes, you can significantly enhance the performance and scalability of your application to handle high traffic volumes.




'CONN_MAX_AGE': 600,  # Connection pooling

Summary:
Database: Optimize with connection pooling.

Caching: Use Redis for caching and session management.

Asynchronous Processing: Use Celery with Redis for background tasks.

Load Balancing: Implement load balancing and auto-scaling.

Static and Media Files: Serve via CDN or cloud storage.

Monitoring: Implement logging and monitoring.

Security: Ensure HTTPS and other security best practices.