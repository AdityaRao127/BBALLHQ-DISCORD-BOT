#!/bin/bash
# Start the Gunicorn server to serve the Flask application and run in foreground
gunicorn keep_alive:app --workers 4 --bind 0.0.0.0:8082 &

sleep 5

# Start the Discord bot  
python main.py