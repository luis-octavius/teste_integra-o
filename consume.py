import os
import re
from zipfile import ZipFile

import requests
from bs4 import BeautifulSoup

from constants import *


def get_html(url):
    try:
        response = requests.get(url)

        if response.status_code == 200:
            return response.text
        else:
            print("Error: ", response.status_code)
            return None
    except Exception as e:
        print("Error: ", e)


def unzip_files(file_paths):
    for file in file_paths:
        with ZipFile(file, "r") as zObject:
            zObject.extractall(path=DOWNLOAD_DIR)


def get_local_download_paths():
    files_list = os.listdir(DOWNLOAD_DIR)
    abs_src = os.path.abspath(DOWNLOAD_DIR)

    file_paths = []
    for file in files_list:
        file_paths.append(os.path.join(abs_src, file))

    return file_paths


def download_files(files, file_names):
    for i in range(0, len(files), 1):
        download = requests.get(files[i])
        file_path = os.path.join(DOWNLOAD_DIR, file_names[i])

        if download.status_code == 200:
            with open(file_path, "wb") as file:
                file.write(download.content)
            print("File downloaded successfully")
        else:
            print("Failed to download file")


def get_files_url(html, url):
    soup = BeautifulSoup(html, "html.parser")

    table_rows = soup.find_all("a")

    files = []
    file_names = []

    for row in table_rows:
        str = row.string
        if re.search("(.zip)", str):
            file = os.path.join(url, str)
            files.append(file)
            file_names.append(str)

    return files, file_names


def get_last_year_url(html, url):
    soup = BeautifulSoup(html, "html.parser")

    table_rows = soup.find_all("a")

    year = extract_last_year(table_rows)
    print(year)

    build_url = url + year + "/"
    return build_url


def extract_last_year(table_rows):
    extracted_years = []

    for row in table_rows:
        str = row.string.replace("/", "")
        if re.search(r"\d", str):
            extracted_years.append(str)

    return extracted_years[-1:][0]


def download_last_three_files():
    page = get_html(URL)

    build_url = get_last_year_url(page, URL)

    years_page_html = get_html(build_url)

    files_url, files_name = get_files_url(years_page_html, build_url)

    download_files(files_url, files_name)

    file_paths = get_local_download_paths()
    print("File paths: ", file_paths)

    unzip_files(file_paths)
