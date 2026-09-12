import base64
import csv
import os
import re
import time
import urllib.request

import static_ffmpeg
import yt_dlp
from mutagen.flac import Picture
from mutagen.oggopus import OggOpus

# Downloads (only the first time) the portable ffmpeg/ffprobe binaries
# inside the Python environment itself.
ffmpeg_path, ffprobe_path = static_ffmpeg.run.get_or_fetch_platform_executables_else_raise()
ffmpeg_dir = os.path.dirname(ffmpeg_path)


def sanitize_filename(name):
    return re.sub(r'[\\/:"*?<>|]+', "_", name).strip()


def download_cover_from_url(url):
    if not url:
        return None
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read()
    except Exception as e:
        print(f"  Could not download the cover art: {e}")
        return None


def _download_best_audio(query_list, temp_path_no_ext, final_path):
    """Tries several search queries until the audio is successfully downloaded.
    Returns (final_path, info) from the first attempt that works."""
    ydl_opts = {
        # We grab the best real audio quality available. On YouTube
        # this is almost always Opus, so this usually ends up
        # being a remux (direct lossless copy) instead of a
        # transcode.
        "format": "bestaudio[acodec=opus]/bestaudio/best",
        "outtmpl": f"{temp_path_no_ext}.%(ext)s",
        "noplaylist": True,
        "ffmpeg_location": ffmpeg_dir,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "opus",
                "preferredquality": "0",
            }
        ],
    }

    last_error = None
    for query in query_list:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
            if "entries" in info:
                info = info["entries"][0]
            temp_path = f"{temp_path_no_ext}.opus"
            os.replace(temp_path, final_path)
            return final_path, info
        except Exception as e:
            last_error = e
            continue

    raise last_error


def write_metadata(audio_path, title, artist, album, track_number, year, cover_bytes):
    audio = OggOpus(audio_path)

    audio["title"] = title
    if artist:
        audio["artist"] = artist
    if album:
        audio["album"] = album
    if track_number:
        audio["tracknumber"] = str(track_number)
    if year:
        audio["date"] = str(year)

    if cover_bytes:
        pic = Picture()
        pic.data = cover_bytes
        pic.type = 3  # front cover
        pic.mime = "image/jpeg"
        pic_data = base64.b64encode(pic.write()).decode("ascii")
        audio["metadata_block_picture"] = [pic_data]

    audio.save()


def download_single_song(song_name, destination_folder="musica"):
    os.makedirs(destination_folder, exist_ok=True)
    clean_name = sanitize_filename(song_name)
    final_path = os.path.join(destination_folder, f"{clean_name}.opus")

    if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
        print("That song is already downloaded, skipping it.")
        return final_path

    queries = [
        f"ytsearch1:{song_name} lyrics",
        f"ytsearch1:{song_name} audio",
    ]
    temp_path_no_ext = os.path.join(destination_folder, "temp_audio")

    try:
        audio_path, info = _download_best_audio(queries, temp_path_no_ext, final_path)
    except Exception as e:
        print(f"ERROR downloading audio: {e}")
        return None

    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        print("ERROR: the file came out empty/corrupted, discarding it.")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return None

    # yt-dlp sometimes provides real music metadata (artist/album/year) if the
    # video has an associated YouTube Music Content ID; if not, we use
    # whatever is available (video title, channel name, etc).
    title = info.get("track") or song_name
    artist = info.get("artist") or info.get("uploader")
    album = info.get("album")
    year = info.get("release_year") or (info.get("upload_date") or "")[:4]
    cover_url = info.get("thumbnail")

    try:
        cover_bytes = download_cover_from_url(cover_url)
        write_metadata(audio_path, title, artist, album, None, year, cover_bytes)
        print(f"OK -> {audio_path}")
    except Exception as e:
        print(f"Audio saved, but the metadata failed: {e}")

    return audio_path


def download_playlist_from_csv(csv_path, destination_folder="playlist"):
    os.makedirs(destination_folder, exist_ok=True)

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        songs = list(csv.DictReader(f))

    total = len(songs)
    print(f"Found {total} songs in the CSV.\n")

    failed = []
    partial = []
    skipped = 0

    for i, row in enumerate(songs, start=1):
        title = row["Nombre de la canción"].strip()
        artist = row["Nombre(s) del artista"].split(",")[0].strip()
        album = row["Nombre del álbum"].strip()
        track_number = row.get("Número de la canción", "").strip()
        year = (row.get("Fecha de lanzamiento del álbum") or "")[:4]
        cover_url = row.get("URL de la imagen del álbum", "").strip()

        clean_name = sanitize_filename(f"{artist} - {title}")
        final_path = os.path.join(destination_folder, f"{clean_name}.opus")

        # If it already exists and isn't empty, we consider it good and skip it.
        # This is what allows resuming after an interruption without repeating work.
        if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
            skipped += 1
            continue

        print(f"[{i}/{total}] {artist} - {title}")

        queries = [
            f"ytsearch1:{artist} - {title} lyrics",
            f"ytsearch1:{artist} - {title} audio",
        ]
        temp_path_no_ext = os.path.join(destination_folder, "temp_audio")

        try:
            audio_path, _info = _download_best_audio(
                queries, temp_path_no_ext, final_path
            )
        except Exception as e:
            print(f"  ERROR downloading audio: {e}")
            failed.append(f"{artist} - {title}")
            time.sleep(1)
            continue

        # Basic integrity check: if the file ended up at 0 bytes, it's discarded
        # instead of leaving a corrupted file in the folder.
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            print("  ERROR: the file came out empty/corrupted, discarding it.")
            if os.path.exists(audio_path):
                os.remove(audio_path)
            failed.append(f"{artist} - {title}")
            time.sleep(1)
            continue

        # The audio is already fine; if only the metadata/cover part fails,
        # we don't lose the song, we just mark it as incomplete.
        try:
            cover_bytes = download_cover_from_url(cover_url)
            write_metadata(
                audio_path, title, artist, album, track_number, year, cover_bytes
            )
            print(f"  OK -> {audio_path}")
        except Exception as e:
            print(f"  Audio saved, but the metadata failed: {e}")
            partial.append(f"{artist} - {title}")

        # Small pause between songs so we don't overload YouTube with searches.
        time.sleep(1)

    print(f"\nDone: {total - len(failed) - skipped}/{total} songs downloaded.")
    if skipped:
        print(f"{skipped} already existed from a previous run and were skipped.")
    if partial:
        print("Audio saved but with incomplete metadata:")
        for name in partial:
            print(f"  - {name}")
    if failed:
        print("Could not be downloaded:")
        for name in failed:
            print(f"  - {name}")


if __name__ == "__main__":
    print("What do you want to download?")
    print("  1) A single song")
    print("  2) A list of songs (CSV)")
    option = input("Choose an option (1/2): ").strip()

    if option == "1":
        song_name = input("Song name: ").strip()
        folder = input("Destination folder (press Enter for 'musica'): ").strip() or "musica"
        download_single_song(song_name, folder)
    elif option == "2":
        csv_path = input("Path to the CSV file: ").strip()
        folder = input("Destination folder (press Enter for 'playlist'): ").strip() or "playlist"
        download_playlist_from_csv(csv_path, folder)
    else:
        print("Invalid option. Run the program again and choose 1 or 2.")