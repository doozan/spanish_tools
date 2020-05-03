import hashlib
import base64
import argparse
import os
import boto3
from botocore.errorfactory import ClientError

polly = boto3.Session(region_name='us-west-2').client('polly')

def get_filename(voice, phrase):
    key = voice + ":" + phrase

    hash_object = hashlib.sha1(bytes(key.lower(), "utf-8"))
    filename = str(base64.b32encode(hash_object.digest()), "utf-8")
    filename += ".mp3"

    return filename


def text_to_mp3(voice, phrase, filename):
    engine = "neural" if voice == "Lupa" else "standard"
    response = polly.synthesize_speech(
                Engine=engine,
                VoiceId=voice,
                OutputFormat='mp3',
                Text = phrase)

    file = open(filename, 'wb')
    file.write(response['AudioStream'].read())
    file.close()


def get_speech(voice, phrase, path):
    if not voice:
        raise ValueError("No voice specified")

    if not phrase:
        raise ValueError("No phrase specified")

    if not path:
        raise ValueError("No path specified")

    if not os.path.isdir(path):
        raise ValueError(f"Speech directory does not exist: {path}")

    filename = get_filename(voice, phrase)
    destfile = path + "/" + filename

    if not os.path.isfile(destfile):
        print("Generating {voice}: {phrase}")
        text_to_mp3(voice, phrase, destfile)

    return filename
