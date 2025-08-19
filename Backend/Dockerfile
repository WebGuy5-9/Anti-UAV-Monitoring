# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by OpenCV
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# 1. Copy ONLY the requirements file
COPY ./requirements.txt /app/requirements.txt

# 2. Install the dependencies. This layer will be cached.
#    If requirements.txt doesn't change, this step will be skipped on future builds.
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 3. Copy the rest of the backend application now.
#    If you only change app.py, the build will be super fast from now on.
COPY . /app

# Expose the port that Waitress will run on
EXPOSE 5000

# Command to run the application using the Waitress production server
# (Assuming your backend uses Flask/Waitress on port 5000)
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "app:app"]