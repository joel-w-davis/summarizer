from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter
from urllib.parse import urlparse, parse_qs
import openai
import os
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI


# Load environment variables from the .env file
load_dotenv(find_dotenv())
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

# Set your OpenAI API key from the .env file
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_video_id(url):
    """
    Extract the video ID from a YouTube URL.
    """
    parsed_url = urlparse(url)
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if 'v' in parse_qs(parsed_url.query):
            return parse_qs(parsed_url.query)['v'][0]
    elif parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    return None

def fetch_transcript(video_id):
    """
    Fetch the transcript for a given YouTube video ID.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        return str(e)

def summarize_with_openai(transcript_text):
    """
    Send the full transcript to OpenAI for summarization using the chat completion API.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Change to "gpt-4" if you have access
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes YouTube transcripts."},
                {"role": "user", "content": f"Summarize the following transcript:\n\n{transcript_text}"}
            ],
            max_tokens=200,  # Adjust based on desired length
            temperature=0.5
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        return str(e)

@app.route('/transcript', methods=['GET'])
def get_transcript():
    """
    Endpoint to get the transcript of a YouTube video and provide a summary.
    """
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400

    video_id = get_video_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400

    transcript = fetch_transcript(video_id)
    if isinstance(transcript, str):
        return jsonify({'error': transcript}), 500

    formatter = JSONFormatter()
    formatted_transcript = formatter.format_transcript(transcript)

    # Convert the formatted transcript into plain text
    transcript_text = ' '.join([entry['text'] for entry in transcript])

    # Generate a summary of the transcript using OpenAI's API
    summary = summarize_with_openai(transcript_text)

    return jsonify({
        'transcript': formatted_transcript,
        'summary': summary
    })

if __name__ == '__main__':
    app.run(debug=True)




