import fitz
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from PyPDF2 import PdfReader, PdfWriter
import io, os, tempfile
from reportlab.lib.utils import ImageReader

# 최종 재단 사이즈
TRIM_W = 460 * mm
TRIM_H = 318 * mm
CROP_LEN = 5 * mm  # 선 길이 (5mm)

def draw_cropmarks(c):
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)
    left, right = 0, TRIM_W
    bottom, top = 0, TRIM_H
    mid_x, mid_y = TRIM_W / 2, TRIM_H / 2

    # 모서리
    c.line(left, bottom, left + CROP_LEN, bottom)
    c.line(left, bottom, left, bottom + CROP_LEN)
    c.line(right, bottom, right - CROP_LEN, bottom)
    c.line(right, bottom, right, bottom + CROP_LEN)
    c.line(left, top, left + CROP_LEN, top)
    c.line(left, top, left, top - CROP_LEN)
    c.line(right, top, right - CROP_LEN, top)
    c.line(right, top, right, top - CROP_LEN)

    # 중앙
    c.line(mid_x, top, mid_x, top - CROP_LEN)
    c.line(mid_x, bottom, mid_x, bottom + CROP_LEN)
    c.line(left, mid_y, left + CROP_LEN, mid_y)
    c.line(right, mid_y, right - CROP_LEN, mid_y)

def resize_with_cropmarks(input_pdf, output_pdf):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    doc = fitz.open(input_pdf)

    for i, page in enumerate(reader.pages):
        orig_w = float(page.mediabox.width)
        orig_h = float(page.mediabox.height)

        if orig_w < TRIM_W and orig_h < TRIM_H:
            scale_w = TRIM_W / orig_w
            scale_h = TRIM_H / orig_h
            scale = min(scale_w, scale_h)
        else:
            scale = 1.0

        new_w, new_h = orig_w * scale, orig_h * scale
        temp_pdf = os.path.join(tempfile.gettempdir(), f"temp_{i}.pdf")

        c = canvas.Canvas(temp_pdf, pagesize=(TRIM_W, TRIM_H))
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(scale, scale))
        imgdata = pix.tobytes("png")
        img = ImageReader(io.BytesIO(imgdata))

        offset_x = (TRIM_W - new_w) / 2
        offset_y = (TRIM_H - new_h) / 2
        c.drawImage(img, offset_x, offset_y, new_w, new_h, mask='auto')

        draw_cropmarks(c)
        c.showPage()
        c.save()

        temp_reader = PdfReader(temp_pdf)
        writer.add_page(temp_reader.pages[0])

    with open(output_pdf, "wb") as f:
        writer.write(f)

def lambda_handler(event, context):
    # S3 트리거 기반 예시
    import boto3
    s3 = boto3.client("s3")

    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]

    input_path = os.path.join(tempfile.gettempdir(), "input.pdf")
    output_path = os.path.join(tempfile.gettempdir(), "output.pdf")

    s3.download_file(bucket, key, input_path)
    resize_with_cropmarks(input_path, output_path)
    s3.upload_file(output_path, bucket, key.replace(".pdf", "_work.pdf"))

    return {"status": "done", "bucket": bucket, "key": key}
