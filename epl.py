import qrcode
from PIL import Image
from config import PRINTER_DEV, LABEL_WIDTH_PX, LABEL_HEIGHT_PX, LABEL_GAP_DOTS


def _qr_bitmap(text: str, size_px: int = 96) -> tuple[bytes, int, int]:
    """Generate QR code as raw 1-bit bitmap for EPL GW command."""
    img = qrcode.make(text).resize((size_px, size_px), Image.NEAREST).convert('1')
    w, h = img.size
    # size_px must be multiple of 8 for clean byte alignment
    assert w % 8 == 0, f"QR width {w} not multiple of 8"
    pixels = list(img.getdata())
    raw = bytearray()
    for row in range(h):
        for col in range(0, w, 8):
            byte = 0
            for bit in range(8):
                idx = row * w + col + bit
                if idx < len(pixels) and pixels[idx] == 0:  # 0 = black in mode '1'
                    byte |= (1 << (7 - bit))
            raw.append(byte)
    return bytes(raw), w, h


def _t(text: str) -> bytes:
    """Encode EPL text line as cp1251 bytes (supports Cyrillic)."""
    return (text + "\n").encode('cp1251')


def print_label(data: dict) -> None:
    order_number = data.get('order_number') or ''
    order_title  = data.get('order_title',  '')
    profile_code = data.get('profile_code', '')
    profile_name = data.get('profile_name', '')
    length       = data.get('length', 0)
    color        = data.get('color')        or ''
    section_path = data.get('section_path') or ''

    qr_parts = [
        f"№{order_number}" if order_number else "",
        order_title,
        f"{profile_name} {profile_code}".strip(),
        f"{length}мм",
        color,
        section_path,
    ]
    qr_text = " | ".join(p for p in qr_parts if p)
    qr_bytes, qr_w, qr_h = _qr_bitmap(qr_text, size_px=96)

    cmd = bytearray()
    cmd += b"N\n"                                                       # clear buffer
    cmd += f"q{LABEL_WIDTH_PX}\n".encode('ascii')                       # label width
    cmd += f"Q{LABEL_HEIGHT_PX},{LABEL_GAP_DOTS}\n".encode('ascii')     # label height + gap

    # Line 1: order number + title
    header = f"#{order_number}  {order_title}" if order_number else order_title
    cmd += _t(f'A10,10,0,2,1,1,N,"{header[:30]}"')

    # Line 2: profile name (large)
    cmd += _t(f'A10,45,0,3,1,1,N,"{profile_name}"')

    # Line 3: profile code
    cmd += _t(f'A10,80,0,2,1,1,N,"{profile_code}"')

    # Line 4: length — biggest font, most important field
    cmd += _t(f'A10,110,0,4,1,1,N,"{length} mm"')

    y = 158
    # Line 5: color (optional)
    if color:
        cmd += _t(f'A10,{y},0,2,1,1,N,"{color}"')
        y += 35

    # Line 6: section path (optional, small font)
    if section_path:
        cmd += _t(f'A10,{y},0,1,1,1,N,"{section_path}"')

    # QR code — bottom-right corner
    # GW format: GWx,y,width_in_bytes,height\n<raw binary>
    qr_x = LABEL_WIDTH_PX - qr_w - 8
    qr_y = LABEL_HEIGHT_PX - qr_h - 8
    cmd += f"GW{qr_x},{qr_y},{qr_w // 8},{qr_h}\n".encode('ascii')
    cmd += qr_bytes  # raw binary — NOT hex, NOT encoded as text

    cmd += b"P1\n"  # print 1 label

    with open(PRINTER_DEV, 'wb') as f:
        f.write(bytes(cmd))
