import pyreadstat

df, meta = pyreadstat.read_xport("/Users/liangnan/Desktop/APAN 5400/Project/FDA/DR1IFF_L.xpt")
print(df.head())

#View The Data
import pandas as pd

# load the xpt file (assuming you’ve already done this)
df = pd.read_sas("your_file.xpt", format="xport")

# Check shape and columns
print("Shape:", df.shape)
print("Column Names:", df.columns.tolist())

# Check data types and missing values
print("\nData Types:")
print(df.dtypes)

print("\nMissing Values:")
print(df.isnull().sum().sort_values(ascending=False).head(10))

# Show a few unique SEQNs
print("\nUnique Respondent IDs:", df['SEQN'].nunique())

# Summary stats for a sample of numeric variables
print("\nSummary statistics:")
print(df.describe().T.head(10))
