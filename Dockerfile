FROM python:3.12-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

ENV NAME leliel_env

CMD [ "python","main.py" ]
