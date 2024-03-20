import os
import requests
from flask import Flask, render_template, request
from PIL import Image
from io import BytesIO
import pytesseract
import moviepy.editor as mp
import speech_recognition as sr
import openai

app = Flask(__name__)

# Define paths to Tesseract executable and temporary audio file
path_to_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
temp_audio_file = "temp_audio.wav"

# Retrieve OpenAI API key from environment variable
openai.api_key = "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"

# Function to process image text extraction
def extract_text_from_image(image_url):
    # Download the image from the URL
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))

    # Provide the tesseract executable location to pytesseract library
    pytesseract.pytesseract.tesseract_cmd = path_to_tesseract

    # Extract text from the image
    text = pytesseract.image_to_string(img)

    return text.strip()

# Function to process video speech-to-text
def extract_text_from_video(video_file):
    try:
        # Load the video
        video = mp.VideoFileClip(video_file)

        # Extract the audio from the video
        audio_file = video.audio
        audio_file.write_audiofile(temp_audio_file)

        # Initialize recognizer
        r = sr.Recognizer()

        # Load the audio file
        with sr.AudioFile(temp_audio_file) as source:
            data = r.record(source)

        # Convert speech to text
        text = r.recognize_google(data)

        return text.strip()

    except sr.UnknownValueError:
        return "Speech could not be recognized due to poor audio quality or background noise."

# Function to generate response using OpenAI
def generate_response(input_text):
    messages = [{"role": "system", "content":
                    "You are an intelligent assistant that summarizes the input given and detects hate speech if any and give the reason for your answers. If detected any hate speech,violence or socially harmful content report 'Socially harmful content detected' and give a reason or else give the summary of the video."}]
    messages.append({"role": "user", "content": input_text})
    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages)
    reply = chat.choices[0].message.content

    return reply.strip()

# Function to process input data using the provided Python script
def process_data(input_data, caption):
    # Check if the input is an image or a video
    if input_data.endswith(('.jpg', '.jpeg', '.png', '.gif')):
        extracted_text = extract_text_from_image(input_data)
    elif input_data.endswith(('.mp4', '.avi', '.mov')):
        extracted_text = extract_text_from_video(input_data)
    else:
        extracted_text = "Unsupported file format."

    # Add the caption to the extracted text
    extracted_text += "\nCaption: " + caption

    response = generate_response(extracted_text)
    return response

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['POST'])
def uploader():
    if request.method == 'POST':
        f = request.files['file']
        caption = request.form['caption']  # Get the caption text from the form
        filepath = os.path.join("uploads", f.filename)
        f.save(filepath)
        result = process_data(filepath, caption)
        return result

if __name__ == '__main__':
    app.run(debug=True)
