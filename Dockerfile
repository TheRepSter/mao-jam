# Utilitza una imatge base de Python
FROM python:3.10-slim

# Estableix el directori de treball dins del contenidor
WORKDIR /app

# Copia el fitxer de dependències
COPY requirements.txt .

# Instal·la les dependències
RUN pip install --no-cache-dir -r requirements.txt

# Copia la resta del codi del projecte al directori de treball
COPY . .

# La comanda per executar el simulador es gestionarà amb docker-compose
CMD ["python3", "simulator_combined_strategies.py"]
