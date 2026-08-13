# Escolhe uma versão leve do Python
FROM python:3.12-slim

# Define a pasta de trabalho dentro da "caixa"
WORKDIR /app

# Copia a lista de dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do teu código
COPY . .

# Diz à caixa qual o comando para iniciar
CMD ["python", "cli.py"]
