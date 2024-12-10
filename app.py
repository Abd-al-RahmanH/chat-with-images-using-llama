import streamlit as st
import base64
import os
import requests
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# WatsonX API key from .env
watsonx_api_key = os.getenv("WATSONX_API_KEY")

def convert_image_to_base64(uploaded_file):
    """Convert uploaded image to Base64."""
    bytes_data = uploaded_file.getvalue()
    base64_image = base64.b64encode(bytes_data).decode()
    return base64_image

def get_auth_token(api_key):
    """Authenticate and retrieve the WatsonX API token."""
    auth_url = "https://iam.cloud.ibm.com/identity/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key
    }

    response = requests.post(auth_url, headers=headers, data=data, verify=False)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        st.error("Failed to authenticate with WatsonX API.")
        raise Exception("Failed to get authentication token")

def main():
    st.title("Chat with Images")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = False

    # User uploads an image
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        with st.chat_message("user"):
            st.image(image, caption='Uploaded Image', use_column_width=True)
            base64_image = convert_image_to_base64(uploaded_file)
            if not st.session_state.uploaded_file:
                st.session_state.messages.append({
                    "role": "user", 
                    "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}]
                })
                st.session_state.uploaded_file = True

    # Display chat messages
    for msg in st.session_state.messages[1:]:
        if msg['role'] == "user":
            with st.chat_message("user"):
                if msg['content'][0]['type'] == "text":
                    st.write(msg['content'][0]['text'])
        else:
            st.chat_message("assistant").write(msg["content"])

    # User inputs text
    user_input = st.chat_input("Type your message here...")

    if user_input:
        message = {"role": "user", "content": [{"type": "text", "text": user_input}]}
        st.session_state.messages.append(message)
        st.chat_message(message['role']).write(user_input)

        # Prepare WatsonX API request
        model_messages = []
        latest_image_url = None
        for msg in st.session_state.messages:
            if msg["role"] == "user" and isinstance(msg["content"], list):
                content = []
                for item in msg["content"]:
                    if item["type"] == "text":
                        content.append(item)
                    elif item["type"] == "image_url":
                        latest_image_url = item
                if latest_image_url:
                    content.append(latest_image_url)
                model_messages.append({"role": msg["role"], "content": content})
            else:
                model_messages.append({"role": msg["role"], "content": [{"type": "text", "text": msg["content"]}] if isinstance(msg["content"], str) else msg["content"]})

        body = {
            "messages": [model_messages[-1]],
            "project_id": "d4459e4b-78c3-45d1-84a0-2429a90483e0",
            "model_id": "meta-llama/llama-3-2-90b-vision-instruct",
            "decoding_method": "greedy",
            "repetition_penalty": 1,
            "max_tokens": 900
        }

        YOUR_ACCESS_TOKEN = get_auth_token(watsonx_api_key)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {YOUR_ACCESS_TOKEN}"
        }

        response = requests.post(
            "https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2023-05-29",
            headers=headers,
            json=body
        )

        if response.status_code != 200:
            st.error("Error from WatsonX API.")
            raise Exception("Non-200 response: " + str(response.text))

        data = response.json()
        res_content = data['choices'][0]['message']['content']

        st.session_state.messages.append({"role": "assistant", "content": res_content})
        with st.chat_message("assistant"):
            st.write(res_content)

if __name__ == "__main__":
    main()
