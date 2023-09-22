
import urllib.request
import fitz
import re
import numpy as np
import tensorflow_hub as hub
import openai
import gradio as gr
import os
from tqdm.auto import tqdm
from sklearn.neighbors import NearestNeighbors


def download_pdf(url, output_path):
    '''
    download file from URL and save it to `output_path`
    '''
    urllib.request.urlretrieve(url, output_path)


def preprocess(text):
    '''
    preprocess chunks
    1. Replace new line character with whitespace.
    2. Replace redundant whitespace with a single whitespace
    '''
    text = text.replace('\n', ' ')
    text = re.sub('\s+', ' ', text)
    return text

def pdf_to_text(path, start_page=1, end_page=None):
    '''
    convert PDF document to text
    '''
    doc = fitz.open(path)
    total_pages = doc.page_count

    if end_page is None:
        end_page = total_pages

    text_list = []

    for i in tqdm(range(start_page-1, end_page)):
        text = doc.load_page(i).get_text("text")
        text = preprocess(text)
        text_list.append(text)

    doc.close()
    return text_list

def text_to_chunks(texts, word_length=150, start_page=1):
    '''
    convert list of texts to smaller chunks of length `word_length`
    '''
    text_toks = [t.split(' ') for t in texts]
    page_nums = []
    chunks = []
    
    for idx, words in enumerate(text_toks):
        for i in range(0, len(words), word_length):
            chunk = words[i:i+word_length]
            if (i+word_length) > len(words) and (len(chunk) < word_length) and (
                len(text_toks) != (idx+1)):
                text_toks[idx+1] = chunk + text_toks[idx+1]
                continue
            chunk = ' '.join(chunk).strip()
            chunk = f'[{idx+start_page}]' + ' ' + '"' + chunk + '"'
            chunks.append(chunk)
    return chunks

class SemanticSearch:
    
    def __init__(self):
        self.use = hub.load('https://tfhub.dev/google/universal-sentence-encoder/4')
        self.fitted = False
    
    def fit(self, data, batch=1000, n_neighbors=5):
        self.data = data
        self.embeddings = self.get_text_embedding(data, batch=batch)
        n_neighbors = min(n_neighbors, len(self.embeddings))
        self.nn = NearestNeighbors(n_neighbors=n_neighbors)
        self.nn.fit(self.embeddings)
        self.fitted = True
    
    
    def __call__(self, text, return_data=True):
        inp_emb = self.use([text])
        neighbors = self.nn.kneighbors(inp_emb, return_distance=False)[0]
        
        if return_data:
            return [self.data[i] for i in neighbors]
        else:
            return neighbors

    
    def get_text_embedding(self, texts, batch=1000):
        embeddings = []
        for i in tqdm(range(0, len(texts), batch)):
            text_batch = texts[i:(i+batch)]
            emb_batch = self.use(text_batch)
            embeddings.append(emb_batch)
        embeddings = np.vstack(embeddings)
        return embeddings


# openai.api_type = "azure"

# openai.api_base = "OPENAI_API_ENDPOINT"

# openai.api_version = "2022-12-01"

# openai.api_key = ""    

print(openai.api_key)


recommender = SemanticSearch()


def load_recommender(path, start_page=1):
    print(path)
    global recommender
    texts = []
    for i in range(len(path)):
        texts.extend(pdf_to_text(path[i], start_page=start_page))
    # print("texts",texts[0])
    # print("texts",texts[1])
    # print("texts",texts)
    chunks = text_to_chunks(texts, start_page=start_page)
    recommender.fit(chunks)
    return 'Corpus Loaded.'


def generate_text(prompt, engine="text-davinci-003"):
    completions = openai.Completion.create(
        engine=engine,
        prompt=prompt,
        max_tokens=512,
        n=1,
        stop=None,
        temperature=0.7,
    )
    message = completions.choices[0].text
    return message

