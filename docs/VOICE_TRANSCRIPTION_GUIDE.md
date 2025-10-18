# Voice Transcription Guide

## Overview

Your MLX Omni Server now has full voice transcription capabilities using OpenAI Whisper. This enables speech-to-text functionality for audio files and voice interactions.

## Prerequisites

✅ **All dependencies are installed via Poetry:**
- `openai-whisper` - Whisper AI model
- `ffmpeg` - Audio processing (installed system-wide)

## Quick Test

We've created a sample audio file and test script for you:

```bash
# Test transcription with sample audio
poetry run python3 tests/test_transcription.py tests/audio/sample.mp3
```

**Expected Output:**
```
================================================================================
Testing Voice Transcription
================================================================================

Audio file: tests/audio/sample.mp3
Audio size: 26684 bytes
Base64 size: 35580 characters

Transcribing...
--------------------------------------------------------------------------------

Status: success
✅ Transcription successful!

Transcribed Text:
--------------------------------------------------------------------------------
Hello, this is a test of the voice transcription system using Whisper AI...
--------------------------------------------------------------------------------

Language: en
Timestamp: 2025-10-18 03:36:43
```

## Usage

### 1. Python API

```python
from server.tools.voice import speech_to_text
import base64
import json

# Read audio file
with open('audio.mp3', 'rb') as f:
    audio_data = f.read()
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')

# Transcribe
result = speech_to_text(audio_base64, language="en")
data = json.loads(result)

if data['status'] == 'success':
    print(f"Transcription: {data['text']}")
    print(f"Language: {data['language']}")
else:
    print(f"Error: {data['error']}")
```

### 2. Direct Function Call

```python
from server.tools.voice import speech_to_text

# With base64 encoded audio
result = speech_to_text(
    audio_base64="your_base64_encoded_audio_here",
    language="en"  # or "es", "fr", "de", etc.
)
```

### 3. Create Your Own Audio Sample

```bash
# Using macOS say command
say -o tests/audio/my_sample.aiff "Your text here"

# Convert to MP3
ffmpeg -i tests/audio/my_sample.aiff -ar 16000 -ac 1 -c:a libmp3lame tests/audio/my_sample.mp3 -y

# Test transcription
poetry run python3 tests/test_transcription.py tests/audio/my_sample.mp3
```

## Supported Audio Formats

Whisper supports various audio formats through ffmpeg:
- ✅ MP3
- ✅ WAV
- ✅ M4A
- ✅ FLAC
- ✅ OGG
- ✅ OPUS

## Whisper Models

The default is `base` model for speed. You can change models in `server/tools/voice.py`:

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | 39M | Very Fast | Low |
| base | 74M | Fast | **Default** |
| small | 244M | Medium | Good |
| medium | 769M | Slow | Better |
| large | 1550M | Very Slow | Best |

**To change model:**
```python
# In server/tools/voice.py, line 38
model = whisper.load_model("base")  # Change to "small", "medium", or "large"
```

## Supported Languages

Whisper supports 99+ languages. Common examples:

```python
speech_to_text(audio_base64, language="en")  # English
speech_to_text(audio_base64, language="es")  # Spanish
speech_to_text(audio_base64, language="fr")  # French
speech_to_text(audio_base64, language="de")  # German
speech_to_text(audio_base64, language="zh")  # Chinese
speech_to_text(audio_base64, language="ja")  # Japanese
speech_to_text(audio_base64, language="ar")  # Arabic
```

## Integration with LangChain

```python
from langchain_openai import ChatOpenAI
from server.tools.voice import speech_to_text, VOICE_TOOL_DEFINITIONS
import base64
import json

# Initialize LLM with voice tools
llm = ChatOpenAI(
    base_url="http://localhost:7007/v1",
    api_key="local-demo-key",
    model="mlx-community/Qwen2.5-3B-Instruct-4bit"
).bind_tools(VOICE_TOOL_DEFINITIONS)

# User provides audio
with open('user_audio.mp3', 'rb') as f:
    audio_base64 = base64.b64encode(f.read()).decode('utf-8')

# LLM can call speech_to_text tool
messages = [
    {"role": "user", "content": "Please transcribe this audio"},
    {"role": "user", "content": f"audio_data: {audio_base64[:100]}..."}  # Truncated for display
]

response = llm.invoke(messages)
# LLM will generate tool call for speech_to_text
```

## Response Format

**Success Response:**
```json
{
  "status": "success",
  "text": "Transcribed text here",
  "language": "en",
  "timestamp": "2025-10-18 03:36:43",
  "answer": "**Transcription:**\n\nTranscribed text here"
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "Error description",
  "answer": "User-friendly error message"
}
```

## Troubleshooting

### Issue: "Whisper not installed"

**Solution:**
```bash
./scripts/orchestrate.sh --install
```

This installs all dependencies including Whisper via Poetry.

### Issue: "ffmpeg not found"

