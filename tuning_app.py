import copy

import streamlit as st
from PIL import Image

from plate_recognition import draw_bb, recognition_api


def sidebar():
    sdk_url = st.sidebar.text_input('SDK URL', 'http://localhost:8080')
    threshold_d = st.sidebar.number_input('Detection Threshold',
                                          value=.2,
                                          min_value=0.,
                                          max_value=1.)
    threshold_o = st.sidebar.number_input('OCR Threshold',
                                          value=.6,
                                          min_value=0.,
                                          max_value=1.)
    regions = st.sidebar.text_input('Regions').split()
    fast = st.sidebar.checkbox('Fast Mode')
    mmc = st.sidebar.checkbox('MMC')
    redaction = st.sidebar.checkbox('Redaction')
    config = dict(threshold_d=threshold_d, threshold_o=threshold_o)
    if fast:
        config['mode'] = 'fast'
    if redaction:
        config['mode'] = 'redaction'
    return config, regions, mmc, sdk_url


def max_width():
    max_width_str = f"max-width: 2000px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )


@st.cache
def recognition(my_file, regions, sdk_url, mmc, config):
    with st.spinner('Processing'):
        res = recognition_api(my_file,
                              regions=regions,
                              sdk_url=sdk_url,
                              mmc=mmc,
                              config=config)
    return res


def main():
    max_width()
    config, regions, mmc, sdk_url = sidebar()
    my_file = st.file_uploader('Pick an image',
                               type=['jpg', 'png', 'jpeg', 'gif', 'bmp'])
    if not my_file:
        return
    image = Image.open(my_file).convert('RGB')
    res = recognition(my_file, regions, sdk_url, mmc, config)
    res = copy.deepcopy(res)
    vehicles = []
    for result in res['results']:
        if 'vehicle' in result:
            details = []
            model_make = result.get('model_make')
            if model_make:
                details.append(
                    '{make} {model} {score:.2f}'.format(**model_make[0]))
            color = result.get('color')
            if color:
                details.append('{color} {score:.2f}'.format(**color[0]))
            result['vehicle']['details'] = ', '.join(details)
            vehicles.append(result['vehicle'])
    overlay = st.checkbox('Show Overlay', value=True)
    if overlay:
        draw_bb(
            image, vehicles, None, lambda vehicle: '%s (%s) [%s]' % (vehicle[
                'type'], vehicle['score'], vehicle['details']))
        draw_bb(
            image, res['results'],
            None, lambda result: '%s [%s] (%s, %s)' % (result['plate'].upper(
            ), result['region']['code'], result['score'], result['dscore']))
    st.image(image, width=image.width)
    res


if __name__ == "__main__":
    main()
