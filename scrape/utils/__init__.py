import pickle
import jsonlines
import json

local_batch_directory = 'scrape/assets/batch_summary.jsonl'

def create_json_batch_file(texts, system_message, response_format, id_var):
    json_list = []
    for text in texts:

        json_list.append({"custom_id": text[id_var], 
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {"model": "gpt-4o-mini", 
                "messages": [{"role": "system", 
                                "content": system_message},
                                {"role": "user", 
                                "content": text['text']}],
                                "max_tokens": 3000,
                                "response_format": response_format
        }})

    with jsonlines.open(local_batch_directory, 'w') as writer:
        writer.write_all(json_list)


def upload_batch_to_gpt(gpt_client):
    batch_input_file = gpt_client.files.create(
    file=open(local_batch_directory, "rb"),
    purpose="batch"
    )

    batch_file_id = batch_input_file.id

    batch_meta = gpt_client.batches.create(
        input_file_id=batch_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={
        "description": "Gaming market trends batch job"
        }
    )
    return batch_meta.id

def extract_summaries(batch_id, gpt_client, status = 'init'):

    batch_meta = gpt_client.batches.retrieve(batch_id)
    file_response = gpt_client.files.content(batch_meta.output_file_id)
    text_response = file_response.read().decode('utf-8')
    text_dict = [json.loads(obj) for obj in text_response.splitlines()]

    data = []
    for i in text_dict:        
        id = i['custom_id']
        output = eval(i['response']['body']['choices'][0]['message']['content'])
        summary = output['Summary']
        data.append({"id": id, "summary": summary})

    # save to local
    with open(f"scrape/assets/{status}_summaries.pkl", "wb") as f:
        pickle.dump(data, f)

    return data
