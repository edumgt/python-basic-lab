"""
Lab: PDF 재단선(크롭마크) 추가 — 로컬 버전
=============================================
입력 PDF를 460×318mm 캔버스에 중앙 배치하고
네 모서리와 네 변 중앙에 크롭마크(재단선)를 그려
새 PDF(*_work.pdf)로 저장합니다.

사용법:
    python pdf_cropmark.py
    → 실행 후 파일명 입력 프롬프트가 표시됩니다.
"""

import io
import os

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
    # 좌하
    c.line(left, bottom, left + CROP_LEN, bottom)
    c.line(left, bottom, left, bottom + CROP_LEN)
    # 우하
    c.line(right, bottom, right - CROP_LEN, bottom)
    c.line(right, bottom, right, bottom + CROP_LEN)
    # 좌상
    c.line(left, top, left + CROP_LEN, top)
    c.line(left, top, left, top - CROP_LEN)
    # 우상
    c.line(right, top, right - CROP_LEN, top)
    c.line(right, top, right, top - CROP_LEN)

    # --- 네 변 중앙 ---
    c.line(mid_x, top, mid_x, top - CROP_LEN)       # 위
    c.line(mid_x, bottom, mid_x, bottom + CROP_LEN)  # 아래
    c.line(left, mid_y, left + CROP_LEN, mid_y)      # 좌
    c.line(right, mid_y, right - CROP_LEN, mid_y)    # 우


# === 핵심 변환 ===
def resize_with_cropmarks(input_pdf):
    """
    input_pdf 를 460×318mm 캔버스에 맞게 조정하고 크롭마크를 추가합니다.
    결과는 <원본명>_work.pdf 로 저장됩니다.
    """
    base, _ = os.path.splitext(input_pdf)
    output_pdf = f"{base}_work.pdf"

    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    doc = fitz.open(input_pdf)

    for i, page in enumerate(reader.pages):
        orig_w = float(page.mediabox.width)
        orig_h = float(page.mediabox.height)

        # 원본이 캔버스보다 작을 때만 확대
        if orig_w < TRIM_W and orig_h < TRIM_H:
            scale = min(TRIM_W / orig_w, TRIM_H / orig_h)
        else:
            scale = 1.0

        new_w = orig_w * scale
        new_h = orig_h * scale

        # 임시 PDF 캔버스 (460×318mm 고정)
        temp_path = f"_temp_page_{i}.pdf"
        c = canvas.Canvas(temp_path, pagesize=(TRIM_W, TRIM_H))

        # 원본 페이지 → 이미지 렌더링
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(scale, scale))
        img = ImageReader(io.BytesIO(pix.tobytes("png")))

        # 중앙 배치
        offset_x = (TRIM_W - new_w) / 2
        offset_y = (TRIM_H - new_h) / 2
        c.drawImage(img, offset_x, offset_y, new_w, new_h, mask="auto")

        draw_cropmarks(c)
        c.showPage()
        c.save()

        temp_reader = PdfReader(temp_path)
        writer.add_page(temp_reader.pages[0])
        os.remove(temp_path)

    with open(output_pdf, "wb") as f:
        writer.write(f)

    print(f"✅ 저장 완료: {output_pdf}")


# === 진입점 ===
if __name__ == "__main__":
    filename = input("PDF 파일명을 입력하세요: ").strip()
    resize_with_cropmarks(filename)
