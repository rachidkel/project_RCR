import pandas as pd
import os

def clean_nomenclature():
    file_path = 'data/raw/nomenclature/clean_NOMENCLATURE.VERSION.AOUT_.2026-.xlsx'
    if not os.path.exists(file_path):
        # Fallback if run from different path
        file_path = 'clean_NOMENCLATURE.VERSION.AOUT_.2026-.xlsx'
        
    print(f"Chargement du fichier : {file_path}")
    xls = pd.ExcelFile(file_path)
    
    os.makedirs('../processed', exist_ok=True)
    
    # 1. Nettoyage de l'onglet principal 'Nomenclature Aout 2026'
    df_raw = pd.read_excel(file_path, sheet_name='Nomenclature Aout 2026', skiprows=15)
    df_cleaned = df_raw.loc[:, ~df_raw.columns.str.contains('^Unnamed.*Unnamed:', na=False)]
    df_cleaned = df_cleaned.dropna(axis=1, how='all')
    
    output_csv = '../processed/nomenclature_aout_2026_clean.csv'
    df_cleaned.to_csv(output_csv, index=False)
    print(f"[OK] Nomenclature active nettoyée et enregistrée : {output_csv} ({df_cleaned.shape[0]} lignes)")

    # 2. Nettoyage de l'onglet 'Non Renouvelés '
    df_nr = pd.read_excel(file_path, sheet_name='Non Renouvelés ', skiprows=11)
    df_nr = df_nr.loc[:, ~df_nr.columns.str.contains('^Unnamed.*Unnamed:', na=False)]
    df_nr = df_nr.dropna(axis=1, how='all')
    out_nr = '../processed/non_renouvelés.csv'
    df_nr.to_csv(out_nr, index=False)
    print(f"[OK] Produits non renouvelés nettoyés et enregistrés : {out_nr} ({df_nr.shape[0]} lignes)")

    # 3. Nettoyage de l'onglet 'Retraits'
    df_ret = pd.read_excel(file_path, sheet_name='Retraits', skiprows=10)
    df_ret = df_ret.loc[:, ~df_ret.columns.str.contains('^Unnamed.*Unnamed:', na=False)]
    df_ret = df_ret.dropna(axis=1, how='all')
    out_ret = '../processed/retraits.csv'
    df_ret.to_csv(out_ret, index=False)
    print(f"[OK] Produits retirés nettoyés et enregistrés : {out_ret} ({df_ret.shape[0]} lignes)")

if __name__ == '__main__':
    clean_nomenclature()