def generate_answer(question):
    # print("question",question)
    # print("question type",type(question))
    # g_answer = Sentiment(question)
    # print("--------",g_answer)
    topn_chunks = recommender(question)
    prompt = ""
    prompt += 'search results:\n\n'
    for c in topn_chunks:
        prompt += c + '\n\n'
        
    prompt += """You are a bot that reads Email Message, and return the most appropriate catergories.
    Every email must be assigned a Primary Category.
    
    Primary Categories: Package Tracking, Customs & Clearance, Billing, Pickup, Rating & Transit Times, Account & Sales Support, POD proof of delivery, Claims, Supplies, IT Support, Other

    Do NOT use any other categories other than the ones that are listed.
    An email can have only one primary category.
    If the text does not relate to any category, simply return 'Unknown Category'. 
    Return the output in the format "Primary Category: [INSERT PRIMARY CATEGORY]"
    """
        
    prompt += f"Query: {question}\n\n"
    answer = generate_text(prompt)
    # print("prompt is", prompt)
    print("++++++++++++++++++",answer)
    return answer

def Sentiment(question):
    prompt = f"Analysing the emotion of he following text: '{question}' Give answer without fullstop.The emotion is:"
    response = openai.Completion.create(
    engine = "text-davinci-003",
    prompt = prompt,
    max_tokens = 50,
    api_key = openai.api_key)
    generated_response = response.choices[0].text.strip()
    # print(generated_response)
    return generated_response

def Summarized(question):
    prompt = f"Summarizing the following text into shorter and meaniningful text: '{question}'.The summary is:"
    response = openai.Completion.create(
    engine = "text-davinci-003",
    prompt = prompt,
    max_tokens = 50,
    api_key = openai.api_key)
    summarized_response = response.choices[0].text.strip()
    # print(generated_response)
    return summarized_response

def quick_resp(question):
    prompt = f"Give quick response  '{question}'.The summary is:"
    response = openai.Completion.create(
    engine = "text-davinci-003",
    prompt = prompt,
    max_tokens = 50,
    api_key = openai.api_key)
    summarized_response = response.choices[0].text.strip()
    # print(generated_response)
    return summarized_response

def quick_resp(question):
    prompt = f"""You are a bot that reads messages {question}, read the tone and come up with a meaninful response email with greeting and regards part.
    Response length should be 70-80 words long.
    Add a Thank you part in the end of the email.
    Return email without newline
    Makes Sure to be polite and generous.
    """
    
    response = openai.Completion.create(
    engine = "text-davinci-003",
    prompt = prompt,
    max_tokens = 150,
    api_key = openai.api_key)
    generated_response = response.choices[0].text.strip()
    return generated_response

def priority(question):
    prompt = f"""You are a bot that reads messages {question}, read the tone and based on the urgency on the message, come up with a priority of the query.
    Specify the priority as either low, medium or high
    Return the priority in one word only without fullstop
    """
    
    response = openai.Completion.create(
    engine = "text-davinci-003",
    prompt = prompt,
    max_tokens = 150,
    api_key = openai.api_key)
    generated_priority = response.choices[0].text.strip()
#     print(generated_response)
    return generated_priority


######Creating UI############


def Email_Category(url, file, question):
    if url.strip() == '' and file == None:
        return '[ERROR]: Both URL and PDF is empty. Provide atleast one.'
    
    if url.strip() != '' and file != None:
        return '[ERROR]: Both URL and PDF is provided. Please provide only one (eiter URL or PDF).'

    if url.strip() != '':
        glob_url = url
        download_pdf(glob_url, 'corpus.pdf')
        load_recommender('corpus.pdf')

    else:
        #old_file_name = file.name
        print(">>>>>>>>>>>>>>", file)
        # print(file[0].name)
        # print(file[1].name)
        # file = [file]
        # print("file", file)
        old_file_name = []
        for item in range(len(file)):
            print("<<<<<<<<<<<<<<<<<<<",file[item].name)
            file_name = file[item].name
            # file_name = file_name[:-12] + file_name[-4:]
            print("---------------------------",file_name)
            old_file_name.append(file_name)
            #os.rename(old_file_name, file_name)
        load_recommender(old_file_name)

    if question.strip() == '':
                return '[ERROR]: Query field is empty'
    
    return generate_answer(question)

