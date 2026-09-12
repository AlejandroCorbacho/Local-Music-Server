# Gestor de Música Online

## Contexto
Este repositorio te guiará paso a paso para poder montar tu propio gestor de música online. En mi caso, he usado una **Raspberry Pi 3** como anfitriona para este proyecto. 

Teniendo en cuenta la seguridad, he usado **Docker** para desplegar el servicio de gestión de música y he configurado las reglas de firewall correspondientes. Para poder escuchar música fuera del área local de tu red (LAN o WLAN), puedes implementar un servicio de VPN. 

Usaremos el servicio **Navidrome** como gestor y servidor de nuestra librería de música descargada. Navidrome cuenta con **Subsonic**, una API muy conocida que nos permitirá la comunicación con aplicaciones de terceros. Recomiendo encarecidamente la aplicación open-source (Arpeggi)[https://github.com/argie-w/Arpeggi-App], desarrollada por [@argie-w](https://github.com/argie-w), para poder disfrutar de nuestra música en dispositivos iOS.

---

## Requisitos
* Servidor (en mi caso una Raspberry Pi 3).
* Python 3.12.X.
* Docker y Docker-compose.
* UFW o el cortafuegos correspondiente de tu sistema.

---

## Instalación

En primer lugar, vamos a preparar el entorno para el contenedor Docker de Navidrome.
Crearemos los directorios necesarios para almacenar todos los archivos y logs. En mi caso, he usado la siguiente distribución para el proyecto:

```text
.
├── data/
│   ├── cache/
│   │   ├── backgrounds/
│   │   ├── images/
│   │   ├── plugins/
│   │   └── transcoding/
│   └── navidrome.log
├── docker-compose.yml
├── music/
├── requirements.txt
└── music-downloader.py
```

* **`music/`**: Directorio donde almacenaremos las canciones previamente descargadas.
* **`data/`**: Directorio donde almacenaremos todos los datos que usará Navidrome (archivos de bases de datos, configuraciones...).
* **`data/cache/`**: Directorio donde se almacenará la caché.
* **`data/navidrome.log`**: Fichero en el cual se almacenarán todos los archivos informativos y registros de ejecución.
* **`docker-compose.yml`**: Fichero para construir y configurar el contenedor de Docker.

---

## Docker-compose

Para que Navidrome funcione, necesitas configurar tu archivo `docker-compose.yml`. (Asegúrate de configurar los volúmenes apuntando a las carpetas `data` y `music` que creamos).

Una vez dentro del directorio principal del proyecto, desplegaremos el contenedor en segundo plano con el comando:

```bash
docker compose up -d
```

> **Nota:** Por defecto, Navidrome toma el puerto `4533` y en el archivo `docker-compose.yml` he añadido la directiva `restart: unless-stopped` para automatizar el inicio en caso de que el servidor sea reiniciado.

---

## Reglas de Firewall (UFW)

En mi caso uso **UFW**. Si tienes configurado el firewall para denegar todas las peticiones entrantes por defecto, tenemos que crear una regla para dejar pasar el tráfico local a nuestro servidor por el puerto que hayamos establecido (4533).

Mi red privada se encuentra en la subred `192.168.1.0/24`, por lo que establezco esta regla para permitir todo el tráfico entrante desde esa red específica:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 4533 comment 'NavidromeServer'
```

---

## Configuración inicial y primeros pasos

Para entrar en la interfaz web, tendremos que escribir la siguiente dirección en nuestro navegador:

```text
http://[IP_DE_TU_SERVIDOR]:4533
```

La primera vez que entres, te pedirá crear una cuenta de administrador introduciendo un nombre de usuario y contraseña. ¡Y listo! Ya estás dentro de la interfaz de uso.

---

## Descarga de contenido

Para descargar nuestra música, utilizaremos el script en Python incluido en este repositorio. 

1. Primero, creamos un entorno virtual aislado para ejecutar nuestro script:
   ```bash
   python -m venv venv
   ```

2. Lo iniciamos:
   ```bash
   source ./venv/bin/activate
   ```

3. Actualizamos `pip` e instalamos las librerías requeridas:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

Para la descarga en cadena, necesitaremos un archivo *CSV* con todas las canciones que queramos descargar. (Para exportar listas de Spotify a *CSV*, recomiendo la web [Exportify]([exportify](https://exportify.app/)) de [@watsonbox](https://github.com/watsonbox)).

4. Una vez tengamos nuestro archivo CSV, ejecutamos el script:
   ```bash
   python music-downloader.py
   ```
   * Escogeremos la **Opción 2**.
   * Le indicamos la ruta de nuestro archivo CSV.
   * Le indicamos la ruta donde se almacenará todo el contenido (nuestra carpeta `music/`). Automáticamente descargará todas las canciones listadas en el CSV.

### Sobre music-downloader.py`

* Este script permite descargar contenido de YouTube mediante la librería `yt-dlp`.
* El códec elegido por defecto, después de múltiples pruebas, es **OPUS** (el formato original de YouTube).
* En caso de no indicar ningún directorio de almacenamiento, el script creará automáticamente una carpeta `music/` en el directorio actual.
* Si la carpeta destino ya contiene música previamente descargada, el script omitirá la descarga de esas canciones para evitar duplicidades.

---

## Arpeggi (Solo para iOS)

(Arpeggi)[https://github.com/argie-w/Arpeggi-App] es una aplicación móvil que se comunica con la API de ***Subsonic*** para que puedas escuchar las canciones de tu servidor en tu dispositivo móvil.

Solo tienes que instalarla desde la App Store, indicar la dirección IP/URL de tu servidor Navidrome e iniciar sesión con la cuenta que creaste previamente.

*Desarrollada por [@argie-w](https://github.com/argie-w)
