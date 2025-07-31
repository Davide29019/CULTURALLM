FROM python:3.13

#working directory
WORKDIR /app

#copia dei requisiti necessari
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app
COPY templates /app/templates

#porta su cui gira FastAPI
EXPOSE 8001

#comando per avviare l'applicazione
CMD ["uvicorn","frontend:app","--host","0.0.0.0","--port","8001","--reload"]