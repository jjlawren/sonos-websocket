# sonos-websocket
Async Python library to communicate with Sonos devices over websockets.

## Example use: Audio Clips
Sonos audio clip functionality will overlay playback of the provided media on top of currently playing music. The music playback volume will be lowered while the audio clip is played and automatically returned to its original level when finished. This feature is especially useful for text-to-speech and alert sounds.

The below shows how to run `sonos-websocket` as a script:
```
python -m sonos_websocket \
    --ip_addr 192.168.1.88 \
    --uri https://freetestdata.com/wp-content/uploads/2021/09/Free_Test_Data_100KB_MP3.mp3 \
    --volume 15
```
Basic use of how to integrate the package can be found [here](https://github.com/jjlawren/sonos-websocket/blob/main/sonos_websocket/__main__.py).
