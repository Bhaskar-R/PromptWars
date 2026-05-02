FROM python:3.12-slim

WORKDIR /app

# Install production dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py core.py firestore_client.py app.py ./
COPY .streamlit/ .streamlit/

# Expose Streamlit default port
EXPOSE 8080

# Cloud Run sets PORT env var; Streamlit needs explicit config
CMD ["streamlit", "run", "app.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
