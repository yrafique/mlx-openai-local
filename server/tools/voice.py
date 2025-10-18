"""
Voice capabilities - Speech-to-Text and Text-to-Speech.
Enables voice interaction like ChatGPT Voice.
"""

import json
import base64
from typing import Dict, Any
from datetime import datetime


def speech_to_text(audio_base64: str, language: str = "en") -> str:
    """
    Convert speech audio to text using Whisper.

    Args:
        audio_base64: Base64 encoded audio file (wav, mp3, m4a, etc.)
        language: Language code (default: "en")

    Returns:
        JSON string with transcribed text
    """
    try:
        import whisper
        import tempfile
        import os

        # Decode base64 audio
        audio_data = base64.b64decode(audio_base64)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name

        try:
            # Load Whisper model (base model for speed, can use "small", "medium", "large" for better accuracy)
            model = whisper.load_model("base")

            # Transcribe
            result = model.transcribe(tmp_path, language=language)

            text = result["text"].strip()

            return json.dumps({
                "status": "success",
                "text": text,
                "language": result.get("language", language),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "answer": f"**Transcription:**\n\n{text}"
            }, indent=2)

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except ImportError:
        return json.dumps({
            "status": "error",
            "error": "Whisper not installed",
            "answer": "Speech-to-text requires OpenAI Whisper. Install with: `pip install openai-whisper`"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "answer": f"Error transcribing audio: {str(e)}"
        })


def text_to_speech(text: str, voice: str = "alloy", speed: float = 1.0) -> str:
    """
    Convert text to speech audio.

    Args:
        text: Text to convert to speech
        voice: Voice to use ("alloy", "echo", "fable", "onyx", "nova", "shimmer")
        speed: Speech speed (0.25 to 4.0, default: 1.0)

    Returns:
        JSON string with audio data as base64
    """
    try:
        # Use pyttsx3 for offline TTS (works without API keys)
        import pyttsx3
        import tempfile
        import os

        # Initialize TTS engine
        engine = pyttsx3.init()

        # Set properties
        rate = engine.getProperty('rate')
        engine.setProperty('rate', int(rate * speed))

        # Get available voices
        voices = engine.getProperty('voices')

        # Map voice parameter to actual voices if available
        # This is a simple mapping - you might want to customize based on available voices
        if voices:
            engine.setProperty('voice', voices[0].id)  # Use first available voice

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Generate speech
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()

            # Read and encode audio
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            return json.dumps({
                "status": "success",
                "audio_base64": audio_base64,
                "audio_format": "wav",
                "text": text,
                "voice": voice,
                "speed": speed,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "answer": f"🔊 **Audio generated for text:**\n\n{text[:200]}{'...' if len(text) > 200 else ''}\n\n[Audio available for playback]"
            }, indent=2)

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except ImportError:
        return json.dumps({
            "status": "error",
            "error": "pyttsx3 not installed",
            "answer": "Text-to-speech requires pyttsx3. Install with: `pip install pyttsx3`"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "answer": f"Error generating speech: {str(e)}"
        })


# Tool definitions
VOICE_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "speech_to_text",
            "description": "Convert speech audio to text using Whisper. Use when user provides audio input or voice messages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "audio_base64": {
                        "type": "string",
                        "description": "Base64 encoded audio file (wav, mp3, m4a, etc.)"
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code (e.g., 'en', 'es', 'fr', 'de')",
                        "default": "en"
                    }
                },
                "required": ["audio_base64"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "text_to_speech",
            "description": "Convert text to speech audio. Use when user asks for audio output or wants to hear the response.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to convert to speech"
                    },
                    "voice": {
                        "type": "string",
                        "enum": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                        "description": "Voice to use for speech",
                        "default": "alloy"
                    },
                    "speed": {
                        "type": "number",
                        "description": "Speech speed (0.25 to 4.0)",
                        "default": 1.0
                    }
                },
                "required": ["text"]
            }
        }
    }
]

# Tool execution mapping
VOICE_TOOL_FUNCTIONS = {
    "speech_to_text": speech_to_text,
    "text_to_speech": text_to_speech
}


def execute_voice_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a voice tool by name.

    Args:
        tool_name: Name of the tool
        arguments: Tool arguments

    Returns:
        Tool result as JSON string
    """
    if tool_name not in VOICE_TOOL_FUNCTIONS:
        return json.dumps({
            "status": "error",
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(VOICE_TOOL_FUNCTIONS.keys())
        })

    try:
        func = VOICE_TOOL_FUNCTIONS[tool_name]
        result = func(**arguments)
        return result
    except Exception as e:
        return json.dumps({
            "status": "error",
            "tool": tool_name,
            "error": str(e),
            "answer": f"Tool execution failed: {str(e)}"
        })


if __name__ == "__main__":
    print("=" * 80)
    print("Testing Voice Capabilities")
    print("=" * 80)

    # Test text-to-speech
    print("\n1. Testing Text-to-Speech...")
    print("-" * 80)

    test_text = "Hello! This is a test of the text to speech system. It works offline using pyttsx3."

    result_tts = text_to_speech(test_text, voice="alloy", speed=1.0)
    data_tts = json.loads(result_tts)

    print(f"Status: {data_tts['status']}")
    if data_tts['status'] == 'success':
        print(f"Audio format: {data_tts.get('audio_format')}")
        print(f"Audio size: {len(data_tts.get('audio_base64', ''))}")
        print("✅ Text-to-speech working!")
    else:
        print(f"Error: {data_tts.get('error')}")
        print(f"Note: {data_tts.get('answer')}")

    print("\n" + "=" * 80)
    print("Voice capabilities ready!")
    print("=" * 80)
