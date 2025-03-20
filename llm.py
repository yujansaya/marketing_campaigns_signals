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

class AffectedBusinessCategory(BaseModel):
    business_category_name: str = Field(..., alias="Business Category Name", description="Name of the business category.")
    naic_code: str = Field(..., alias="NAIC Code", description="NAIC Code for the business category.")
    suggested_niches: List[str] = Field(..., alias="Suggested Niches", description="List of niches within the category that are good targets based on impact assessment.")
    affected_commodities: List[str] = Field(..., alias="Affected Commodities", description="Specific commodities from the data that are relevant to the category.")
    potential_impact: str = Field(..., alias="Potential Impact", description="Explanation of how commodity market changes could affect the category.")

class LLMOutput(BaseModel):
    summary_of_key_findings: str = Field(...,alias='Summary of Key Findings', description="Brief overview of the major insights drawn from the scraped data.")
    list_of_affected_business_categories: List[AffectedBusinessCategory] = Field(
        ..., alias='List of Affected Business Categories',description="List of affected business categories with detailed insights."
    )


# gpt_mini = ChatGroq(model_name="deepseek-r1-distill-llama-70b", temperature=0)

gpt_mini = ChatOpenAI(model= "gpt-4o-mini",
                 # max_tokens=4096
                 )
# FOOD_SECTOR_MAPPING_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRQXdibXus54aUsemw6_jTqf_BgNXoEfDTNv-QCmyvYRUIGca_e_5M-McIr_45z9oey5pjRMvQUsoT3/pub?gid=1988978843&single=true&output=csv"
NAIC_TABLE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQazo4kuy0iLUc136vNV95JIyaYHh2asSBLs2bPJlokm38KhSjhwlUhjpE85vu_BqLbDcOQxYPA4I28/pub?gid=0&single=true&output=csv"

def get_category_list():
    df = pd.read_csv(NAIC_TABLE_URL)
    unique_categories = df[['naic_category', 'Category']].drop_duplicates().to_dict(orient='records')
    return unique_categories


def choose_relevant_niches(scraped_data, business, batch_size=300):

    # format = """
    # [{{
    #       category: chosen category from the list,
    #       naic_code: corresponding naic code from provided dataframe,
    # }}]
    # """

    prompt_template = """ 
Your task is to analyze scraped data derived from user-input keywords to identify market events and trends that could impact various business categories. 
Additionally, the user's business category is provided in {business}, which will be used to better tailor the recommendations on potential target niches where the user can approach to sell their {business} products. 
For example, if business of a user is insurance, and the news signal there were a lof cyberattacks lately, return those niches that could potentially need an insurance and likely to suffer from cyberattack.

Instructions:

Data Analysis:

Thoroughly review the provided scraped data for trends, significant events, and market shifts relevant to a wide range of industries.
Identify key terms, events, or changes that indicate broader market dynamics.
Category Filtering:

Using the provided list of business categories (each with its corresponding NAIC code), identify those categories that are likely to be impacted by the market events found in the scraped data.
Consider both:
Direct Impact: Categories that directly produce or deal with the goods or services referenced. So they would need {business} products or services.
Indirect Impact: Categories that rely on the affected market variables as critical inputs or are influenced by the overall market environment. So they would need {business} products or services.
Factor in the user's business category {business} to determine which impacted categories are most aligned with or complementary to the user’s offerings.
Impact Assessment:

For each affected category, assess the potential impact of the market trends on that sector.
Evaluate the urgency or potential benefit of introducing the user's products/services (as defined in {business}) to that category based on the insights derived from the scraped data.
Identify and suggest specific, actionable niches within each category that would be optimal targets for a marketing campaign, considering how well they align with the user’s business category.
Output Structure:
Return your answer in JSON format with the following structure:
{{
  "Summary of Key Findings": "A concise overview of the major insights derived from the scraped data.",
  "Affected Business Categories": [
    {{
      "Business Category Name": "Name of the category",
      "NAIC Code": "Corresponding NAIC code",
      "Suggested Niches": ["List of specific niches within the category. Provide such names that could be queried in company databases based on company description. So return niche names in singular, not plural form! For example if you return Premium Steakhouse, i can easily compnay description column and find names of premium steakhouses that i contact immediately to sell my services."],
      "Relevant Market Trends": ["List of key trends or terms from the data relevant to this category"],
      "Potential Impact": "Explanation of how the identified market changes could affect the category and why it might be an attractive target for the user's offerings in {business}."
    }}
  ]
}}
Focus solely on the provided list of business categories and their NAIC codes, ensuring that your final output is actionable and tailored for a targeted marketing campaign that leverages the user's business category {business}.

Scraped Data: {scrapes}
Categories List with their NAIC code: {categories}
User's Business Category: {business}
    """

    prompt = PromptTemplate(template=prompt_template, input_variables=["scrapes", "categories", "business"])
    chain = prompt | gpt_mini.with_structured_output(method="json_mode")

    all_results = []  # To store results from all batches
    categories = get_category_list()
    result = chain.invoke({
        "scrapes": scraped_data,
        "categories": categories,
        "business": business,
    })

    # # Process data in batches
    # for i in range(0, total_records, batch_size):
    #     batch = naics_df.iloc[i:i + batch_size].to_dict(orient='records')  # Get batch as list of dicts
    #     logging.info(
    #         f"Processing batch {i // batch_size + 1}/{(total_records // batch_size) + 1} with {len(batch)} records...")
    #
    #     result = chain.invoke({
    #         "niches": batch,
    #         "format": format,
    #         "sector": sector,
    #         "insurance_types": product_type
    #     })
    #
    #     try:
    #         result_list = next(iter(result.values()))
    #         logging.info(f"Batch {i // batch_size + 1} processed. Returned {len(result_list)} items.")
    #         all_results.extend(result_list)
    #     except StopIteration:
    #         all_results.extend(result)

    # Convert results to a dataframe
    # df_merged = pd.DataFrame(all_results)
    try:
        with open("llm_response.json", "w", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=4)
        logging.info(f"Data successfully written to llm_response.json")
    except Exception as e:
        logging.error(f"Failed to write data to file: {e}")
    print(result)
    return result