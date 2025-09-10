import fitz
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from PyPDF2 import PdfReader, PdfWriter
import io, os
from reportlab.lib.utils import ImageReader

# 최종 재단 사이즈
TRIM_W = 460 * mm
TRIM_H = 318 * mm

# 크롭마크 설정
CROP_LEN = 5 * mm   # 선 길이 (5mm)

def draw_cropmarks(c):
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)

    left, right = 0, TRIM_W
    bottom, top = 0, TRIM_H
    mid_x, mid_y = TRIM_W / 2, TRIM_H / 2

    # --- 모서리 L자 ---
    # 좌하
    c.line(left, bottom, left + CROP_LEN, bottom)   # 가로
    c.line(left, bottom, left, bottom + CROP_LEN)   # 세로
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
    # 위
    c.line(mid_x, top, mid_x, top - CROP_LEN)
    # 아래
    c.line(mid_x, bottom, mid_x, bottom + CROP_LEN)
    # 좌
    c.line(left, mid_y, left + CROP_LEN, mid_y)
    # 우
    c.line(right, mid_y, right - CROP_LEN, mid_y)


def resize_with_cropmarks(input_pdf):
    base, ext = os.path.splitext(input_pdf)
    output_pdf = f"{base}_work.pdf"

    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    doc = fitz.open(input_pdf)

    for i, page in enumerate(reader.pages):
        orig_w = float(page.mediabox.width)
        orig_h = float(page.mediabox.height)

        # 작은 경우만 확대
        if orig_w < TRIM_W and orig_h < TRIM_H:
            scale_w = TRIM_W / orig_w
            scale_h = TRIM_H / orig_h
            scale = min(scale_w, scale_h)
        else:
            scale = 1.0

        new_w = orig_w * scale
        new_h = orig_h * scale

        # 캔버스 (페이지 크기 고정: 460x318mm)
        c = canvas.Canvas("temp.pdf", pagesize=(TRIM_W, TRIM_H))

        # 원본 PDF → 이미지 렌더링
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(scale, scale))
        imgdata = pix.tobytes("png")
        img = ImageReader(io.BytesIO(imgdata))

        # 중앙 배치
        offset_x = (TRIM_W - new_w) / 2
        offset_y = (TRIM_H - new_h) / 2
        c.drawImage(img, offset_x, offset_y, new_w, new_h, mask='auto')

        # 재단선 (크롭마크) 표시
        draw_cropmarks(c)

        c.showPage()
        c.save()

        # temp.pdf → 최종 PDF에 추가
        temp_reader = PdfReader("temp.pdf")
        writer.add_page(temp_reader.pages[0])

    with open(output_pdf, "wb") as f:
        writer.write(f)

    print(f"✅ 저장 완료: {output_pdf}")


if __name__ == "__main__":
    filename = input("PDF 파일명을 입력하세요: ").strip()
    resize_with_cropmarks(filename)
