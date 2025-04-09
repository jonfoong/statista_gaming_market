from bs4 import BeautifulSoup
import requests
import os
from openai import OpenAI

from scrape.gpt_prompts import init_summary_system_message, init_summary_response_format, fin_summary_system_message, fin_summary_response_format
from scrape.utils import create_json_batch_file, upload_batch_to_gpt, extract_summaries

# openai key

os.environ["OPENAI_API_KEY"] = open("token/gpt_api_token.txt", 'r').readlines()[0]

# initialize client

gpt_client = OpenAI()

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/111.0.0.0 Safari/537.36"
    )
}

# get search links
# get first 3 pages

link_list = []

for page_no in [0, 10, 20]:

    url = f"https://www.google.com/search?q=gaming+market+trends&lr=&sca_esv=7c7b298578be5db7&tbs=qdr:m&tbm=nws&sxsrf=AHTn8zrD1yya3K5-ODcuU9EpxiOQviJXbg:1744190457237&ei=-Tv2Z9OiDqWHptQPppqf0Qc&start={page_no}&sa=N&ved=2ahUKEwiTg__kz8qMAxWlg4kEHSbNJ3o4ChDy0wN6BAgFEAQ&biw=1280&bih=665&dpr=1.5"

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    all_links = soup.find_all("a", class_ = "WlydOe")

    for i in all_links:
        link = i["href"]
        link_list.append(link)

# get unique links
link_list = set(link_list)

# now get texts

texts = []

for i in link_list:
    response = requests.get(i, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    all_p = soup.find_all("p")

    all_text = ' '.join([p.get_text() for p in all_p])
    text_dict = {"link": i, "text": all_text}
    texts.append(text_dict)

# create json batch file for summary
create_json_batch_file(texts, init_summary_system_message, init_summary_response_format, id_var = 'link')

# upload job to gpt
batch_id = upload_batch_to_gpt(gpt_client)

# extract summaries
summaries = extract_summaries(batch_id, gpt_client, status = 'init')

# now resummarize into shorter points
all_summaries = ' '.join([i['summary'] for i in summaries]).replace('\n', ' ')

# create new batch file
create_json_batch_file([{'id': '1', "text": all_summaries}], fin_summary_system_message, fin_summary_response_format, id_var = 'id')

# upload new batch to gpt
batch_id = upload_batch_to_gpt(gpt_client)

# extract final summary
final_summary = extract_summaries(batch_id, gpt_client, status = 'fin')