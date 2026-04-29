FROM python:3.11

WORKDIR /app

COPY . .

# Install required dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    kafka-python

# Start FastAPI service (IMPORTANT: not python script)
CMD ["uvicorn", "producer:app", "--host", "0.0.0.0", "--port", "8001"]