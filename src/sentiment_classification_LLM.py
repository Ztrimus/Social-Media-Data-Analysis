# !pip install sentencepiece==0.1.99
# !pip install transformers==4.31.0
# !pip install accelerate==0.21.0
# !pip install bitsandbytes==0.41.1

import json
import config
import credentials
from transformers import LlamaForCausalLM, LlamaTokenizer

category = ["AI Optimist", "neutral", "AI Pessimist"]

tokenizer = LlamaTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf", token=credentials.HF_TOKEN)
model = LlamaForCausalLM.from_pretrained("meta-llama/Llama-2-7b-chat-hf", load_in_8bit=True, device_map="auto", token=hf_access_token)

def llama2_talk(prompt_text):
    generation_kwargs = {
          "max_new_tokens": 512,
          "top_p": 0.9,
          "temperature": 0.6,
          "repetition_penalty": 1.2,
          "do_sample": True,
      }

    B_INST, E_INST = "[INST]", "[/INST]"
    prompt = f"{B_INST} {prompt_text} {E_INST}"  # Special format reuired by the Llama2 Chat Model
    prompt_ids = tokenizer(prompt, return_tensors="pt")
    prompt_size = prompt_ids['input_ids'].size()[1]
    generate_ids = model.generate(prompt_ids.input_ids.to(model.device), **generation_kwargs)
    generate_ids = generate_ids.squeeze()
    response = tokenizer.decode(generate_ids.squeeze()[prompt_size+1:], skip_special_tokens=True).strip()

    return response

def get_sentiment_classification_prompt(user):
    text = f"**User Sentiment Classification Request**\n\nBelow is an instruction that describes a task. Write a response that appropriately completes the request.\n\n### Instruction:\n\nUser profile can be categories like below.\n\nAI optimist, neutral, or AI pessimist\n\n\nBelow is some example classifications. the format is the user profile followed by classification tag.\n\n1. **User Profile:**\n- Bio: AI Ethusiat, working in AI for Good domain. Working toward making AI more accessable and safe\n\n- Post 1 Content: It's not like AI is giving biased data. It human how given bias data. so blaming AI is not good thing. Ai just learning from human So calling Ai fdanger is wrong thing.\n- Post 1 Hashtags: The post includes the following hashtags: #ai, #aiforgood.\n\n<classification>AI optimist</classification>\n\n\n2. **User Profile:**\n- Bio: General Attorny, Work in risk evalution, regulation and audit department\n\n- Post 1 Content: Resarch should stop working on AI technology recklessly. We never no small bug in system can endagours billions of human life. there should be proper evalution of risk at each step of AI development and if it causing any possble harm to living being. it should stop quickly.\n- Post 1 Hashtags: The post includes the following hashtags: #airegulation, #aiethics.\n\n<classification>AI pessimist</classification>\n\n\nClassify below user profile.\n\n**User Profile:**\n- Bio: {user['note']}\n"

    for index, post in enumerate(user['posts']):
        post_text = "\n"
        if len(post['content'].strip()):
            post_text += f"- Post {index+1} Content: {post['content']}\n"
        if len(post['attach_media_text'].strip()):
            post_text += f"- Media Text Attached to Post {index+1}: {post['attach_media_text']}\n"
        if len(post['tags']):
            hashtag_line = ", ".join(["#"+value if index+1 != len(value) else "and #"+value for index, value in enumerate(post['tags'])])
            post_text += f"- Post {index+1} Hashtags: The post includes the following hashtags: {hashtag_line}.\n"

        text+=post_text

    text += "### Response:\n\n<classification>and here is the category response from you</classification>\n\ngive me catgory in first line and do rest of explaination below"

    return text

# Get all user nodes
with open(config.JSON_DATA_PATH, "rb") as file:
    raw_data = json.load(file)

# Classify each user into AI Sentiment category
for user in raw_data:
  print(f"going through {user['id']}: {user['username']}")
  if 'is_sentiment_done' not in user:
    # Prompt Generation
    input_text = get_sentiment_classification_prompt(user)

    # passing prompt to LLM
    result = llama2_talk(input_text)

    for index, value in enumerate(category):
      if value.lower() in result.lower():
        user['ai_sentiment'][index] = 1
        if index !=1:
          user['ai_sentiment'][1] = 0
    print(user['ai_sentiment'])
    user['is_sentiment_done'] = True

    with open("./data.json", "w", encoding="utf-8") as file:
          json.dump(raw_data, file, ensure_ascii=False, indent=4)
    print("-"*100)