#
# file        pymain.py
# brief       Application (Python Version)
# author      Panasonic
# date        2021-01-08
# version     1.0
# Copyright    (C) COPYRIGHT 2021 Panasonic Corporation
#              (C) COPYRIGHT 2022 i-PRO Co., Ltd.
#

# import numpy as np;
# import cv2;
# import threading;
import hello
import libAdamApiPython

# if print() output is delay, enalbe the following lines.
# sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
# sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

loop = None
id = -1
isH26 = False
isJpeg = False
isAudio = False
addInfo = ""


def stopCB():
    global loop
    print("Stop callback")
    loop.exit()


def httpCB(reqType, reqData):
    print("HTTP callback: type=%d" % reqType)
    body = b"body"
    header = "header"
    return (header, body)


def appPrefCB(prefTuple):

    global id
    global isH26
    global isJpeg
    global isAudio
    global addInfo

    libAdamApiPython.adam_lock_appPref()

    if prefTuple == "ID":
        id = libAdamApiPython.adam_get_appPref("ID")
    elif prefTuple == "H.26X":
        isH26 = libAdamApiPython.adam_get_appPref("H.26X")
    elif prefTuple == "JPEG":
        isJpeg = libAdamApiPython.adam_get_appPref("JPEG")
    elif prefTuple == "Audio":
        isAudio = libAdamApiPython.adam_get_appPref("Audio")
    elif prefTuple == "Additional Info":
        addInfo = libAdamApiPython.adam_get_appPref("Additional Info")
    else:
        print("Undefined AppPrefName: %s" % prefTuple)

    libAdamApiPython.adam_unlock_appPref()


def loadPref():
    global id
    global isH26
    global isJpeg
    global isAudio
    global addInfo

    libAdamApiPython.adam_lock_appPref()

    id = libAdamApiPython.adam_get_appPref("ID")  # int
    isH26 = libAdamApiPython.adam_get_appPref("H.26X")  # bool
    isJpeg = libAdamApiPython.adam_get_appPref("JPEG")  # bool
    isAudio = libAdamApiPython.adam_get_appPref("Audio")  # bool
    addInfo = memoryview(
        libAdamApiPython.adam_get_appPref("Additional Info").encode()
    )  # char

    libAdamApiPython.adam_unlock_appPref()


def procPref():
    global id
    global isH26
    global isJpeg
    global isAudio
    global addInfo

    len(addInfo)
    stream = 0
    if isH26:
        stream += libAdamApiPython.ADAM_STREAM_H26X
    if isJpeg:
        stream += libAdamApiPython.ADAM_STREAM_JPEG
    if isAudio:
        stream += libAdamApiPython.ADAM_STREAM_AUDIO

    level = libAdamApiPython.ADAM_LV_INF
    libAdamApiPython.adam_debug_print(
        level, ("id=%d, addInfo=%s, stream=%d" % (id, addInfo, stream))
    )

    libAdamApiPython.adam_additional_info_set(id, addInfo, stream)


def startProcessing():
    global loop

    loop = libAdamApiPython.adamEventloop()

    loadPref()
    procPref()

    loop.dispatch()
    # 	time.sleep(2)
    del loop
    print("Finish: Process")


if __name__ == "__main__":
    print("Start: main thread")
    # 	adam.setPrintLevel(0xffffffff)

    hello.hello()

    libAdamApiPython.adam_set_stop_callback(stopCB)
    libAdamApiPython.adam_set_http_callback(httpCB)
    libAdamApiPython.adam_set_appPref_callback(appPrefCB)

    # Case of executing image processing in same thread.
    startProcessing()

    print("Finish: main thread")
