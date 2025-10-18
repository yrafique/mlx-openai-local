#!/usr/bin/env python3
"""
Test speech transcription with sample audio file.
"""

import sys
import os
import base64
import json

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server.tools.voice import speech_to_text


def test_transcription(audio_file_path):
    """Test transcription with an audio file."""
    print("=" * 80)
    print("Testing Voice Transcription")
    print("=" * 80)
    print(f"\nAudio file: {audio_file_path}")

    # Read audio file
    if not os.path.exists(audio_file_path):
        print(f"❌ Error: Audio file not found at {audio_file_path}")
        return

    # Read and encode audio
    with open(audio_file_path, 'rb') as f:
        audio_data = f.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

    print(f"Audio size: {len(audio_data)} bytes")
    print(f"Base64 size: {len(audio_base64)} characters")
    print("\nTranscribing...")
    print("-" * 80)

    # Transcribe
    result = speech_to_text(audio_base64, language="en")
    data = json.loads(result)

    # Display results
    print(f"\nStatus: {data.get('status')}")

    if data.get('status') == 'success':
        print(f"✅ Transcription successful!")
        print(f"\nTranscribed Text:")
        print("-" * 80)
        print(data.get('text'))
        print("-" * 80)
        print(f"\nLanguage: {data.get('language')}")
        print(f"Timestamp: {data.get('timestamp')}")
    else:
        print(f"❌ Transcription failed!")
        print(f"Error: {data.get('error')}")
        print(f"Message: {data.get('answer')}")

    print("\n" + "=" * 80)

    return data


if __name__ == "__main__":
    # Get audio file path from command line or use default
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
    else:
        # Use default sample audio
        audio_path = os.path.join(os.path.dirname(__file__), 'audio', 'sample.mp3')

    test_transcription(audio_path)
