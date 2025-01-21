# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI

client = OpenAI(api_key="sk-e0365992728d4327bce4f78c522146ca", base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {"role": "system", "content": "我是傻逼"},
        {"role": "user", "content": "你是谁"},
    ],
    stream=False
)

print(response.choices[0].message.content)