FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY app.py .

RUN mkdir -p /app/uploads

EXPOSE 5000

ENV ADMIN_PASSWORD=admin
ENV SECRET_KEY=""

VOLUME /app/uploads
VOLUME /app/users.json

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
