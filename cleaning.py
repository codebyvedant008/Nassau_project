import pandas as pd
import numpy as np

def clean_data(input_path="data/Nassau Candy Distributor.csv", output_path="data/cleaned_data.csv"):
    print("Loading data...")
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"Error: {input_path} not found. Please ensure the CSV file is in the data folder.")
        return

    # 2. Remove duplicates
    initial_rows = len(df)
    df = df.drop_duplicates()
    print(f"Removed {initial_rows - len(df)} duplicate rows.")

    # 3. Convert Order Date and Ship Date to datetime
    if 'Order Date' in df.columns:
        df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    if 'Ship Date' in df.columns:
        df['Ship Date'] = pd.to_datetime(df['Ship Date'], errors='coerce')

    # 4. Handle missing values
    critical_cols = ['Sales', 'Units', 'Gross Profit']
    existing_critical = [c for c in critical_cols if c in df.columns]
    df = df.dropna(subset=existing_critical)
    
    # Fill remaining NaNs
    text_cols = ['Division', 'Region', 'City', 'State/Province', 'Product Name']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('Unknown')

    # 5. Remove invalid rows
    if 'Sales' in df.columns and 'Units' in df.columns:
        df = df[(df['Sales'] > 0) & (df['Units'] > 0)]

    # 6. Standardize text columns
    for col in ['Division', 'Region', 'City', 'State/Province']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # 7. Create Compliance KPIs
    if 'Sales' in df.columns and 'Gross Profit' in df.columns:
        df['Cost'] = df['Sales'] - df['Gross Profit']
        df['Gross Margin %'] = (df['Gross Profit'] / df['Sales']) * 100
        
        total_sales = df['Sales'].sum()
        df['Revenue Contribution %'] = (df['Sales'] / total_sales) * 100 if total_sales else 0
        
        total_profit = df['Gross Profit'].sum()
        df['Profit Contribution %'] = (df['Gross Profit'] / total_profit) * 100 if total_profit else 0

    if 'Gross Profit' in df.columns and 'Units' in df.columns:
        df['Profit per Unit'] = df['Gross Profit'] / df['Units']

    if 'Order Date' in df.columns and 'Ship Date' in df.columns:
        df['Shipping Days'] = (df['Ship Date'] - df['Order Date']).dt.days

    # Remove infinities
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['Gross Margin %', 'Profit per Unit'])

    # 8. Save
    df.to_csv(output_path, index=False)
    print(f"Data cleaned successfully. Saved to {output_path} with {len(df)} rows.")

if __name__ == "__main__":
    clean_data()
