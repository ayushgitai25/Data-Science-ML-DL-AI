FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOME=/home/app
ENV CREWAI_STORAGE_DIR=/home/app/.crewai
ENV XDG_DATA_HOME=/home/app/.local/share
ENV XDG_CONFIG_HOME=/home/app/.config
ENV STREAMLIT_CONFIG_DIR=/home/app/.streamlit

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directories and fix permissions
RUN mkdir -p \
    /home/app/.local/share \
    /home/app/.config \
    /home/app/.crewai \
    /home/app/.streamlit \
    /app/outputs \
    /app/logs \
    && chown -R app:app /home/app \
    && chown -R app:app /app

# Switch to app user
USER app

# Expose ports
EXPOSE 8000 8501

# Run backend with uvicorn directly, then frontend
CMD ["bash", "-c", "uvicorn app:app --host 0.0.0.0 --port 8000 --log-level info & streamlit run frontend_streamlit.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"]