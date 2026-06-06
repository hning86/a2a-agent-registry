# Use a slim Python base image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set the working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy pyproject.toml to install dependencies
COPY pyproject.toml ./

# Install dependencies (ignoring the local package install for now)
RUN uv pip install --system -r pyproject.toml

# Copy source code and config files
COPY app/ ./app/
COPY remote_agent/ ./remote_agent/
COPY deploy/deployment_metadata.json ./deploy/deployment_metadata.json

# Expose default Cloud Run port
EXPOSE 8080

# Configure environment variables
ENV PORT=8080
ENV GOOGLE_GENAI_USE_VERTEXAI=TRUE
ENV GOOGLE_CLOUD_PROJECT=ninghai-ccai
ENV GOOGLE_CLOUD_LOCATION=global
ENV PYTHONUNBUFFERED=1

# Run the FastAPI app
CMD ["python", "-m", "app.web_app"]
