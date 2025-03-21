# News & Tweets Scraper – Data-Driven Market Insights

![Demo](demo.mp4)

Welcome to this project repository, where modern data engineering meets thoughtful design. This application automates the process of scraping news articles and tweets based on user-defined keywords, analyzes the gathered content, and suggests market segments that might benefit from a user's products or services. It then generates a targeted list of companies from the Crunchbase database via Snowflake. Designed with robust engineering practices in mind, this solution is ideal for running refined marketing campaigns.

---

## Project Overview

This application is designed to:

- **Scrape Social and News Media:** Using Selenium, it dynamically collects tweets and news articles based on user input.
- **Analyze Market Trends:** By examining the content, it identifies market events and trends that may impact various business niches.
- **Generate Targeted Recommendations:** It suggests business niches where the user's offerings might be needed.
- **Enrich Company Data:** It retrieves a curated list of companies from Crunchbase using a Snowflake database connection.

The project emphasizes a structured and modular approach, ensuring maintainability, scalability, and robust performance.

---

## Technical Highlights

### Advanced Web Scraping & Data Collection

The application leverages **Selenium** for scraping both tweets and news articles. For example, the `scrape_nitter` function retrieves tweets dynamically while providing live feedback through a Streamlit interface:

```python
def scrape_nitter(keyword, max_tweets=10):
    encoded_keyword = quote_plus(keyword)
    search_url = f"{NITTER_INSTANCE}/search?f=tweets&q={encoded_keyword}+usa"
    options = get_chrome_options(headless=True)
    driver = create_driver(options)
    tweets = []
    st.write(f"Scraping tweets for: **{keyword}**")
    
    try:
        driver.get(search_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.tweet-content"))
        )
        tweet_elements = driver.find_elements(By.CSS_SELECTOR, "div.tweet-content")
        tweet_display = st.empty()
        for i, tweet in enumerate(tweet_elements):
            if i >= max_tweets:
                break
            tweets.append(tweet.text)
            tweet_display.write(f"✅ {i + 1}/{max_tweets} tweets fetched...")
            time.sleep(0.5)
    
    except Exception as e:
        st.error(f"Error scraping Nitter: {e}")
        logging.error(f"Error scraping Nitter: {e}")
    finally:
        driver.quit()
    
    return tweets
```
This code not only demonstrates the use of Selenium but also shows how the user experience is enhanced with live progress updates.

---

## Concurrent Data Fetching and UI Integration

Utilizing Python’s `concurrent.futures.ThreadPoolExecutor`, the application efficiently fetches data in parallel:

```python
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    future_to_query = {executor.submit(fetch_feed, query): query for query in keyword_list}
    for future in concurrent.futures.as_completed(future_to_query):
        query = future_to_query[future]
        try:
            query_key, entries = future.result()
            feed_results[query_key] = entries
            status.update(label=f"✅ News fetched for {query}")
        except Exception as exc:
            logging.error(f"Query '{query}' generated an exception: {exc}")
            status.update(label=f"⚠️ Error fetching news for {query}")
```

This design ensures that data collection is both time-efficient and resilient.

---

## AI-Powered Analysis & Enrichment

The system employs a custom prompt pipeline to analyze scraped data and recommend actionable market segments. Here’s a snippet that demonstrates part of the AI pipeline using a structured prompt and processing with LangChain and LangGraph:

```python
def choose_relevant_niches(scraped_data, business, batch_size=300):
    prompt_template = """
    Analyze the following scraped data to identify trends and market events that impact various business categories.
    User's Business Category: {business}
    Scraped Data: {scrapes}
    Categories List with their NAIC code: {categories}

    Provide your answer in structured JSON format:
    {{
        "Summary of Key Findings": "...",
        "Affected Business Categories": [
            {{
                "Business Category Name": "...",
                "NAIC Code": "...",
                "Suggested Niches": ["..."],
                "Relevant Market Trends": ["..."],
                "Potential Impact": "..."
            }}
        ]
    }}
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["scrapes", "categories", "business"])
    chain = prompt | gpt_mini.with_structured_output(method="json_mode")
    
    categories = get_category_list()
    result = chain.invoke({
        "scrapes": scraped_data,
        "categories": categories,
        "business": business,
    })
    
    try:
        with open("llm_response.json", "w", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Failed to write data to file: {e}")
    
    return result
```
This module is pivotal in mapping market trends to actionable recommendations using clear and structured analysis.

## Leveraging LangGraph for Dynamic Company Listing
A standout feature of this project is the use of LangGraph to generate a list of company names based on a dynamic action plan. This plan is constructed by creating a graph that selects the appropriate tools (integrating with LangChain) to retrieve and structure company data. Here’s a concise example from the graph-based module:

```python
def run_graph(niche: str):
    graph = StateGraph(ReWOO)
    graph.add_node("plan", get_plan)
    graph.add_node("tool", tool_execution)
    graph.add_node("solve", solve)
    graph.add_edge("plan", "tool")
    graph.add_edge("solve", END)
    graph.add_conditional_edges("tool", _route)
    graph.add_edge(START, "plan")
    
    task = f"Return me a list of at least 30 companies in the USA within the following niche: {niche}. Return the list in JSON format: companies: [list of company names]"
    for s in app.stream({"task": task}):
        print(s)
    result = s
    companies = result['solve']['result']
    companies_list = companies["companies"]
    
    return companies_list
```

This integration of LangGraph and LangChain showcases advanced orchestration techniques common in AI engineering roles. The graph automatically generates a step-by-step action plan, selects the appropriate tools, and responds in a structured JSON format, demonstrating both automation and precision.

---

## Data Enrichment with Snowflake
To complete the pipeline, the project enriches the company data by querying the Crunchbase database using a Snowflake connection. The enrich function safely constructs SQL queries to retrieve detailed company information:

```python
def enrich(company_list):
    safe_company_list = [name.replace("'", "''") for name in company_list]
    conditions = " OR ".join(f"name ILIKE '%{company}%'" for company in safe_company_list)
    query = f"select * from crunchbase_basic_company_data.public.organization_summary where {conditions}"
    data = run_query(query)
    return data
```
This step ensures that the data provided is actionable and ready for further analysis.

---
## Getting Started
### Prerequisites
* Python 3.8+
* Selenium WebDriver
* Streamlit
* Pandas, Feedparser, and other necessary Python libraries
* Access to a Snowflake instance and Crunchbase data
---
## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/yourusername/news-tweets-scraper.git
cd news-tweets-scraper
pip install -r requirements.txt
```
## Running the Application

Launch the Streamlit application:

```bash
streamlit run main.py
```

Input your keywords and business category, and the system will display live updates as it fetches and processes the data.

---

## Conclusion
This project is a testament to thoughtful engineering and clean design. It integrates robust data pipelines, web scraping, and structured analysis to deliver actionable market insights. Key skills demonstrated include:

* Selenium-based scraping
* Asynchronous data processing with concurrent.futures
* Modern orchestration using LangGraph and LangChain
* Safe, dynamic SQL querying with Snowflake
  
This solution is built for real-world applications and offers a strong foundation for advanced marketing analytics.

For any questions or contributions, please open an issue or submit a pull request.

Happy coding!
