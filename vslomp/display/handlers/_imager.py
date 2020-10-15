# type:ignore

from typing import NamedTuple, Optional, Union, Tuple
from PIL import Image, ImageDraw

from cmdq.cmdproc import InvalidDataError  # type:ignore


class ConvertData(NamedTuple):
    img: Image.Image
    mode: Optional[str]
    dither: Optional[int]


class EnsureSizeData(NamedTuple):
    img: Image.Image
    size: Tuple[int, int]
    fill: int


DataType = Optional[Union[str, ConvertData, EnsureSizeData]]
ReturnType = Optional[Image.Image]


def cmd_load_file(data: DataType) -> ReturnType:
    return Image.open(data)  # type:ignore


def cmd_convert(data: DataType) -> ReturnType:
    if isinstance(data, ConvertData):
        return data.img.convert(mode=data.mode, dither=data.dither)

    raise InvalidDataError(type(data))


def cmd_ensure_size(data: DataType) -> ReturnType:
    if not isinstance(data, EnsureSizeData):
        raise InvalidDataError(type(data))

    img = data.img
    img.thumbnail(data.size, resample=Image.ANTIALIAS)

    img_w, img_h = img.size
    des_w, des_h = data.size
    if img_w < des_w or img_h < des_h:
        bg = Image.new(img.mode, data.size, 0)
        box_tlw = (des_w - img_w) // 2
        box_tlh = (des_h - img_h) // 2
        bg.paste(img, (max(0, box_tlw), max(0, box_tlh)))
        return bg
    else:
        return img


def cmd_get_demo(data: DataType) -> ReturnType:
    # font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
    # font18 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 18)

    # Drawing on the Horizontal image
    # logging.info("1.Drawing on the Horizontal image...")
    Himage = Image.new("1", (800, 480), 255)  # 255: clear the frame
    draw = ImageDraw.Draw(Himage)
    # draw.text((10, 0), 'hello world', font = font24, fill = 0)
    # draw.text((10, 20), '7.5inch e-Paper', font = font24, fill = 0)
    # draw.text((150, 0), u'微雪电子', font = font24, fill = 0)
    draw.line((20, 50, 70, 100), fill=0)
    draw.line((70, 50, 20, 100), fill=0)
    draw.rectangle((20, 50, 70, 100), outline=0)
    draw.line((165, 50, 165, 100), fill=0)
    draw.line((140, 75, 190, 75), fill=0)
    draw.arc((140, 50, 190, 100), 0, 360, fill=0)
    draw.rectangle((80, 50, 130, 100), fill=0)
    draw.chord((200, 50, 250, 100), 0, 360, fill=0)

    return Himage
