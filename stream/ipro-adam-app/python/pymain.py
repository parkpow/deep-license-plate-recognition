# import threading;

# debug
import traceback

# import numpy as np;
# import cv2;
import libAdamApiPython

# if print() output is delay, enalbe the following lines.
# sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
# sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)


def debugDbg(str):
    # libAdamApiPython.adam_debug_print(libAdamApiPython.ADAM_LV_DBG, "[DBG] {}".format(str))
    print(f"[DBG] {str}")


def debugErr(str):
    # libAdamApiPython.adam_debug_print(libAdamApiPython.ADAM_LV_ERR, "[ERR] {}".format(str))
    print(f"[ERR] {str}")


loop = None
license_key = memoryview(b"")
token = memoryview(b"")
stream_log_level = 0
enum_values = ["10", "20", "30", "40", "50"]


# Store pref names as constants
LICENSE_KEY_PREF = "LICENSE_KEY"
TOKEN_PREF = "TOKEN"
LOGGING_PREF = "LOGGING"


def stopCB():
    global loop
    print("Stop callback")
    loop.exit()


ADAM_HTTP_REQ_TYPE_GET = 0
ADAM_HTTP_REQ_TYPE_POST = 1


def create_respone_header(body, status=200):
    content_length = len(body)
    assert len(str(status)) == 3, "status code must be 3 digits"
    header = f"HTTP/1.1 {status} OK\r\nContent-Type: text/html\r\nContent-Length: {content_length}\r\n"

    return header


def write_env_file(token, license_key, log_level):
    debugDbg("Writing stream credentials to /ai_data/env-file.ini")

    env_vars = {
        "TOKEN": token,
        "LICENSE_KEY": license_key,
        "LOGGING": enum_values[log_level],
    }

    # Write or overwrite environment variables to ini file
    env_file_path = "/ai_data/env-file.ini"
    with open(env_file_path, "w") as env_file:
        env_file.write("[DEFAULT]\n")
        for key, value in env_vars.items():
            env_file.write(f"{key}={value}\n")


def httpCB(reqType, reqData):
    global license_key
    global token
    global stream_log_level

    print("HTTP callback: type=%d" % reqType)
    debugDbg("HTTP callback: reqType=%d" % reqType)

    # body = b'body'
    # header = "header"
    # return (header, body)

    # Html key words to be replaced
    template_literals = [
        "@pInstallID",
        "@LICENSE_KEY_PREF",
        "@TOKEN_PREF",
        "@LOGGING_PREF_10",
        "@LOGGING_PREF_20",
        "@LOGGING_PREF_30",
        "@LOGGING_PREF_40",
        "@LOGGING_PREF_50",
    ]

    try:
        # get data directory
        appPath = libAdamApiPython.adam_get_app_data_dir_path()
        with open(f"{appPath}/index.html") as fp:
            htmlData = fp.read()

        print("reqType:%d" % reqType)
        debugDbg("call httpCB: reqType=%d" % reqType)
        if reqType == ADAM_HTTP_REQ_TYPE_GET:
            debugDbg("Show html")
            # load AppPref
            loadPref()
        elif reqType == ADAM_HTTP_REQ_TYPE_POST:
            debugDbg("Edit html")
            # set AppPref
            setPref(reqData.decode("utf-8"))
        else:
            debugErr("call httpCB: reqType=%d" % reqType)

        # set AppPref parameter
        context = []
        # Get App Install ID
        install_id = "%08X" % libAdamApiPython.InstallId
        context.append(install_id)
        context.append(license_key.tobytes().decode("utf-8"))
        context.append(token.tobytes().decode("utf-8"))
        context.extend(get_stream_log_level_context(stream_log_level))

        debugDbg(f"Context: {context}")

        # replace parameters in html
        cnt = 0
        for keywd in template_literals:
            htmlData = htmlData.replace(keywd, context[cnt])
            cnt += 1
        header = create_respone_header(htmlData)

    except Exception as e:
        debugErr(f"httpCB Exception: {e}")
        htmlData = f"Server Error: {traceback.format_exc()}"
        header = create_respone_header(htmlData, 500)

    body = bytes(htmlData, "utf-8")
    return header, body


