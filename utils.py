import json

def seg_to_txt(segment) -> str:
    """Format transcript segment as plain text."""
    text = segment["text"].strip()
    speaker = "UNKNOWN_SPEAKER" if not "speaker" in segment else segment["speaker"]
    return f'{speaker}: {text}'

def jsonl_to_txt(jsonl: str) -> str:
    """Convert JSONL transcript to basic transcript with speaker labels."""
    segments = (json.loads(seg) for seg in jsonl.split('\n'))
    transcript = "\n".join(seg_to_txt(segment)
                            for segment in segments)
    return transcript
