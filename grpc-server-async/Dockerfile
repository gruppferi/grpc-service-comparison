FROM python:3.11.6-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools wheel
RUN pip install --no-cache-dir  -r requirements.txt
EXPOSE 50051
EXPOSE 8000

CMD ["python", "src/main.py"]



