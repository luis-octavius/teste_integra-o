import os
import re
from zipfile import ZipFile

import requests
from bs4 import BeautifulSoup

from constants import *
from csv_parsing import parse_csv


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
            print(f"{file} extracted successfully!")


def get_local_zip_files():
    files_list = os.listdir(DOWNLOAD_DIR)
    abs_src = os.path.abspath(DOWNLOAD_DIR)

    file_paths = []
    for file in files_list:
        if file.endswith(".zip"):
            file_paths.append(os.path.join(abs_src, file))

    return file_paths


def get_local_csv_files():
    files_list = os.listdir(DOWNLOAD_DIR)
    abs_src = os.path.abspath(DOWNLOAD_DIR)

    file_paths = []
    for file in files_list:
        if file.endswith(".csv"):
            file_paths.append(os.path.join(abs_src, file))

    return file_paths


def download_files(files, file_names):
    for i in range(0, len(files), 1):
        download = requests.get(files[i])
        file_path = os.path.join(DOWNLOAD_DIR, file_names[i])

        if download.status_code == 200:
            with open(file_path, "wb") as file:
                file.write(download.content)
            print(f"File downloaded successfully at {os.path.abspath(file_path)}")
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

    zip_file_paths = get_local_zip_files()
    if len(zip_file_paths) == 0:
        files_url, files_name = get_files_url(years_page_html, build_url)
        download_files(files_url, files_name)

    csv_file_paths = get_local_csv_files()
    print("CSV FILES: ", csv_file_paths)

    if len(csv_file_paths) == 0:
        zip_file_paths = get_local_zip_files()
        unzip_files(zip_file_paths)
        csv_file_paths = get_local_csv_files()

    parse_csv(csv_file_paths)


def get_data():
    filename = os.path.basename(RELATORIO_URL)
    file_path = os.path.join(CSV_DIR, filename)

    download = requests.get(RELATORIO_URL)

    if download.status_code == 200:
        with open(file_path, "wb") as file:
            file.write(download.content)
        print(f"File downloaded successfully at {os.path.abspath(file_path)}")
    else:
        print("Failed to download file")

    return file_path