def get_stream_log_level_context(stream_log_level: int) -> list:
    """
    Generate selected attribute for stream log level options.
    """
    selected = 'selected="selected"'
    unselected = ""

    context = []

    for i, _value in enumerate(enum_values):
        if stream_log_level == i:
            context.append(selected)
        else:
            context.append(unselected)

    return context


def appPrefCB(prefTuple):
    global license_key
    global token
    global stream_log_level

    libAdamApiPython.adam_lock_appPref()

    if prefTuple == LICENSE_KEY_PREF:
        license_key = memoryview(
            libAdamApiPython.adam_get_appPref(LICENSE_KEY_PREF).encode()
        )
    elif prefTuple == TOKEN_PREF:
        token = memoryview(libAdamApiPython.adam_get_appPref(TOKEN_PREF).encode())

    elif prefTuple == LOGGING_PREF:
        stream_log_level = libAdamApiPython.adam_get_appPref(LOGGING_PREF)
    else:
        print("Undefined AppPrefName: %s" % prefTuple)

    libAdamApiPython.adam_unlock_appPref()


def loadPref():
    global license_key
    global token
    global stream_log_level

    libAdamApiPython.adam_lock_appPref()
    license_key = memoryview(
        libAdamApiPython.adam_get_appPref(LICENSE_KEY_PREF).encode()
    )
    token = memoryview(libAdamApiPython.adam_get_appPref(TOKEN_PREF).encode())
    stream_log_level = libAdamApiPython.adam_get_appPref(LOGGING_PREF)

    libAdamApiPython.adam_unlock_appPref()

    debugDbg("loadPref adam_get_appPref")
    debugDbg(f"  license_key:{license_key}")
    debugDbg(f"  token:{token}")
    debugDbg(f"  stream_log_level :{stream_log_level}")

    libAdamApiPython.adam_debug_print(
        libAdamApiPython.ADAM_LV_INF,
        f"PLATEREC - license_key={license_key}, token={token}, stream_log_level={stream_log_level}",
    )

    if license_key and token:
        license_key_pref = license_key.tobytes().decode("utf-8")
        token_pref = token.tobytes().decode("utf-8")
        write_env_file(token_pref, license_key_pref, stream_log_level)


def setPref(pref_str):
    global license_key
    global token
    global stream_log_level

    debugDbg(f"Set Pref: {pref_str}")
    pref = pref_str.split(",")
    license_key_pref = pref[0]
    token_pref = pref[1]
    log_level_pref = pref[2]

    license_key = memoryview(license_key_pref.encode())
    token = memoryview(token_pref.encode())
    stream_log_level = enum_values.index(log_level_pref)

    libAdamApiPython.adam_lock_appPref()
    libAdamApiPython.adam_set_appPref({LICENSE_KEY_PREF: license_key_pref})
    libAdamApiPython.adam_set_appPref({TOKEN_PREF: token_pref})
    libAdamApiPython.adam_set_appPref({LOGGING_PREF: stream_log_level})
    libAdamApiPython.adam_unlock_appPref()

    debugDbg("setPref adam_set_appPref")
    debugDbg(f"  license_key:{license_key_pref}")
    debugDbg(f"  license_token:{token_pref}")
    debugDbg(f"  stream_log_level :{stream_log_level}")

    write_env_file(token_pref, license_key_pref, stream_log_level)


def startProcessing():
    global loop
    loop = libAdamApiPython.adamEventloop()
    loadPref()
    loop.dispatch()
    del loop
    print("Finish: Process")


if __name__ == "__main__":
    print("Start: main thread")
    # 	adam.setPrintLevel(0xffffffff)

    libAdamApiPython.adam_set_stop_callback(stopCB)
    libAdamApiPython.adam_set_http_callback(httpCB)
    libAdamApiPython.adam_set_appPref_callback(appPrefCB)

    # Case of executing image processing in same thread.
    startProcessing()

    print("Finish: main thread")
