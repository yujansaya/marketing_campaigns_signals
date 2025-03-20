from langchain_openai import ChatOpenAI
from environs import Env
from langchain_core.prompts import PromptTemplate
import pandas as pd
import logging
import json
from langchain_groq import ChatGroq
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List

from pygments.lexers import business

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
env = Env()
env.read_env(".env")

gpt_mini = ChatOpenAI(model= "gpt-4o-mini",
                 # max_tokens=4096
                 )

def clean_company_list(company_df, niche, batch_size=300):

    # format = """
    # [{{
    #       UUID: corresponding UUID from teh provided dataframe,
    #       SHORT_DESCRIPTION: chosen description from the list,
    # }}]
    # """

    prompt_template = """ 
You are provided with a dataframe with companies description and their corresponding unique ids.
Your task is to analyse which descriptions match the {niche}, i.e. this company belongs to {niche} business or has at least some relation to it.
Include in your answer only those companies that belong to the {niche} business or has some relation to it even not that obvious.
The answer must be the following json format:
    [{{
          UUID: corresponding UUID from teh provided dataframe,
          SHORT_DESCRIPTION: chosen description from the list,
    }}]
Companies description dataframe: {companies_dataframe}
    """

    prompt = PromptTemplate(template=prompt_template, input_variables=["companies_dataframe", "niche"])
    chain = prompt | gpt_mini.with_structured_output(method="json_mode")

    result = chain.invoke({
        "companies_dataframe": company_df[["UUID", "SHORT_DESCRIPTION"]].to_dict(orient="records"),
        "niche": niche,
    })
    try:
        with open("llm_df_response.json", "w", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=4)
        logging.info(f"Data successfully written to llm_df_response.json")
    except Exception as e:
        logging.error(f"Failed to write data to file: {e}")
    print(result)
    # Convert the list of dictionaries to a set of UUIDs
    uuid_set = set(item['UUID'] for item in next(iter(result.values())))
    # Filter the DataFrame based on UUIDs
    filtered_df = company_df[company_df['UUID'].isin(uuid_set)].reset_index(drop=True)
    return filtered_df