# Use the official Python image from the Docker Hub as the base image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the timezone
ENV TZ=Europe/Amsterdam

# Ensure the timezone package is installed and configure the timezone
RUN apt-get update && apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install the dependencies listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Expose the port your application runs on
EXPOSE 8000

# Specify the command to run the Django application using waitress
# common way to serve a Django application in a production environment.
# Waitress server on port 8000 and instructs it to use the WSGI application defined in the schedule_tasks.wsgi module.
# schedule_tasks is the name of the project or package, and wsgi is the Python file.
# application: This is the WSGI application callable within the wsgi module. It is usually an object or function that the WSGI server will use to handle requests.
CMD ["waitress-serve", "--port=8000", "schedule_tasks.wsgi:application"]
