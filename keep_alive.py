from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def index():
    return "Alive"

def run():
    app.run(host='0.0.0.0', port=8082)
    
def keep_alive():
    server = Thread(target=run)
    server.start()