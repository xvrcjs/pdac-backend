# ----- Base -----
FROM python:3.8 AS django-base

WORKDIR /src

# Instalar dependencias del sistema y optimizar la instalación en una sola capa
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  libpq-dev  \
  gcc \
  default-libmysqlclient-dev \
  libcap2 libcap2-bin libpam-cap iputils-ping gettext \
  python3-dev  graphviz  libgraphviz-dev  pkg-config \
  tesseract-ocr tesseract-ocr-spa

# Crear usuario 'django'
RUN groupadd django && \
    useradd django -g django && \
    chown -R django:django .

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar scripts y código de la aplicación
COPY ./docker/scripts/start /start
RUN chmod +x /start && sed -i 's/\r$//g' /start

COPY --chown=django:django ./ .

# Exponer puerto 8000
EXPOSE 8000


# ----- Desarrollo -----
FROM django-base AS django-develop

# Configuraciones específicas de desarrollo
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER django

EXPOSE 8000

# ----- Produccion -----
FROM django-base AS django-production

COPY ./docker/scripts/start.prod /start
RUN chmod +x /start && sed -i 's/\r$//g' /start

USER django

EXPOSE 8000

# Comando de inicio
CMD [ "bash", "-c", "/start" ]