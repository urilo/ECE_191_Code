import Jetson.GPIO as GPIO
import pyaudio
import wave
import spidev
# Use a pipeline as a high-level helper
from transformers import pipeline, WhisperProcessor, WhisperForConditionalGeneration

# large model
pipe = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3")

# whisper tiny model for English only
pipe_med = pipeline("automatic-speech-recognition", model="openai/whisper-medium")


# Set up GPIO pin for push button
button_pin = 8
GPIO.setmode(GPIO.BOARD)
GPIO.setup(button_pin, GPIO.IN)

# Set up SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0

# Audio recording parameters

# FORMAT: Audio format (16-bit PCM).
# CHANNELS: Number of audio channels (1 for mono).
# RATE: Sample rate
# CHUNK: Buffer size for audio input.
# RECORD_SECONDS: Duration of audio recording.
# WAVE_OUTPUT_FILENAME: Output filename for the recorded WAV file.

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"


def record_audio():

    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    # Open audio stream
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    frames = []
    # Record audio while button is pressed
    print("Recording...")
    # Record audio while button is pressed
    while GPIO.input(button_pin) == GPIO.HIGH:
        data = stream.read(CHUNK)
        frames.append(data)

    print("Button released. Performing speech recognition...")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Write audio data to WAV file
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # Perform speech recognition
    recognized_text = pipe_med(WAVE_OUTPUT_FILENAME)[0]['transcription']

    # outputs a string text
    return recognized_text

# Main function
def main():
    try:
        while True:
            # Check if button is pressed
            if GPIO.input(button_pin) == GPIO.HIGH:
                # Record audio and perform speech recognition
                recognized_text = record_audio()
                print("The result text is:", recognized_text)

                # Send recognized text over SPI
                spi.xfer(list(recognized_text.encode()))

    except KeyboardInterrupt:
        print("Connection Lost.")
        GPIO.cleanup()
        spi.close()

if __name__ == "__main__":
    main()