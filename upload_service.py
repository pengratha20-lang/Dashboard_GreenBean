import os
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime


def allowed_file(filename, allowed_extensions):
    return (
            '.' in filename and
            filename.rsplit('.', 1)[1].lower() in allowed_extensions
    )


def add_watermark(image, watermark_text="© Dashboard"):
    """Add a watermark text to the image"""
    try:
        img_with_watermark = image.copy()
        draw = ImageDraw.Draw(img_with_watermark, 'RGBA')

        img_width, img_height = img_with_watermark.size

        try:
            font_size = int(img_height / 15)
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding = 10
        x = img_width - text_width - padding
        y = img_height - text_height - padding

        draw.text((x, y), watermark_text, font=font, fill=(100, 100, 100, 200))
        
        return img_with_watermark
    except Exception as e:
        print(f"Warning: Could not add watermark: {e}")
        return image


def save_image(
        file,
        upload_folder,
        allowed_extensions,
        resize_to=(400, 400),
        thumb_size=(200, 200),
        watermark_text="© GreenBean"
):
    if not file or file.filename == '':
        return 'no file'

    if not allowed_file(file.filename, allowed_extensions):
        return 'invalid file'

    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
    filename_with_timestamp = timestamp + filename
    name_with_timestamp = timestamp + name

    original_path = os.path.join(upload_folder, filename_with_timestamp)
    resized_path = os.path.join(upload_folder, f"resized_{name_with_timestamp}{ext}")
    thumb_path = os.path.join(upload_folder, f"thumb_{name_with_timestamp}{ext}")

    file.save(original_path)

    image = Image.open(original_path)
    img_with_watermark = add_watermark(image, watermark_text)
    img_with_watermark.save(original_path)

    resized = image.copy()
    resized.thumbnail(resize_to)
    resized_with_watermark = add_watermark(resized, watermark_text)
    resized_with_watermark.save(resized_path)

    thumb = image.copy()
    thumb.thumbnail(thumb_size)
    thumb_with_watermark = add_watermark(thumb, watermark_text)
    thumb_with_watermark.save(thumb_path)

    return {
        "original": filename_with_timestamp,
        "resized": f"resized_{name_with_timestamp}{ext}",
        "thumbnail": f"thumb_{name_with_timestamp}{ext}"
    }
