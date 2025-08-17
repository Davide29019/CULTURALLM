FROM python:3.13

#working directory
WORKDIR /app

#copia dei requisiti necessari

COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

COPY src /app

#porta su cui gira FastAPI
EXPOSE 8003

#comando per avviare l'applicazione
CMD ["uvicorn","backend:app","--host","0.0.0.0","--port","8003","--reload"]