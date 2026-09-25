# ============================================================
# backend/Dockerfile
# ============================================================
#
# WHAT IS A DOCKERFILE?
# A Dockerfile is a recipe that tells Docker how to build
# a "container image" for your application.
# Each line is an instruction. Docker reads them top-to-bottom.
#
# WHAT IS AN IMAGE vs CONTAINER?
# Image  = the recipe/snapshot (like a class in OOP)
# Container = a running instance of that image (like an object)
# ============================================================

# ---  STAGE 1: Choose a base image  ---
# FROM = "start from this pre-built image"
# python:3.11-slim = official Python 3.11, minimal size (no extras)
FROM python:3.11-slim

# ---  Set the working directory inside the container  ---
# WORKDIR = "from now on, all commands run from /app"
# Think of it as: cd /app inside the container.
WORKDIR /app

# ---  Install system dependencies  ---
# RUN = "execute a shell command during BUILD time"
# pdf2image (used in our AI pipeline) needs poppler-utils.
# We clean apt cache after to keep the image small.
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ---  Copy only requirements FIRST  ---
# Why? Docker caches each layer. If requirements.txt hasn't changed,
# Docker reuses the cached pip install layer — much faster rebuilds.
COPY requirements.txt .

# ---  Install Python dependencies  ---
# --no-cache-dir = don't save pip cache inside image (saves space)
RUN pip install --no-cache-dir -r requirements.txt

# ---  Copy the rest of the application code  ---
# COPY <source-on-host> <destination-in-container>
# The dot (.) means "current directory in the container" = /app
COPY . .

# ---  Tell Docker which port our app listens on  ---
# EXPOSE = documentation only — does NOT actually publish the port.
# The actual publishing happens in docker-compose.yml with "ports:".
EXPOSE 8000

# ---  The command to run when the container starts  ---
# CMD = the default command executed when `docker compose up` runs.
# We run uvicorn (the ASGI server for FastAPI).
#   --host 0.0.0.0  = listen on ALL interfaces (required in Docker)
#   --port 8000     = the port inside the container
#   --reload        = auto-restart when code changes (dev mode)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
