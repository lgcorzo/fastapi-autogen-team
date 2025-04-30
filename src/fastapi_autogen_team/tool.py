# export R2R_API_KEY=...
import os
from r2r import R2RClient


def search(query: str):
  
  user = os.getenv("R2R_USER")  
  pwd = os.getenv("R2R_PWD")  
  base_url = os.getenv("R2R_URL", "http://r2r:7272")
  client = R2RClient(base_url=base_url) 
  client.users.login(user, pwd)

  response = client.retrieval.rag(
    query=query,
  )
  return response
