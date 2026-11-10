#!/bin/bash

# Activate virtual environment and start the server
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

