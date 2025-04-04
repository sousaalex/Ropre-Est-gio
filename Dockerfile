
FROM python:3.12-slim as builder

# Instalar dependências do sistema
RUN sed -i 's/deb.debian.org/ftp.br.debian.org/' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --fix-missing \
        build-essential \
        cmake \
        libopenblas-dev \
        libomp-dev \
        swig && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy dependencies and application code
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . .

# Default command
CMD ["python", "app.py"]
