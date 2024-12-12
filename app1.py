import streamlit as st
import base64
from PIL import Image
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()
api_key = os.getenv("IBM_API_KEY")

# Function to convert image to Base64
def convert_image_to_base64(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    base64_image = base64.b64encode(bytes_data).decode()
    return base64_image

# Function to get authentication token
def get_auth_token(api_key):
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
        st.error("Failed to get authentication token. Please check your API key.")
        return None

# Main function
def main():
    st.title("Chat with Images")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = False

    # File uploader
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        with st.chat_message("user"):
            st.image(image, caption="Uploaded Image", use_container_width=True)
            base64_image = convert_image_to_base64(uploaded_file)
            if not st.session_state.uploaded_file:
                st.session_state.messages.append({
                    "role": "user",
                    "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}]
                })
                st.session_state.uploaded_file = True

    # Display chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                if "text" in msg["content"][0]:
                    st.write(msg["content"][0]["text"])
        else:
            with st.chat_message("assistant"):
                st.write(msg["content"])

    # User input
    user_input = st.chat_input("Type your message here...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": [{"type": "text", "text": user_input}]})
        with st.chat_message("user"):
            st.write(user_input)

        # API call to IBM Watson for response
        token = get_auth_token(api_key)
        if token:
            url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2023-05-29"
            body = {
                "messages": st.session_state.messages,
                "project_id": "833c9053-ef07-455e-819f-6557dea2f8bc",
                "model_id": "meta-llama/llama-3-2-90b-vision-instruct",
                "decoding_method": "greedy",
                "repetition_penalty": 1,
                "max_tokens": 900
            }
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            response = requests.post(url, headers=headers, json=body)
            if response.status_code == 200:
                res_content = response.json()['choices'][0]['message']['content']
                st.session_state.messages.append({"role": "assistant", "content": res_content})
                with st.chat_message("assistant"):
                    st.write(res_content)
            else:
                st.error("Failed to fetch response from the model.")
    
    # Friendly follow-up
    st.write("If you have any other questions about the image, feel free to ask!")

if __name__ == "__main__":
    main()
