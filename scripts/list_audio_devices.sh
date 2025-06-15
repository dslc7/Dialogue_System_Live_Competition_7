#!/bin/bash

if [ ! -d "venv" ]; then
    python3 -m venv venv
    . venv/bin/activate && pip install pyaudio
fi

venv/bin/python3 -c "import pyaudio; audio = pyaudio.PyAudio(); info = [str(audio.get_device_info_by_index(i)) for i in range(audio.get_device_count())]; print('\n'.join(info))"