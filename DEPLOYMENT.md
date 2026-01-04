# 🚀 Guía de Deployment - Servidor Linux con OpenLiteSpeed

## Pre-requisitos

- Servidor Linux (Ubuntu/Debian recomendado)
- OpenLiteSpeed instalado
- Python 3.8+ instalado
- Git instalado
- Subdominio configurado: `sorteo.invite-art.com`

---

## 📦 Paso 1: Clonar Repositorio en el Servidor

```bash
# Conectar al servidor via SSH
ssh usuario@invite-art.com

# Navegar a directorio web
cd /var/www

# Clonar repositorio
sudo git clone https://github.com/luisalbertoquino/Predictor.git
cd Predictor

# Dar permisos
sudo chown -R www-data:www-data /var/www/Predictor
sudo chmod -R 755 /var/www/Predictor
```

---

## 🐍 Paso 2: Configurar Python y Dependencias

```bash
# Instalar pip y venv si no están instalados
sudo apt update
sudo apt install python3-pip python3-venv -y

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
python -c "import flask, pandas, sklearn, xgboost; print('✓ Todas las librerías instaladas')"
```

---

## 📂 Paso 3: Crear Archivos de Datos Iniciales

```bash
# Crear archivos JSON vacíos si no existen
cat > predicciones_historial.json << 'EOF'
{
  "predicciones": []
}
EOF

# Crear directorio de logs
mkdir -p logs

# Dar permisos de escritura
chmod 755 predicciones_historial.json
chmod 755 logs
```

---

## ⚙️ Paso 4: Configurar OpenLiteSpeed

### 4.1 Crear archivo de configuración para la aplicación

```bash
sudo nano /usr/local/lsws/conf/vhosts/sorteo/vhconf.conf
```

Contenido:

```apache
docRoot                   /var/www/Predictor/templates
enableGzip                1

context / {
  type                    proxy
  handler                 fcgi://127.0.0.1:5000
  addDefaultCharset       off
}

rewrite  {
  enable                  1
  autoLoadHtaccess        1
}
```

### 4.2 Crear Virtual Host

En el panel de OpenLiteSpeed (`https://tu-servidor:7080`):

1. **Virtual Hosts** → **Add**
   - Virtual Host Name: `sorteo`
   - Virtual Host Root: `/var/www/Predictor`
   - Config File: `/usr/local/lsws/conf/vhosts/sorteo/vhconf.conf`
   - Enable Scripts: `Yes`

2. **Listeners** → Agregar `sorteo.invite-art.com`
   - Port: `80` y `443` (SSL)
   - Virtual Host Mappings: `sorteo`

3. **Graceful Restart**

---

## 🔄 Paso 5: Configurar Supervisor (Mantener Flask corriendo)

```bash
# Instalar supervisor
sudo apt install supervisor -y

# Crear configuración
sudo nano /etc/supervisor/conf.d/superastro.conf
```

Contenido:

```ini
[program:superastro]
command=/var/www/Predictor/venv/bin/python /var/www/Predictor/superastro_web.py
directory=/var/www/Predictor
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/www/Predictor/logs/flask_error.log
stdout_logfile=/var/www/Predictor/logs/flask_output.log
environment=PATH="/var/www/Predictor/venv/bin"
```

Iniciar servicio:

```bash
# Recargar configuración
sudo supervisorctl reread
sudo supervisorctl update

# Iniciar aplicación
sudo supervisorctl start superastro

# Verificar estado
sudo supervisorctl status superastro
```

---

## ⏰ Paso 6: Configurar Cron para Ejecución Automática

```bash
# Editar crontab
crontab -e

# Agregar línea para ejecutar todos los días a las 2:00 AM
0 2 * * * cd /var/www/Predictor && ./run_all_predictors.sh >> /var/www/Predictor/logs/cron.log 2>&1
```

Dar permisos de ejecución al script:

```bash
chmod +x /var/www/Predictor/run_all_predictors.sh
```

---

## 🔒 Paso 7: Configurar SSL (HTTPS)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtener certificado SSL
sudo certbot certonly --webroot -w /var/www/Predictor/templates -d sorteo.invite-art.com

# Configurar OpenLiteSpeed para usar SSL
# En el panel: Listeners → SSL → Add
# - Certificate File: /etc/letsencrypt/live/sorteo.invite-art.com/fullchain.pem
# - Private Key File: /etc/letsencrypt/live/sorteo.invite-art.com/privkey.pem
```

---

## 🧪 Paso 8: Verificar Instalación

```bash
# 1. Verificar que Flask está corriendo
curl http://localhost:5000

# 2. Verificar desde fuera
curl http://sorteo.invite-art.com

# 3. Ejecutar manualmente un predictor de prueba
cd /var/www/Predictor
source venv/bin/activate
python superastro_predictor_mejorado.py

# 4. Verificar que se creó el JSON
cat predicciones_historial.json
```

---

## 📊 Comandos Útiles

### Ver logs de Flask
```bash
tail -f /var/www/Predictor/logs/flask_output.log
tail -f /var/www/Predictor/logs/flask_error.log
```

### Ver logs de Cron
```bash
tail -f /var/www/Predictor/logs/cron.log
```

### Reiniciar aplicación
```bash
sudo supervisorctl restart superastro
```

### Actualizar código desde GitHub
```bash
cd /var/www/Predictor
git pull origin main
sudo supervisorctl restart superastro
```

### Ver estado de supervisor
```bash
sudo supervisorctl status
```

---

## 🔧 Solución de Problemas

### Error: "Permission denied"
```bash
sudo chown -R www-data:www-data /var/www/Predictor
sudo chmod -R 755 /var/www/Predictor
```

### Error: "Module not found"
```bash
cd /var/www/Predictor
source venv/bin/activate
pip install -r requirements.txt
```

### Flask no inicia
```bash
# Ver logs
sudo supervisorctl tail -f superastro stderr

# Reiniciar
sudo supervisorctl restart superastro
```

### Cron no ejecuta
```bash
# Verificar sintaxis
crontab -l

# Ver logs del sistema
grep CRON /var/log/syslog
```

---

## 📝 Mantenimiento

### Backup de datos
```bash
# Crear backup diario automático (agregar a crontab)
0 3 * * * cp /var/www/Predictor/predicciones_historial.json /var/www/Predictor/backups/historial_$(date +\%Y\%m\%d).json

# Limpiar backups antiguos (mantener 30 días)
0 4 * * * find /var/www/Predictor/backups -name "historial_*.json" -mtime +30 -delete
```

### Actualizar dependencias
```bash
cd /var/www/Predictor
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo supervisorctl restart superastro
```

---

## 🎉 ¡Listo!

Accede a: **https://sorteo.invite-art.com**

El sistema:
- ✅ Genera predicciones automáticamente a las 2 AM
- ✅ Dashboard accesible 24/7
- ✅ Flask reinicia automáticamente si falla
- ✅ Logs guardados para debugging
