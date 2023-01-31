import bs4
import undetected_chromedriver.v2 as uc
import requests
import os
import threading
import argparse
import subprocess
import sys

class DevNull:
    def write(self, msg):
        pass

sys.stderr = DevNull()


class CdaFolderScraper:
    def __init__(self, url):
        self.url = url
        self.video_urls = []
        self.folder_name = ""

    def get_data(self, url):
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        driver = uc.Chrome(options=options)
        driver.get(url)
        soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
        with open('test.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        driver.quit()

        # get data
        video_urls = []
        videos = soup.find_all('a', class_='link-title-visit')

        for video in videos:
            video_url = "https://www.cda.pl" + video['href']
            video_urls.append(video_url)

        folder_name = soup.select("span.folder-one-line:nth-child(2) > a:nth-child(2)")[0].text

        self.video_urls = video_urls
        self.folder_name = folder_name

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def execute_command(command):
    subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Download videos from cda folder')
    parser.add_argument('--url', type=str, help='url of the folder')
    args = parser.parse_args()

    url = args.url
    videos = CdaFolderScraper(url)
    videos.get_data(url)
    
    r = requests.get("https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe")
    if os.path.exists("yt-dlp.exe"):
        with open("yt-dlp.exe", "wb") as f:
            f.write(r.content)

    leading_zeros = int(len(videos.video_urls) / 10) + 1
    if not os.path.exists(videos.folder_name):
        os.mkdir(videos.folder_name)

    commands = []
    for i, video in enumerate(videos.video_urls):
        i += 1
        commands.append(f'yt-dlp.exe -f bestvideo+bestaudio/best {video} -o "{videos.folder_name}/{i:0{leading_zeros}d}.mp4"')

    threads = []
    max_threads = 8
    finished = 0
    for i in range(0, len(commands), max_threads):
        for command in commands[i:i+max_threads]:
            t = threading.Thread(target=execute_command, args=(command,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
            if finished < len(commands):
                finished += 1
                print(f"{bcolors.OKGREEN}Downloaded {finished}/{len(commands)}{bcolors.ENDC}")

    if os.path.exists("yt-dlp.exe"):
        os.remove("yt-dlp.exe")

    print(f"{bcolors.WARNING}Done{bcolors.ENDC}")

