# ---------- Stage 1: Build dependencies ----------
FROM python:3.12-slim AS builder

# Environment variables to improve Python behavior and set Poetry version
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.3

# Install system tools and Poetry
# Note: Removed the duplicated 'apt-get' and typo in the RUN line
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential \
    && pip install --no-cache-dir poetry==$POETRY_VERSION \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy Poetry configuration files first (to take advantage of Docker cache)
COPY pyproject.toml poetry.lock ./

# Copy source code BEFORE installing dependencies (so local paths exist)
COPY src/ ./src

# Install only the main (production) dependencies, without creating a virtual environment
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# ---------- Stage 2: Final lightweight image ----------
FROM python:3.12-slim

# Set working directory for the final image
WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12

# Copy the application source code
COPY --from=builder /app/src ./src

# Add 'src' to PYTHONPATH for absolute imports (e.g. Dashboard.app)
ENV PYTHONPATH="/app/src"

# Expose the default Dash port
EXPOSE 8050

# Command to run the Dash app
# You can use the Poetry script (if defined in pyproject.toml):
# CMD ["poetry", "run", "stamm"]

# Or run the app directly (most common option)
CMD ["python", "-m", "Dashboard.app"]
