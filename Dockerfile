FROM python:3.11.9
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt gunicorn
COPY . /bot/
RUN chmod +x start.sh
ENV PATH=$PATH:/bot
EXPOSE 8082
CMD ["sh", "start.sh"]