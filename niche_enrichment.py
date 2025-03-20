import streamlit as st
import pandas as pd
import snowflake.connector


# Connect to Snowflake
@st.cache_resource
def init_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        # warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
    )


# Run a query on the free Snowflake database
@st.cache_data
def run_query(query):
    conn = init_connection()
    with conn.cursor() as cur:
        cur.execute(query)
        df = pd.DataFrame(cur.fetchall(), columns=[col[0] for col in conn.cursor().execute(query).description])
        return df

def enrich(company_list):
    # Escape single quotes in company names for SQL safety
    safe_company_list = [name.replace("'", "''") for name in company_list]
    # Create a properly formatted SQL string
    conditions = " OR ".join(f"name ILIKE '{company}%'" for company in safe_company_list)
    query = f"select * from crunchbase_basic_company_data.public.organization_summary where {conditions}"
             #f"and country_code like '%USA%'")
    data = run_query(query)
    return data

