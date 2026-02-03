import os
import zipfile as ZipFile

import pandas as pd

from constants import CSV_DIR


def parse_csv(csv_files_path, output_file=CSV_DIR + "consolidado_despesas.csv"):
    dfs = []

    for file in csv_files_path:
        filename = os.path.basename(file)
        trimester = None
        year = 2025

        if "T1" in filename or "1T" in filename:
            trimester = 1
        if "T2" in filename or "2T" in filename:
            trimester = 2
        if "T3" in filename or "3T" in filename:
            trimester = 3
        if "T4" in filename or "4T" in filename:
            trimester = 4

        df = pd.read_csv(file, sep=";", encoding="utf-8")

        if "VL_SALDO_INICIAL" in df.columns:
            df["VL_SALDO_INICIAL"] = pd.to_numeric(
                df["VL_SALDO_INICIAL"]
                .astype(str)
                .str.replace(".", "")
                .str.replace(",", "."),
                errors="coerce",
            )
        if "VL_SALDO_FINAL" in df.columns:
            df["VL_SALDO_FINAL"] = pd.to_numeric(
                df["VL_SALDO_FINAL"]
                .astype(str)
                .str.replace(".", "")
                .str.replace(",", "."),
                errors="coerce",
            )

        df["VALOR_DESPESAS"] = (
            df["VL_SALDO_FINAL"] / 1_000_000
        )  # Scale down by 1 million

        data = {
            "REG_ANS": df["REG_ANS"] if "REG_ANS" in df.columns else "",
            "CD_CONTA_CONTABIL": df["CD_CONTA_CONTABIL"]
            if "CD_CONTA_CONTABIL" in df.columns
            else "",
            "ANO": year,
            "TRIMESTRE": trimester,
            "VALOR_DESPESAS": df["VALOR_DESPESAS"],
        }

        consolidated_df = pd.DataFrame(data)
        dfs.append(consolidated_df)

    df_final = pd.concat(dfs, ignore_index=True)

    df_final.to_csv(output_file, sep=";", index=False, encoding="utf-8")

    zip_file(output_file, "consolidado_despesas.zip")


def zip_file(file, file_name):
    with ZipFile.ZipFile(file_name, "w") as zipf:
        zipf.write(file)
        print(f"File {file} zipped successfully as {file_name}")


def realize_join_ans(
    consolidated_path, cadastro_path, output_path=CSV_DIR + "joined.csv"
):
    df_expenses = pd.read_csv(consolidated_path, sep=";")

    df_cadastro = pd.read_csv(cadastro_path, sep=";")

    df_cadastro = df_cadastro.rename(columns={"REGISTRO_OPERADORA": "REG_ANS"})

    df_cadastro_redux = df_cadastro[
        ["REG_ANS", "CNPJ", "Razao_Social", "Modalidade", "UF"]
    ]

    # Check for duplicate REG_ANS in df_cadastro_redux before merging
    if df_cadastro_redux["REG_ANS"].duplicated().any():
        num_duplicates = df_cadastro_redux["REG_ANS"].duplicated().sum()
        print(
            f"Warning: Found {num_duplicates} duplicate REG_ANS entries in df_cadastro_redux."
        )
        print("This might lead to inflated values due to row duplication during merge.")
        # Optionally, remove duplicates if desired, e.g., df_cadastro_redux = df_cadastro_redux.drop_duplicates(subset=['REG_ANS'])

    df_result = pd.merge(df_expenses, df_cadastro_redux, on="REG_ANS", how="left")

    df_result.to_csv(output_path, sep=";", index=False, encoding="utf-8")

    print("\nJoin successful")
    print(f"Expenses registry: {len(df_expenses)}")
    print(f"Result registry: {len(df_result)}")
    print(f"Found matches: {df_result['CNPJ'].notna().sum()}")

    return df_result


def aggregate(csv_file):
    df = pd.read_csv(csv_file, sep=";")

    # Explicitly ensure VALOR_DESPESAS is numeric
    df["VALOR_DESPESAS"] = pd.to_numeric(df["VALOR_DESPESAS"], errors="coerce")

    # df["VALOR_DESPESAS"] = pd.to_numeric(
    #     df["VALOR_DESPESAS"].astype(str).str.replace(".", "").str.replace(",", "."),
    #     errors="coerce",
    # )

    # Convert CD_CONTA_CONTABIL to string to allow length calculation
    df["CD_CONTA_CONTABIL"] = df["CD_CONTA_CONTABIL"].astype(str)

    # Determine the maximum length of CD_CONTA_CONTABIL
    max_len = df["CD_CONTA_CONTABIL"].str.len().max()

    # Filter to keep only the most granular accounts
    df_filtered = df[df["CD_CONTA_CONTABIL"].str.len() == max_len].copy()

    print("\nAgrupando por RazaoSocial e UF...")
    groups = df_filtered.groupby(["Razao_Social", "UF"])

    print("Calculando total de despesas...")
    total_operator = groups["VALOR_DESPESAS"].sum().reset_index()
    total_operator = total_operator.rename(columns={"VALOR_DESPESAS": "TOTAL_DESPESAS"})

    print("Calculando média por trimestre...")

    total_trimester = (
        df_filtered.groupby(["Razao_Social", "UF", "TRIMESTRE"])["VALOR_DESPESAS"]
        .sum()
        .reset_index()
    )

    media_trimester = (
        total_trimester.groupby(["Razao_Social", "UF"])["VALOR_DESPESAS"]
        .mean()
        .reset_index()
    )

    media_trimester = media_trimester.rename(
        columns={"VALOR_DESPESAS": "MEDIA_TRIMESTRAL"}
    )

    print("Calculando desvio padrão...")
    desvio_padrao = groups["VALOR_DESPESAS"].std().reset_index()
    desvio_padrao = desvio_padrao.rename(columns={"VALOR_DESPESAS": "DESVIO_PADRAO"})

    print("Consolidando resultados...")
    result = pd.merge(total_operator, media_trimester, on=["Razao_Social", "UF"])
    result = pd.merge(result, desvio_padrao, on=["Razao_Social", "UF"])

    # Round monetary values to 2 decimal places for presentation
    result["TOTAL_DESPESAS"] = result["TOTAL_DESPESAS"].round(2)
    result["MEDIA_TRIMESTRAL"] = result["MEDIA_TRIMESTRAL"].round(2)
    result["DESVIO_PADRAO"] = result["DESVIO_PADRAO"].round(2)

    result["COEFICIENTE_VARIACAO"] = (
        result["DESVIO_PADRAO"] / result["MEDIA_TRIMESTRAL"]
    ) * 100
    result["COEFICIENTE_VARIACAO"] = result["COEFICIENTE_VARIACAO"].round(2)

    result = result.sort_values("TOTAL_DESPESAS", ascending=False)

    result.to_csv(
        CSV_DIR + "despesas_agregadas.csv", sep=";", index=False, encoding="utf-8"
    )

    print("\nResultados salvos em 'despesas_agregadas.csv'")
    print(f"Total de operadoras/UF analisadas: {len(result)}")
    print("Top 5 operadoras por despesas:")
    print(result.head(5).to_string())

    return result
