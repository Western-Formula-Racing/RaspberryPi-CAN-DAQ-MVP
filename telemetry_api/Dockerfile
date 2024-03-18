FROM python:3.9

WORKDIR /home/telemetry_api

COPY requirements.txt ./

# Get the dependencies
RUN pip install -r requirements.txt

# Copy everything allowed in .dockerignore from the current folder to 
# the present working directory
COPY . . 

EXPOSE 5000

# Run the application
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "app:app"]