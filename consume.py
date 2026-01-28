import re

import requests
from bs4 import BeautifulSoup


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
        if re.search("\d", str):
            extracted_years.append(str)

    return extracted_years[-1:][0]
