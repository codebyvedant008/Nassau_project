import pandas as pd

try:
    df = pd.read_excel('data/Nassau Candy Distributor.xlsx')
    df.to_csv('data/Nassau Candy Distributor.csv', index=False)
    print("Successfully converted Excel to CSV.")
except Exception as e:
    print("Error converting file:", e)
