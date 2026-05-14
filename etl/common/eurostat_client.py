import eurostat
import pandas as pd

# All countries we care about: EU27 + key non-EU for comparison
COUNTRIES = [
    'AT','BE','BG','CY','CZ','DE','DK','EE','ES','FI',
    'FR','GR','HR','HU','IE','IT','LT','LU','LV','MT',
    'NL','PL','PT','RO','SE','SI','SK',
    'NO','CH','UK','IS',
    'EU27_2020','EA20'  # EU and Eurozone aggregates — useful for averages
]

COUNTRY_NAMES = {
    'AT':'Austria','BE':'Belgium','BG':'Bulgaria','CY':'Cyprus',
    'CZ':'Czechia','DE':'Germany','DK':'Denmark','EE':'Estonia',
    'ES':'Spain','FI':'Finland','FR':'France','GR':'Greece',
    'HR':'Croatia','HU':'Hungary','IE':'Ireland','IT':'Italy',
    'LT':'Lithuania','LU':'Luxembourg','LV':'Latvia','MT':'Malta',
    'NL':'Netherlands','PL':'Poland','PT':'Portugal','RO':'Romania',
    'SE':'Sweden','SI':'Slovenia','SK':'Slovakia','NO':'Norway',
    'CH':'Switzerland','UK':'United Kingdom','IS':'Iceland',
    'EU27_2020':'European Union (27)','EA20':'Euro Area (20)',
}

def fetch_dataset(dataset_code: str) -> pd.DataFrame:
    """
    Fetch a full Eurostat dataset including data quality flags.
    Raises ValueError if the dataset returns empty.
    """
    print(f"[eurostat_client] Fetching {dataset_code}...")
    df = eurostat.get_data_df(dataset_code, flags=True)
    if df is None or df.empty:
        raise ValueError(f"Empty response for dataset: {dataset_code}")
    print(f"[eurostat_client] {dataset_code}: {df.shape[0]} rows, {df.shape[1]} columns")
    return df