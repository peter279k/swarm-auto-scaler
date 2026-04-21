FROM python:3.12-alpine
WORKDIR /app
RUN pip install docker requests
COPY auto_scaler.py .
CMD ["python", "autoscaler.py"]
