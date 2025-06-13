# Base image
FROM python:3.10-slim

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.2

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Set working directory
WORKDIR /app

# Copy Poetry configuration first (for better build caching)
COPY pyproject.toml poetry.lock ./

# Install production dependencies only
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Copy the rest of the project files
COPY . .

# Expose Dash default port
EXPOSE 8050

# Command to run the app
# If you are using the 'stamm' script defined in pyproject.toml (recommended):
CMD ["poetry", "run", "stamm"]

# Alternative command if you prefer to run the app directly:
# CMD ["poetry", "run", "python", "Dashboard/app.py"]
