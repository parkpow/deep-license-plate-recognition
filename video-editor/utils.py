import cv2
import numpy as np


def draw_bounding_box_on_image(
    image, ymin, xmin, ymax, xmax, display_str, color=(255, 234, 32), thickness=4
):
    (left, right, top, bottom) = (xmin, xmax, ymin, ymax)
    pts = np.array(
        [[left, top], [left, bottom], [right, bottom], [right, top]], np.int32
    )
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(image, [pts], True, color, thickness)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness_text = 2
    text_size, baseline = cv2.getTextSize(display_str, font, font_scale, thickness_text)
    text_width, text_height = text_size
    margin = np.ceil(0.2 * text_height)
    thickness_fill = -1
    start_point = (int(left - margin), int(top - text_height - 2 * margin))
    end_point = (int(left + text_width + 2 * margin), int(top))

    cv2.rectangle(image, start_point, end_point, color, thickness_fill)

    org = (int(left + margin), int(top - text_height + 3 * margin))
    cv2.putText(
        image,
        display_str,
        org,
        font,
        font_scale,
        (255, 255, 255),
        thickness_text,
        cv2.LINE_AA,
    )
