import logging
import os
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydub import AudioSegment
import io
import requests

app = FastAPI()

log_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "app.log")
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def speech_to_text(audio_file_path, subscription_key, region):
    # API endpoint
    url = f"https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
    # url = f"https://{region}.no-mrs-entity-speech-serv.cognitiveservices.azure.com/"

    # Request headers
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Content-Type': 'audio/wav',
        'Accept': 'application/json'
    }

    # Query parameters
    params = {
        'language': 'en-US',
        'format': 'detailed'
    }

    # Read audio file
    with open(audio_file_path, 'rb') as audio_file:
        audio_data = audio_file.read()

    # Send POST request
    response = requests.post(url, headers=headers, params=params, data=audio_data)

    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        print(result)
        return result['DisplayText']
    else:
        return f"Error: {response.status_code}, {response.text}"

# Usage example
subscription_key = '4d178a95dfe340fc9c13535bbf2f7917'
region = 'southcentralus'

# subscription_key = "f15959209a4f447192c4352c2c9ef599"
# region = "southcentralus"


@app.get('/health')
def root():
    return {'status': 'up'}


@app.post("/upload")
async def upload_file(mp3_file: UploadFile = File(...)):
    try:
        logging.info("Received request to transcribe")
        # Read the uploaded MP3 file
        mp3_data = await mp3_file.read()
        
        logging.info("Reading data")
        # Convert MP3 data to AudioSegment
        audio_segment = AudioSegment.from_file(io.BytesIO(mp3_data))
        
        # Define the path where you want to save the MP3 file
        current_path = os.path.dirname(os.path.realpath(__file__))
        save_path = os.path.join(current_path, "recorded_audio.wav")
        
        # Save the AudioSegment as an MP3 file
        audio_segment.export(save_path, format='wav')

        logging.info("Starting transcription")
        transcript_text = speech_to_text(save_path, subscription_key, region)
        # Convert transcript_text to lowercase for case-insensitive comparisons
        transcript_text_lower = transcript_text.lower()

        # Replace conditions from JavaScript with equivalent Python if statements
        if "are" in transcript_text_lower:
            transcript_text = "r"
        if "tee" in transcript_text_lower:
            transcript_text = "t"
        if "hen" in transcript_text_lower or "en" in transcript_text_lower or "and" in transcript_text_lower or "an" in transcript_text_lower or "in" in transcript_text_lower:
            transcript_text = "n"
        if "ex" in transcript_text_lower:
            transcript_text = "x"
        if "you" in transcript_text_lower:
            transcript_text = "u"
        logging.info("Transcription ended")
        logging.info(f"Transcription result: {transcript_text}")
        
        return JSONResponse(content={"transcript": transcript_text})
    except Exception as e:
        logging.info(f"Error: {e}")# error e
        return JSONResponse(content={"message": "Failed to transcribe", "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True,port=8000)