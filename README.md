# Online Music Manager

## Context
This repository will guide you step by step to set up your own online music manager. In my case, I have used a Raspberry Pi 3 as the host for this project. 

Taking security into consideration, I have used Docker to deploy the music management service and configured the corresponding firewall rules. In order to listen to music outside your local network area (LAN or WLAN), you can implement a VPN service. 

We will use the Navidrome service as the manager and server for our downloaded music library. Navidrome features Subsonic, a widely known API that allows communication with third-party applications. I highly recommend the open-source application (Arpeggi)[https://github.com/argie-w/Arpeggi-App], developed by  [@argie-w](https://github.com/argie-w), to enjoy our music on iOS devices.

## Requirements
* Server (in my case, a Raspberry Pi 3).
* Python 3.12.X.
* Docker and Docker-compose.
* UFW or the corresponding firewall for your system.

## Installation
First, we will prepare the environment for the Navidrome Docker container. 

We will create the necessary directories to store all files and logs. In my setup, I have used the following directory structure for the project:

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

* **music/:** Directory where we will store the previously downloaded songs.
* **data/:** Directory where we will store all the data utilized by Navidrome (database files, configurations...).
* **data/cache/:** Directory where the cache will be stored.
* **data/navidrome.log:** File where all informational logs and execution records will be stored.
* **docker-compose.yml:** File to build and configure the Docker container.

## Docker-compose
For Navidrome to function, you need to configure your `docker-compose.yml` file. (Ensure you configure the volumes pointing to the `data` and `music` folders we created).

Once inside the main project directory, we will deploy the container in the background using the following command:

```bash
docker compose up -d
```
*Note: By default, Navidrome uses port 4533, and in the `docker-compose.yml` file, I have added the `restart: unless-stopped` directive to automate the startup in case the server is rebooted.*

## Firewall Rules (UFW)
In my case, I use UFW. If your firewall is configured to deny all incoming requests by default, we must create a rule to allow local traffic to pass through to our server via the port we have established (4533).

My private network is located on the 192.168.1.0/24 subnet, so I establish this rule to allow all incoming traffic from that specific network:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 4533 comment 'NavidromeServer'
```

## Initial Configuration and First Steps
To access the web interface, we must enter the following address into our browser:

`http://[YOUR_SERVER_IP]:4533`

The first time you log in, it will prompt you to create an administrator account by entering a username and password. And you are all set! You are now inside the user interface.

## Content Download
To download our music, we will use the Python script included in this repository. 

First, we create an isolated virtual environment to execute our script:
```bash
python -m venv venv
```

We activate it:
```bash
source ./venv/bin/activate
```

We update pip and install the required libraries:
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For batch downloading, we will need a CSV file containing all the songs we want to download. (To export Spotify playlists to CSV, I recommend the ([exportify](https://exportify.app/)) website by  [@watsonbox](https://github.com/watsonbox).

Once we have our CSV file, we execute the script:
```bash
python music-downloader.py
```
* We will select Option 2.
* We provide the path to our CSV file.
* We indicate the path where all the content will be stored (our `music/` folder). It will automatically download all the songs listed in the CSV.

## About music-downloader.py
* This script allows downloading content from YouTube using the `yt-dlp` library.
* The default codec chosen, after multiple tests, is OPUS (the original YouTube format).
* In case no storage directory is specified, the script will automatically create a `music/` folder in the current directory.
* If the destination folder already contains previously downloaded music, the script will skip the download of those songs to avoid duplicates.

## Arpeggi (iOS Only)
(Arpeggi)[https://github.com/argie-w/Arpeggi-App] is an excellent mobile application that communicates with the Subsonic API so you can listen to the songs from your server on your mobile device.

You just have to install it from the App Store, provide the IP address/URL of your Navidrome server, and log in with the account you created previously.

*Developed by  [@argie-w](https://github.com/argie-w)

