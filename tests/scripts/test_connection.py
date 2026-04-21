import requests
import json
import os
import sys

def test_agent_team(prompt, model="internal-gpt4_v0.1"):
    url = "http://10.152.183.237/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-1234"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    
    print(f"Sending request to {url} with model {model}...")
    try:
        response = requests.post(url, headers=headers, json=data, timeout=300)
        response.raise_for_status()
        result = response.json()
        return result
    except Exception as e:
        print(f"Error: {e}")
        if 'response' in locals():
            print(f"Response content: {response.text}")
        return None

if __name__ == "__main__":
    prompt = "que es el mlops y como se defien un proyecto por pasos"
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    
    result = test_agent_team(prompt)
    if result:
        print("\n--- Response ---\n")
        print(result['choices'][0]['message']['content'])
        
        # Save to artifacts directory in the repo
        output_dir = "/mnt/F024B17C24B145FE/Repos/rust-agent-team/.artifacts"
        os.makedirs(output_dir, exist_ok=True)
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"execution_results_{timestamp}.json")
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nArtifact saved to: {output_file}")
    else:
        sys.exit(1)
