FROM python:3

ADD /app /app

EXPOSE 80 443

RUN pip install -r /app/requirements.txt

ENTRYPOINT ["python", "/app/app.py"]