def Summarized_Query(url, file, question):
    if url.strip() == '' and file == None:
        return '[ERROR]: Both URL and PDF is empty. Provide atleast one.'
    
    if url.strip() != '' and file != None:
        return '[ERROR]: Both URL and PDF is provided. Please provide only one (eiter URL or PDF).'

    if url.strip() != '':
        glob_url = url
        download_pdf(glob_url, 'corpus.pdf')
        load_recommender('corpus.pdf')

    else:
        #old_file_name = file.name
        print(">>>>>>>>>>>>>>", file)
        # print(file[0].name)
        # print(file[1].name)
        # file = [file]
        # print("file", file)
        old_file_name = []
        for item in range(len(file)):
            print("<<<<<<<<<<<<<<<<<<<",file[item].name)
            file_name = file[item].name
            # file_name = file_name[:-12] + file_name[-4:]
            print("---------------------------",file_name)
            old_file_name.append(file_name)
            #os.rename(old_file_name, file_name)
        load_recommender(old_file_name)

    if question.strip() == '':
                return '[ERROR]: Query field is empty'
    
    return Summarized(question)

def Sentiment_analysis(url, file, question):
    if url.strip() == '' and file == None:
        return '[ERROR]: Both URL and PDF is empty. Provide atleast one.'
    
    if url.strip() != '' and file != None:
        return '[ERROR]: Both URL and PDF is provided. Please provide only one (eiter URL or PDF).'

    if url.strip() != '':
        glob_url = url
        download_pdf(glob_url, 'corpus.pdf')
        load_recommender('corpus.pdf')

    else:
        #old_file_name = file.name
        print(">>>>>>>>>>>>>>", file)
        # print(file[0].name)
        # print(file[1].name)
        # file = [file]
        # print("file", file)
        old_file_name = []
        for item in range(len(file)):
            print("<<<<<<<<<<<<<<<<<<<",file[item].name)
            file_name = file[item].name
            # file_name = file_name[:-12] + file_name[-4:]
            print("---------------------------",file_name)
            old_file_name.append(file_name)
            #os.rename(old_file_name, file_name)
        load_recommender(old_file_name)

    if question.strip() == '':
                return '[ERROR]: Query field is empty'
    
    return Sentiment(question)

def quick_response(url, file, question):
    if url.strip() == '' and file == None:
        return '[ERROR]: Both URL and PDF is empty. Provide atleast one.'
    
    if url.strip() != '' and file != None:
        return '[ERROR]: Both URL and PDF is provided. Please provide only one (eiter URL or PDF).'

    if url.strip() != '':
        glob_url = url
        download_pdf(glob_url, 'corpus.pdf')
        load_recommender('corpus.pdf')

    else:
        #old_file_name = file.name
        print(">>>>>>>>>>>>>>", file)
        # print(file[0].name)
        # print(file[1].name)
        # file = [file]
        # print("file", file)
        old_file_name = []
        for item in range(len(file)):
            print("<<<<<<<<<<<<<<<<<<<",file[item].name)
            file_name = file[item].name
            # file_name = file_name[:-12] + file_name[-4:]
            print("---------------------------",file_name)
            old_file_name.append(file_name)
            #os.rename(old_file_name, file_name)
        load_recommender(old_file_name)

    if question.strip() == '':
                return '[ERROR]: Query field is empty'
    
    return quick_resp(question)

