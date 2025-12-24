# Use an official Python runtime as a parent image
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgtk2.0-dev \
    libgtk-3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install pip and build dependencies
RUN pip install --upgrade pip

# Install project dependencies using pyproject.toml (PEP 517/518)
RUN pip install megadetector-utils speciesnet

# Download SpeciesNet model weights at build time (inline)
RUN python -c "import kagglehub; kagglehub.model_download('google/speciesnet/pyTorch/v4.0.1a')"

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Set the default command to run your main script
CMD ["ls /working_volume", "&&", "python", "main.py", "/working_volume/temp"]