**Solution:**
```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt install ffmpeg

# Linux (Fedora/RHEL)
sudo dnf install ffmpeg
```

### Issue: "FP16 is not supported on CPU"

This is just a warning and can be ignored. Whisper will use FP32 instead.

### Issue: Slow transcription

**Solutions:**
1. Use smaller Whisper model (`tiny` or `base`)
2. Use Apple Silicon acceleration (if available)
3. Reduce audio file size
4. Lower audio sample rate to 16kHz

### Issue: Incorrect transcription

**Solutions:**
1. Use larger model (`small`, `medium`, or `large`)
2. Specify correct language
3. Ensure audio quality is good
4. Remove background noise

## Performance Tips

**Optimize for Speed:**
```python
# Use tiny model
model = whisper.load_model("tiny")

# Specify language (skips language detection)
result = model.transcribe(audio_path, language="en")
```

**Optimize for Accuracy:**
```python
# Use larger model
model = whisper.load_model("medium")

# Enable more detailed options
result = model.transcribe(
    audio_path,
    language="en",
    temperature=0.0,  # More deterministic
    best_of=5,  # Try multiple decodings
    beam_size=5  # Use beam search
)
```

## Example Use Cases

### 1. Voice Commands
```python
# User speaks command
audio_file = "command.mp3"
with open(audio_file, 'rb') as f:
    audio_base64 = base64.b64encode(f.read()).decode('utf-8')

result = speech_to_text(audio_base64)
data = json.loads(result)
command = data['text']

# Process command
if "turn on" in command.lower():
    print("Turning on...")
```

### 2. Meeting Transcription
```python
# Long meeting audio
with open('meeting.mp3', 'rb') as f:
    audio_base64 = base64.b64encode(f.read()).decode('utf-8')

result = speech_to_text(audio_base64)
data = json.loads(result)

# Save transcript
with open('meeting_transcript.txt', 'w') as f:
    f.write(data['text'])
```

### 3. Multi-language Support
```python
# Detect and transcribe multiple languages
languages = ['en', 'es', 'fr', 'de']

for lang in languages:
    result = speech_to_text(audio_base64, language=lang)
    data = json.loads(result)
    print(f"{lang}: {data['text'][:100]}...")
```

## Test Files

We've created sample test files for you:

```
tests/
├── audio/
│   ├── sample.mp3          # Sample audio file
│   └── sample.aiff         # Original AIFF format
└── test_transcription.py   # Test script
```

**Create more test samples:**
```bash
# Create custom samples
say -o tests/audio/hello.aiff "Hello world"
ffmpeg -i tests/audio/hello.aiff tests/audio/hello.mp3 -y

# Test
poetry run python3 tests/test_transcription.py tests/audio/hello.mp3
```

## Voice Tool Definitions

The voice tools are already defined and ready to use:

```python
from server.tools.voice import VOICE_TOOL_DEFINITIONS, execute_voice_tool

# Available tools
tools = VOICE_TOOL_DEFINITIONS
# [
#     {"type": "function", "function": {"name": "speech_to_text", ...}},
#     {"type": "function", "function": {"name": "text_to_speech", ...}}
# ]

# Execute tool
result = execute_voice_tool(
    tool_name="speech_to_text",
    arguments={"audio_base64": "...", "language": "en"}
)
```

## Configuration in .env

Add voice-related settings to your `.env` file:

```bash
# Voice Features
ENABLE_VOICE=true
WHISPER_MODEL=base  # tiny, base, small, medium, large
WHISPER_LANGUAGE=en  # Default language
WHISPER_DEVICE=cpu   # cpu or cuda
```

## API Integration

If you want to add a voice transcription endpoint to your API:

```python
from fastapi import FastAPI, File, UploadFile
from server.tools.voice import speech_to_text
import base64

app = FastAPI()

@app.post("/v1/audio/transcriptions")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    OpenAI-compatible transcription endpoint.
    """
    audio_data = await file.read()
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')

    result = speech_to_text(audio_base64)
    return json.loads(result)
```

## Summary

✅ **ffmpeg installed** - Audio processing ready
✅ **Whisper installed** - AI transcription ready
✅ **Sample audio created** - Test file available
✅ **Test script created** - Easy testing
✅ **Working transcription** - Fully functional

**Quick Start:**
```bash
# Test transcription
poetry run python3 tests/test_transcription.py

# Create your own audio
say -o my_audio.aiff "Your text here"
ffmpeg -i my_audio.aiff my_audio.mp3 -y

# Transcribe it
poetry run python3 tests/test_transcription.py my_audio.mp3
```

**Next Steps:**
- Integrate with LangChain agents
- Add real-time transcription
- Create voice command interface
- Build conversational AI with voice I/O

For more information:
- [Voice Implementation](../server/tools/voice.py)
- [Whisper Documentation](https://github.com/openai/whisper)
- [ffmpeg Documentation](https://ffmpeg.org/documentation.html)
