# Docker build command
# docker buildx build -t eraticwanderer/radio_listener:0.0.01 --load .
FROM python:3.14.0a2

# Install Python dependencies and other dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

# Install CUDA, cuDNN, and cupti (replace the version numbers with the correct versions you need)
ENV CUDA_VERSION 11.4.0
ENV CUDNN_VERSION 8.2.4.15
ENV PATH /usr/local/cuda-${CUDA_VERSION}/bin:${PATH}
ENV LD_LIBRARY_PATH /usr/local/cuda-${CUDA_VERSION}/lib64:${LD_LIBRARY_PATH}
ENV LD_LIBRARY_PATH /usr/local/cuda/extras/CUPTI/lib64:${LD_LIBRARY_PATH}

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY . .

# Install Python dependencies
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt


# Example: Run your script
CMD [ "python3", "-u", "radio.py"]
