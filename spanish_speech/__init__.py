import hashlib
import base64
import argparse
import os
import boto3
from botocore.errorfactory import ClientError

#_FEMALE1 = "Lupe"
_FEMALE1 = "Penelope"
_FEMALE2 = "Penelope"
_MALE1   = "Miguel"

polly = boto3.Session(region_name='us-west-2').client('polly')

def get_phrase(word, pos, noun_type):
    voice = ""
    phrase = ""

    if noun_type:
        if noun_type == "f":
            voice = _FEMALE2
            phrase = "la " + word
        elif noun_type == "fp":
            voice = _FEMALE2
            phrase = "las " + word
        elif noun_type == "f-el":
            voice = _FEMALE2
            phrase = "el " + word
        elif noun_type == "m-f":
            voice = _FEMALE1
            phrase = "la " + word + ". el " + word
        elif noun_type == "m":
            voice = _MALE1
            phrase = "el " + word
        elif noun_type == "mf":
            voice = _MALE1
            phrase = "el " + word + ". la " + word
        elif noun_type == "mp":
            voice = _MALE1
            phrase = "los " + word
        elif noun_type == "m/f":
            voice = _MALE1
            phrase = "la " + word[:-1]+"a. " + "el " + word
        else:
            print("Unknown noun type", noun_type)
            exit()

    else:
        voice = _FEMALE1
        phrase = word

    return { "voice": voice, "phrase": phrase }


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


def get_speech(word, pos, noun_type, path):
    res = get_phrase(word, pos, noun_type)

    if not res:
        print("Error", word, pos, noun_type, path)
        exit()

    filename = get_filename(res['voice'], res['phrase'])
    destfile = path + "/" + filename

    if not os.path.isfile(destfile):
        text_to_mp3(res['voice'], res['phrase'], destfile)

    return {
        'phrase': res['phrase'],
        'filename': filename
    }

