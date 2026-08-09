import asyncio
import edge_tts
import os
import tempfile

def text_to_speech_hindi(text: str, voice_type: str = "female") -> str:
    """
    Microsoft Edge TTS Engine (Natural Neural Voice)
    Female: hi-IN-SwaraNeural
    Male: hi-IN-MadhurNeural
    """
    if not text or not text.strip():
        return None

    # Female Voice Default Set
    selected_voice = "hi-IN-SwaraNeural" if voice_type == "female" else "hi-IN-MadhurNeural"

    temp_dir = tempfile.gettempdir()
    output_filename = os.path.join(temp_dir, "ai_natural_response.mp3")

    async def _generate_audio():
        communicate = edge_tts.Communicate(text, selected_voice)
        await communicate.save(output_filename)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate_audio())
        loop.close()

        if os.path.exists(output_filename):
            return output_filename
    except Exception as e:
        print(f"Edge TTS Error: {e}")
        return None

    return None

def is_mic_available() -> bool:
    return False
