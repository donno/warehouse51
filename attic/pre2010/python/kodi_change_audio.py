

"""
The goal is determine the current audio device and switch it between
HDMI and Analog

"""

import requests
import json

#Settings.GetSettingValue

proxies = {
  #"http": "http://localhost:8888/",
}


getAllSettings = {"jsonrpc":"2.0","method":"Settings.GetSettings","id":2, "params": {"level": "advanced"}}


# Set audio-device.

headers = {
  'Content-type': 'application/json',
  'Accept': 'application/json, text/javascript, */*; q=0.01',
}

#application/json

def getAudioDeviceValue():
  query = {
    "jsonrpc": "2.0",
    "id": 1,
    "method":"Settings.GetSettingValue",
    "params": {"setting": "audiooutput.audiodevice"},
  }

  r = requests.post(
    'http://openelec/jsonrpc',
    data=json.dumps(query),
    proxies=proxies,
    headers=headers,
  )
  return r.json()['result']['value']

def setAudioDeviceValue(newValue):
  query = {
    "jsonrpc": "2.0",
    "id": 1,
    "method":"Settings.SetSettingValue",
    "params": {
      "setting": "audiooutput.audiodevice",
      "value": newValue,
    },
  }

  r = requests.post(
    'http://openelec/jsonrpc',
    data=json.dumps(query),
    proxies=proxies,
    headers=headers,
  )
  return r.json()['result']

value = getAudioDeviceValue()
print value
if value == 'PI:Analogue':
  print setAudioDeviceValue('PI:HDMI')
elif value == 'PI:HDMI':
  print setAudioDeviceValue('PI:Analogue')
