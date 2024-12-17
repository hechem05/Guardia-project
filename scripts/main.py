import json
import pyaudio  # Alternative to sounddevice for audio input/output
from scipy.io.wavfile import write  # Used to save audio file
import pyttsx3  # For text-to-speech (TTS)
import os  # For checking file existence
import speech_recognition as sr
import wave


# Record audio using pyaudio and save it to file
def record_audio(record_seconds=5, output_filename="output.wav"):
    # Parameters for pyaudio
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 1
    rate = 44100  # Record at 44100 samples per second

    p = pyaudio.PyAudio()

    print("Recording...")

    # Open the stream
    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=rate,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []

    # Store data in chunks for the record_seconds duration
    for i in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    print("Finished recording.")

    # Save the recorded data as a WAV file
    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()


#  Load and Parse the JSON Log File
def load_json_data(file_path=r"C:\Pristini\Guardia project\scripts\log_p-guard.json"):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print("Log file not found.")
        return []
    except json.JSONDecodeError:
        print("Error decoding the JSON file.")
        return []


# Step 3: Chatbot Logic for Text-Based Interaction
def respond_to_query(query, data):
    response = ""

    # Handle battery-related queries
    if "battery" in query.lower():
        for entry in data:
            battery = entry.get("_source", {}).get("battery", "No battery info available")
            response += f"The robot’s battery is at {battery}%.\n"

    # Handle patrol status-related queries
    elif "patrol" in query.lower():
        for entry in data:
            patrol_status = entry.get("_source", {}).get("patrolStatus", "No patrol status available")
            response += f"The robot is currently {patrol_status}.\n"

    # Handle error or camera-related queries
    elif "error" in query.lower() or "camera" in query.lower():
        for entry in data:
            error_logs = entry.get("_source", {}).get("errorLogs", {})
            if error_logs:
                for error in error_logs.get("ipStatus", []):
                    response += f"Error: {error.get('info', 'Unknown error')} on {error.get('date', 'Unknown date')}.\n"
            else:
                response += "No errors found.\n"

    # Handle general queries like 
    elif "doing" in query.lower() or "operational" in query.lower() or "status" in query.lower():
        for entry in data:
            battery = entry.get("_source", {}).get("battery", "No battery info available")
            patrol_status = entry.get("_source", {}).get("patrolStatus", "No patrol status available")
            error_logs = entry.get("_source", {}).get("errorLogs", {})

            # General status report
            response += f"The robot’s battery is at {battery}%. "
            response += f"It is currently {patrol_status}.\n"

            if error_logs:
                for error in error_logs.get("ipStatus", []):
                    response += f"Also, there was an error: {error.get('info', 'Unknown error')} on {error.get('date', 'Unknown date')}.\n"
            else:
                response += "No errors have been logged.\n"

    # Handle unrecognized queries
    else:
        response = "Sorry, I didn't understand that."

    return response


# Step 4: Text-to-Speech Function
def speak_text(text):
    engine = pyttsx3.init()

    # Set properties for TTS
    engine.setProperty('rate', 150)  # Speed of speech
    engine.setProperty('volume', 1)  # Volume level (0.0 to 1.0)

    # Get available voices
    voices = engine.getProperty('voices')

    # Set voice based on your preference (0 for male, 1 for female)
    engine.setProperty('voice', voices[1].id)  # Choosing female voice

    engine.say(text)
    engine.runAndWait()


# Step 5: Voice Command Function (Speech-to-Text)
def listen_and_respond(data):
    record_audio()
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile("output.wav") as source:
            audio = recognizer.record(source)
            print("Audio from file captured.")  # Debugging: Print raw audio data
            query = recognizer.recognize_google(audio)
            print(f"Audio file recognized query: {query}")
            response = respond_to_query(query, data)
            print(response)  # For text-based response
            speak_text(response)  # For voice-based response
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand the audio from the file.")
        speak_text("Sorry, I couldn't understand the audio from the file.")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        speak_text("Sorry, there was an issue with the speech recognition service.")


# Main Loop
if __name__ == "__main__":

    data = load_json_data()  # Load the log data at the start

    # Optionally choose whether to use text or voice interaction
    mode = input(
        "Type 'voice' for voice interaction, 'audio' for pre-recorded file, or press Enter for text: ").strip().lower()

    if mode == "voice":
        while True:
            listen_and_respond(data)  # Voice-based interaction
    elif mode == "audio":
        file_name = "tlnyr-u9rht.wav"  # Use only the filename
        if os.path.isfile(file_name):
            listen_and_respond(data)  # Test using a pre-recorded audio file
        else:
            print(f"File not found: {file_name}")
    else:
        # Text-based chatbot interaction
        while True:
            user_query = input("Ask a question: ")
            response = respond_to_query(user_query, data)
            print(response)
