import io
import base64
from PIL import Image, ImageDraw, ImageFont
import qrcode

DPI = 203
FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def mm_to_px(mm: float) -> int:
    return int(float(mm) * DPI / 25.4)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT_BOLD_PATH if bold else FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def render_label(layout: dict) -> Image.Image:
    w = mm_to_px(layout.get('width_mm', 40))
    h = mm_to_px(layout.get('height_mm', 57))
    img = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(img)

    for el in layout.get('elements', []):
        x, y = el.get('x', 0), el.get('y', 0)
        t = el.get('type')

        if t == 'text':
            font = _font(el.get('font_size', 24), el.get('bold', False))
            draw.text((x, y), el.get('text', ''), fill='black', font=font)

        elif t == 'qr':
            text = el.get('text', '')
            size = el.get('size', 96)
            # Round size up to multiple of 8 for EPL bitmap alignment
            size = ((size + 7) // 8) * 8
            qr_img = qrcode.make(text).resize((size, size), Image.NEAREST).convert('RGB')
            img.paste(qr_img, (x, y))

        elif t == 'image':
            raw = base64.b64decode(el['data'])
            el_img = Image.open(io.BytesIO(raw)).convert('RGB')
            w_el = el.get('width', el_img.width)
            h_el = el.get('height', el_img.height)
            el_img = el_img.resize((w_el, h_el), Image.LANCZOS)
            img.paste(el_img, (x, y))

    return img


def render_to_png_bytes(layout: dict, scale: int = 3) -> bytes:
    img = render_label(layout)
    preview = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    buf = io.BytesIO()
    preview.save(buf, 'PNG')
    return buf.getvalue()


def render_to_epl(layout: dict) -> bytes:
    from config import LABEL_GAP_DOTS
    img = render_label(layout)
    w_px = img.width
    h_px = img.height
    w_bytes = (w_px + 7) // 8

    # Convert to grayscale and threshold without dithering
    gray = img.convert('L')
    pixels = list(gray.getdata())

    bitmap = bytearray()
    for row in range(h_px):
        for byte_idx in range(w_bytes):
            col = byte_idx * 8
            byte = 0
            for bit in range(8):
                px = col + bit
                if px < w_px:
                    idx = row * w_px + px
                    if idx < len(pixels) and pixels[idx] < 128:  # dark pixel = print dot
                        byte |= (1 << (7 - bit))
            bitmap.append(byte)

    cmd = bytearray()
    cmd += b"N\n"
    cmd += f"q{w_px}\n".encode('ascii')
    cmd += f"Q{h_px},{LABEL_GAP_DOTS}\n".encode('ascii')
    cmd += f"GW0,0,{w_bytes},{h_px}\n".encode('ascii')
    cmd += bytes(bitmap)
    cmd += b"P1\n"
    return bytes(cmd)
