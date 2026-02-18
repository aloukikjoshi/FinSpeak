# Demo Assets

This directory contains demo audio files for testing FinSpeak.

## Generate Sample Audio

You can generate sample audio files using the notebook:
- `notebooks/01_stt_demo.ipynb`

Or using the Python script below:

```python
from gtts import gTTS

queries = [
    "What is the current NAV of Vanguard S&P 500 Fund?",
    "Show me six month returns for Fidelity Growth Fund",
    "How has Wellington Fund performed over one year?"
]

for i, query in enumerate(queries, 1):
    tts = gTTS(text=query, lang='en', slow=False)
    tts.save(f'query_{i}.mp3')
    print(f"Generated query_{i}.mp3")
```

## Available Demo Files

Demo audio files can be generated using the above script or the Jupyter notebook.
