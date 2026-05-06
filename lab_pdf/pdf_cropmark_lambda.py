"""
Lab: PDF 재단선(크롭마크) 추가 — AWS Lambda 버전
=================================================
S3 이벤트 트리거로 실행되며, 입력 PDF를 460×318mm 캔버스에
중앙 배치하고 크롭마크를 추가한 뒤 결과를 S3에 업로드합니다.

Lambda 핸들러: lambda_handler(event, context)
로컬 CLI 사용법:
    python pdf_cropmark_lambda.py <input.pdf> <output.pdf>
"""

import io
import os
import tempfile

import fitz
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# === 상수 ===
TRIM_W = 460 * mm   # 재단 너비
TRIM_H = 318 * mm   # 재단 높이
CROP_LEN = 5 * mm   # 크롭마크 선 길이


# === 크롭마크 그리기 ===
def draw_cropmarks(c):
    """캔버스 c 위에 크롭마크(재단선)를 그립니다."""
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)

    left, right = 0, TRIM_W
    bottom, top = 0, TRIM_H
    mid_x, mid_y = TRIM_W / 2, TRIM_H / 2

    # --- 모서리 L자 ---
    c.line(left, bottom, left + CROP_LEN, bottom)
    c.line(left, bottom, left, bottom + CROP_LEN)
    c.line(right, bottom, right - CROP_LEN, bottom)
    c.line(right, bottom, right, bottom + CROP_LEN)
    c.line(left, top, left + CROP_LEN, top)
    c.line(left, top, left, top - CROP_LEN)
    c.line(right, top, right - CROP_LEN, top)
    c.line(right, top, right, top - CROP_LEN)

    # --- 네 변 중앙 ---
    c.line(mid_x, top, mid_x, top - CROP_LEN)
    c.line(mid_x, bottom, mid_x, bottom + CROP_LEN)
    c.line(left, mid_y, left + CROP_LEN, mid_y)
    c.line(right, mid_y, right - CROP_LEN, mid_y)


# === 핵심 변환 ===
def resize_with_cropmarks(input_pdf, output_pdf):
    """
    input_pdf 를 460×318mm 캔버스에 맞게 조정하고 크롭마크를 추가합니다.
    결과는 output_pdf 경로에 저장됩니다.
    """
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    doc = fitz.open(input_pdf)

    for i, page in enumerate(reader.pages):
        orig_w = float(page.mediabox.width)
        orig_h = float(page.mediabox.height)

        if orig_w < TRIM_W and orig_h < TRIM_H:
            scale = min(TRIM_W / orig_w, TRIM_H / orig_h)
        else:
            scale = 1.0

        new_w, new_h = orig_w * scale, orig_h * scale
        temp_pdf = os.path.join(tempfile.gettempdir(), f"temp_{i}.pdf")

        c = canvas.Canvas(temp_pdf, pagesize=(TRIM_W, TRIM_H))
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(scale, scale))
        img = ImageReader(io.BytesIO(pix.tobytes("png")))

        offset_x = (TRIM_W - new_w) / 2
        offset_y = (TRIM_H - new_h) / 2
        c.drawImage(img, offset_x, offset_y, new_w, new_h, mask="auto")

        draw_cropmarks(c)
        c.showPage()
        c.save()

        temp_reader = PdfReader(temp_pdf)
        writer.add_page(temp_reader.pages[0])

    with open(output_pdf, "wb") as f:
        writer.write(f)


# === AWS Lambda 핸들러 ===
def lambda_handler(event, context):
    """
    S3 트리거 기반 Lambda 핸들러.
    업로드된 PDF에 크롭마크를 추가하고 *_work.pdf 로 저장합니다.
    """
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


# === 로컬 실행 ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python pdf_cropmark_lambda.py <input.pdf> <output.pdf>")
        sys.exit(1)

    resize_with_cropmarks(sys.argv[1], sys.argv[2])
    print(f"✅ 저장 완료: {sys.argv[2]}")
