# Imagem base: Linux mínimo com Python já instalado. Mesma versão do ambiente
# de desenvolvimento (3.14). "slim" = sem ferramentas extra, imagem mais pequena.
FROM python:3.14-slim

# PYTHONDONTWRITEBYTECODE: não gerar ficheiros __pycache__ dentro da imagem.
# PYTHONUNBUFFERED: mostrar os prints/logs de imediato em "docker logs".
# BIBLIOTECA_DB: caminho da base de dados dentro do container (ver database.py);
# fica na pasta /data, que será ligada a um volume do Docker.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BIBLIOTECA_DB=/data/biblioteca.db

WORKDIR /app

# Dependências primeiro, código depois: o Docker guarda cada passo em cache,
# por isso mudar o código não obriga a reinstalar o Flask de cada vez.
# gunicorn (servidor de produção) instala-se só aqui, não no requirements-web.txt,
# porque não corre em Windows. Versão fixa (a que o primeiro build instalou)
# para o build ser reproduzível.
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt gunicorn==26.2.0

# Só o que a versão web precisa (a GUI e os testes ficam de fora).
COPY database.py isbn_lookup.py ./
COPY web/ ./web/

# Utilizador sem privilégios: se alguém explorar uma falha na app, não tem root.
# A pasta /data tem de existir e pertencer a esse utilizador ANTES do volume ser
# ligado, senão o SQLite não consegue escrever lá.
RUN useradd --create-home appuser \
    && mkdir /data \
    && chown appuser:appuser /data
USER appuser

EXPOSE 8000

# 1) cria as tabelas (o gunicorn não passa pelo bloco __main__ do app.py);
# 2) arranca o gunicorn a escutar em 0.0.0.0 (acessível de fora do container).
# "exec" faz o gunicorn substituir o shell, para receber o Ctrl+C / docker stop.
CMD ["sh", "-c", "python -c 'from database import create_tables; create_tables()' && exec gunicorn --bind 0.0.0.0:8000 web.app:app"]
