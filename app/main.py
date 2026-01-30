import os

from constants import CSV_DIR, DOWNLOAD_DIR
from consume import download_last_three_files, get_data
from csv_parsing import aggregate, realize_join_ans


def main():
    os.mkdir(CSV_DIR)
    os.mkdir(DOWNLOAD_DIR)
    download_last_three_files()

    files_dir = os.listdir(CSV_DIR)
    file_name = "Relatorio_cadop.csv"

    if file_name not in files_dir:
        get_data()

    file_path = os.path.join(os.path.abspath(CSV_DIR), file_name)

    if "joined.csv" not in files_dir:
        realize_join_ans(CSV_DIR + "consolidado_despesas.csv", file_path)

    aggregate(CSV_DIR + "joined.csv")


if __name__ == "__main__":
    main()
