from consume import get_html, get_last_year_url


def main():
    url = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"
    page = get_html(url)
    build_url = get_last_year_url(page, url)
    print(build_url)


if __name__ == "__main__":
    main()
