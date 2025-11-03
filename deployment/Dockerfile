# Base image
FROM python:3.10-slim

# Install dependencies for OpenCV + Java + ZBar
RUN apt-get update && apt-get install -y \
    openjdk-21-jre-headless \
    libzbar0 \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . /app
WORKDIR /app

# Expose port
EXPOSE 7860

# Jalankan Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0",  "--server.enableXsrfProtection=false"]