def priority_check(url, file, question):
    if url.strip() == '' and file == None:
        return '[ERROR]: Both URL and PDF is empty. Provide atleast one.'
    
    if url.strip() != '' and file != None:
        return '[ERROR]: Both URL and PDF is provided. Please provide only one (eiter URL or PDF).'

    if url.strip() != '':
        glob_url = url
        download_pdf(glob_url, 'corpus.pdf')
        load_recommender('corpus.pdf')

    else:
        #old_file_name = file.name
        print(">>>>>>>>>>>>>>", file)
        # print(file[0].name)
        # print(file[1].name)
        # file = [file]
        # print("file", file)
        old_file_name = []
        for item in range(len(file)):
            print("<<<<<<<<<<<<<<<<<<<",file[item].name)
            file_name = file[item].name
            # file_name = file_name[:-12] + file_name[-4:]
            print("---------------------------",file_name)
            old_file_name.append(file_name)
            #os.rename(old_file_name, file_name)
        load_recommender(old_file_name)

    if question.strip() == '':
                return '[ERROR]: Query field is empty'
    
    return priority(question)

title = 'GPT UseCase for Email Category'
description = ""

css = """
#warning1 {background-color: #D4E7E6}
#warning2 {background-color: white}
.feedback {font-size: 12px !important}
.feedback textarea {font-size: 12px !important}
"""

with gr.Blocks(css=css) as demo:

    gr.Markdown(f'<center><h1>{title}</h1></center>',elem_classes="feedback")
    gr.Markdown(description)
    
    with gr.Row():
        
        with gr.Group():
            url = gr.Textbox(label='URL',elem_id="warning1",elem_classes="feedback")
            gr.Markdown("<center><h6>or<h6></center>",elem_id="warning2")
            file = gr.Files(label='PDF', file_types=['.pdf'],file_count="multiple",elem_id="warning1",elem_classes="feedback")
            question = gr.Textbox(label='Query',elem_id="warning1",elem_classes="feedback")
            # btn = gr.Button(value='Submit',scale=1,elem_classes="feedback",elem_id="warning1")
            # btn.style(full_width=False)

        with gr.Group():
            answer = gr.Textbox(label='Category',elem_id="warning1",elem_classes="feedback")
            gr.Markdown("<center><h6><h6></center>",elem_id="warning2")
            Summary = gr.Textbox(label='Query Summary',elem_id="warning1",elem_classes="feedback")
            gr.Markdown("<center><h6> <h6></center>",elem_id="warning2")
            Sent = gr.Textbox(label='Emotion',elem_id="warning1",elem_classes="feedback")
            gr.Markdown("<center><h6>  <h6></center>",elem_id="warning2")
        # with gr.Group():
            Priority = gr.Textbox(label='Priority',elem_id="warning1",elem_classes="feedback")
            gr.Markdown("<center><h6> <h6></center>",elem_id="warning2")
            Quick_Response = gr.Textbox(label='Quick Response',elem_id="warning1",elem_classes="feedback")
           
        
        # btn.click(Email_Category, inputs=[url, file, question], outputs=[answer])
        # btn.click(Sentiment, inputs = [question], outputs=[Sent])
        # btn.click(Summarized, inputs = [question], outputs=[Summary])
        # btn.click(quick_resp, inputs = [question], outputs=[Quick_Response])
        # btn.click(priority, inputs = [question], outputs=[Priority])
    btn = gr.Button(value='Submit',scale=1,elem_id="warning1",elem_classes="feedback")
    btn.style(full_width=True)
    btn.click(Email_Category, inputs=[url, file, question], outputs=[answer])
    btn.click(Sentiment_analysis, inputs = [url, file, question], outputs=[Sent])
    btn.click(Summarized_Query, inputs = [url, file, question], outputs=[Summary])
    btn.click(quick_response, inputs = [url, file, question], outputs=[Quick_Response])
    btn.click(priority_check, inputs = [url, file, question], outputs=[Priority])

demo.launch()