FROM python:3.11.9
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
RUN pip install gunicorn 
COPY . /bot/
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "keep_alive:app"]