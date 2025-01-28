Context
The assignment involves creating a web service that allows for the execution of scheduled tasks. The tasks are defined by a URL and a specific time to run. The core functionality includes setting a timer and firing a webhook when the timer expires. The service must handle invalid inputs, ensure the timers persist through restarts, support horizontal scalability, and ensure each timer is fired only once.

Functional Requirements
Set Timer Endpoint: Accepts a JSON object with hours, minutes, seconds, and a URL. It starts an internal timer and returns the time left and a timer ID.

Get Timer Endpoint: Returns the time left for a given timer ID.

Technical Requirements
Handle invalid inputs and ensure robustness.

Timers must persist through process restarts.

Horizontal scalability to handle increasing numbers of timers.

Fire each timer only once.

Implemented in Python using Django, Django REST Framework, FastAPI, or Flask.

Dockerize the application for easy deployment.

Include sensible testing.

Tech Stack
Programming Language:

Python

Frameworks:

Django + Django REST Framework (or Django Ninja)

FastAPI

Flask

Containerization:

Docker

Testing:

Unit tests (with libraries like pytest, unittest)

Caching (Optional for Performance):

Redis or similar caching solution (for horizontal scalability and persistence)

Message Broker (For Asynchronous Tasks):

Celery with Redis or RabbitMQ (if needed)

Database (For Persistence):

PostgreSQL or any other relational database supported by Django/FastAPI/Flask

Implementation
Endpoints:

/timer (POST): Set a timer.

/timer/{timer_uuid} (GET): Get the timer status.

Docker:

Use Docker to wrap the application and its dependencies.

Provide a Dockerfile and docker-compose.yml for building and running the application.

Readme:

Include clear instructions on how to build, run, and test the application.

Testing:

Write tests to ensure the key functionalities work as expected.





## Files to read:  "README.md" ,  "Assignment_Documentation_Notes.docx" and "Technical_assignment_new.pdf"



# Note 1: Use notepad++ to read this README file.(indentation would be clearer)

# Note 2: There is additional "Assignment_Documentation_Notes.docx" in the submission folder, please refer ,where  I mentioned answers for all the "Requirements of Technical Assignment"




## Pre-requisites:
	
	- Install "Docker Desktop" application 

	- Start Docker Desktop: Ensure Docker Desktop is running.
	- WEB browser

	- Install POSTMAN (to test API or end points)
	- Terminal (VS code or Powershell terminal) 
	- Have VS code editor , notepad++ editors 
	- Requirements.txt file has all the dependecies that need to be installed.



####### Build steps and HOW to Run the application #########
 
## Step 1: Download the submiited code, unzip it, copy to your desired folder and 
## In Terminal, Navigate to the Project Directory using cd command , where the Dockerfile, docker-compose.yml and requirements.txt are located

Example: cd .\schedule_tasks\


## Note: Ensure Docker Desktop is running.

## Step 2: Build the Docker Images : Build the Docker images for your services (web, celery, etc.) as defined in the Dockerfile and docker-compose.yml. , following command will read the  docker-compose.yml file, use the Dockerfile to create the necessary images, and pull the required base images if they are not already available.

	run command below:

	docker-compose build


## Step 3: Start the Containers (Start all the services defined in your docker-compose.yml file, command below) -run command below:

	docker-compose up

	Note: 1) If you want to run the services in the background (detached mode), use the -d flag:
	docker-compose up -d
	
	 #### To check status (use new terminal and run following command)
	 docker ps

	2) command below (Note to check logs u can use Examples : 
	docker-compose logs or docker-compose logs celery:



## Note : If previous docker processes and servicess are running successfulling , GO to Step 4
All the necessary services like PostgreSQL, Redis, and Celery will be running in the background, managed by Docker Compose.


## Step 4: Access Your Django Application (using Web browser or POSTMAN)

Once the containers are up and running, you can access your Django application at Web browser: http://localhost:8000/ui_timer
E


## Step5 (optional) : Use POSTMAN, To test your endpoints

		#### Example 1) Send   POST request with following JSON data passed to end point -  http://localhost:8000/timer
		Pass following JSON object containing hours, minutes, seconds, and a web url.

		
		{
		"hours": 0,
		"minutes": 1,
		"seconds": 0,
		"url": "https://webhook.site/c91aafb2-0e75-4cc6-bd1f-bc3888b1f629"
		}



		YOu will get Response:
		{
			"id": "f9eeddad-ebc2-4dbc-82f8-c6d4378473d0",
			"time_left": 60
		}

		
		You can visit https://webhook.site/#!/view/c91aafb2-0e75-4cc6-bd1f-bc3888b1f629/27913c73-e862-4d28-8604-2d205f850979/1 , to see that after 60 seconds
		the Post url you passed will be triggered and response can be seen.
		 -----------------------------------------------------------

		#### Example 2) Use the response "id" value and use as input to get request endpoint: /timer/{timer_uuid}
		GET Request - /timer/f9eeddad-ebc2-4dbc-82f8-c6d4378473d0
		

		http://localhost:8000/timer/f9eeddad-ebc2-4dbc-82f8-c6d4378473d0


		Response:
		{
			"id": "f9eeddad-ebc2-4dbc-82f8-c6d4378473d0",
			"time_left": 0
		}
		
		
		## Example 3: To check Scenario: if app is down, timer expired  and if app restarted and to see if webhook should be triggered once the application comes back up.
		Initiate a timer using POST request, and once request submiited, do docker-compose down, let the timer gets expired and again repeat docker-compose up -d,
		The post url will which was expired will be triggered , u can see back in https://webhook.site/#!/view/c91aafb2-0e75-4cc6-bd1f-bc3888b1f629/27913c73-e862-4d28-8604-2d205f850979/1
		
		Response:
		{
	  "id": "ca9ca27d-5d99-4452-aa22-2deb5a4b26b1"
	   }


## Step 6: Stop the Containers
When you're done, you can stop all the running containers with command below:  


docker-compose down



OPTIONAL steps below:

## Step 5: Run Migrations (if needed)
If you need to run migrations, you can do so by running the commands inside the web container:

docker-compose exec web python manage.py migrate


## Step 7: Stop the Containers
When you're done, you can stop all the running containers with:

docker-compose down




# Note : There is additional "Assignment_Documentation_Notes.docx" in the submission folder, please refer ,where  I mentioned answers for all the "Requirements of Technical Assignment"
