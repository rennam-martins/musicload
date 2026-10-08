import subprocess
import os
import requests
import gdown
from concurrent.futures import ThreadPoolExecutor, as_completed
import glob
import sys

max_simultaneous_downloads = 16
max_simultaneous_conversions = 8

YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_DRIVE_ID = "1SFIIYJSomDBGKfuICx1EkFDu-SxiDIRq"

def check_and_download_executables():
    pass

def is_executable_in_path(executable_name):
    return any(
        os.access(os.path.join(path, executable_name), os.X_OK)
        for path in os.environ["PATH"].split(os.pathsep)
    )

def download_file(url, save_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(save_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
    print(f"Downloaded: {save_path}")

def download_ffmpeg_from_drive():
    url = f"https://drive.google.com/uc?id={FFMPEG_DRIVE_ID}"
    gdown.download(url, "ffmpeg.exe", quiet=False)
    print("ffmpeg.exe downloaded successfully.")

def extract_video_links():
    print("Extraindo links dos vídeos da playlist...")
    with open("playlist_links.txt", "r") as playlist_file, open("video_links.txt", "w") as video_file:
        playlists = playlist_file.readlines()
        for playlist in playlists:
            playlist = playlist.strip()
            if not playlist:
                continue
            command = f'{sys.executable} -m yt_dlp --flat-playlist -g -f m4a "{playlist}"'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.stdout:
                video_file.write(result.stdout)
            else:
                print(f"Aviso: Não foi possível extrair de {playlist}")
    print("Links extraídos com sucesso!")

def download(link):
    link = link.strip()
    if not link:
        return
    print(f"Baixando: {link}")
    os.makedirs("output", exist_ok=True)
    command = f'{sys.executable} -m yt_dlp -o "output/%(title)s.%(ext)s" -f m4a "{link}"'
    subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Download concluído: {link}")

def convert_file(m4a_file):
    print(f"Convertendo: {m4a_file}")
    mp3_file = m4a_file.replace(".m4a", ".mp3")
    command = f'ffmpeg -y -i "{m4a_file}" -vn -ar 44100 -ac 2 -b:a 128k -threads 4 "{mp3_file}"'
    subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(m4a_file)
    print(f"Conversão concluída: {mp3_file}")

print("Iniciando processo...")
check_and_download_executables()

extract_video_links()

print("Lendo links dos vídeos...")
try:
    with open("video_links.txt", "r") as file:
        links = [line.strip() for line in file.readlines() if line.strip()]
except FileNotFoundError:
    links = []

if not links:
    print("Nenhum link encontrado para baixar.")
else:
    print(f"Iniciando download de {len(links)} vídeos...")
    with ThreadPoolExecutor(max_workers=max_simultaneous_downloads) as executor:
        futures = [executor.submit(download, link) for link in links]
        for future in as_completed(futures):
            pass

    print("Iniciando conversão para MP3...")
    m4a_files = glob.glob("output/*.m4a")
    if not m4a_files:
        print("Nenhum arquivo .m4a encontrado para converter.")
    else:
        with ThreadPoolExecutor(max_workers=max_simultaneous_conversions) as executor:
            futures = [executor.submit(convert_file, m4a_file) for m4a_file in m4a_files]
            for future in as_completed(futures):
                pass
    print("Processo finalizado com sucesso!")
