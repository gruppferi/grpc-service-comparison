FROM python:3.11.6-slim

WORKDIR /app
COPY . /app
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
WORKDIR /app/src
RUN echo "#!/bin/bash" > run_gunicorn.sh && \
    echo "trap 'kill -TERM \$!' SIGINT SIGTERM" >> run_gunicorn.sh && \
    echo "gunicorn -w \${WORKERS:-4} -k gthread -b 0.0.0.0:5000 main:app &" >> run_gunicorn.sh && \
    echo "wait \$!" >> run_gunicorn.sh && \
    chmod +x run_gunicorn.sh

CMD ["./run_gunicorn.sh"]
