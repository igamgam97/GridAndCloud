FROM python:3.8.0

ADD app.py, requirements.txt /app/

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "app.py"]