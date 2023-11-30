# This article was helpful: https://sourcery.ai/blog/python-docker/ 

# First build stage
FROM python:3.9.18-slim AS base

# Set locale
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Don't generate compiled python (.pyc) files
ENV PYTHONDONTWRITEBYTECODE 1

# Give stack traces on segmentation faults
ENV PYTHONFAULTHANDLER 1

# New build stage encapsulating the installation of all infrastructure + program dependencies 
FROM base AS python-dependencies

# Get pipenv
RUN pip install pipenv

# Update apt-get
RUN apt-get update

# Get GCC (C compiler)
RUN apt-get install -y --no-install-recommends gcc

# Copy python dependency files to here 
COPY Pipfile .
COPY Pipfile.lock .

# Create virtual environment in this folder (environment variable assignment + "pipenv")
#   and install the dependencies specified in the Pipfile ("install"), failing if the python 
#   version is wrong or any hashes in the Pipfile.lock are outdated (--local)
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

# New build stage where the canInterface-specific program actions are defined
FROM base AS runtime

# Use the virtual environment created in the last stage but not with the 
#   supporting resources used to make it
COPY --from=python-dependencies /.venv /.venv
ENV PATH="./venv/bin:$PATH"

# New user and use their home directory
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser 

# Copy everything from the current file to the /home/appuser working directory
COPY . . 

# Run the application
ENTRYPOINT ["python", "canInterface.py"]