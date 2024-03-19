FROM python:3.9

WORKDIR ~/data_logger

COPY requirements.txt ./

# Get the dependencies
RUN pip install -r requirements.txt

# Copy everything allowed in .dockerignore from the current folder to 
# the present working directory
COPY . . 

# Run the application
ENTRYPOINT ["python3", "canInterface.py"]