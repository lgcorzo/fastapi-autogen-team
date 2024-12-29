# Streaming Autogen with FastAPI 
This is an example FastAPI server that streams messages from the Autogen framework

https://medium.com/@moustafa.abdelbaky/building-an-openai-compatible-streaming-interface-using-server-sent-events-with-fastapi-and-8f014420bca7

## Installation
```sh
git clone https://github.com/LineaLabs/autogen-fastapi.git
cd autogen-fastapi
conda create -n autogen python=3.10
conda activate autogen
pip install -r requirements.txt
```

## Running the server
Make sure to set `OPENAI_API_KEY` in your environment variables or in `.env` file. You can get an API key from https://platform.openai.com/account/api-keys
```sh
./run.sh
```


## Querying the server

You can query the autogen agents using the following command: 
```sh
curl -X 'POST' \
  'http://localhost:8001/autogen/api/v1/chat/completions' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "model": "azure-gpt4",
  "messages": [
    {
      "role": "user",
      "content": "Get the local time form the system"
    }
  ],
  "temperature": 1,
  "top_p": 1,
  "presence_penalty": 0,
  "frequency_penalty": 0,
  "stream": true
}'
```
Note that you must provide the entire conversation history to the backend, as the server expects input in OpenAI format. 

## Documentation
``` 
docker build -t autogen_team 
``` 
Navigate to http://localhost:8001/autogen/api/v1/docs to see the docs. 

