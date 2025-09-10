import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from PyPDF2 import PdfReader, PdfWriter
import io, os
from reportlab.lib.utils import ImageReader

# 페이지 크기 (pt 단위)
TARGET_W = 460 * mm
TARGET_H = 318 * mm

# 크롭마크 길이 (5mm)
CROP_LEN = 5 * mm
# 재단선에서 바깥쪽 거리 (3mm)
CROP_OFFSET = 3 * mm

def draw_cropmarks(c):
    c.setStrokeColorRGB(0, 0, 0)  # 인쇄용 블랙
    c.setLineWidth(0.5)

    mid_x = TARGET_W / 2
    mid_y = TARGET_H / 2

    # --- 네 모서리 L자형 ---
    # 좌하단
    c.line(-CROP_OFFSET, 0, -CROP_OFFSET - CROP_LEN, 0)  # 가로
    c.line(0, -CROP_OFFSET, 0, -CROP_OFFSET - CROP_LEN)  # 세로

    # 우하단
    c.line(TARGET_W + CROP_OFFSET, 0, TARGET_W + CROP_OFFSET + CROP_LEN, 0)
    c.line(TARGET_W, -CROP_OFFSET, TARGET_W, -CROP_OFFSET - CROP_LEN)

    # 좌상단
    c.line(-CROP_OFFSET, TARGET_H, -CROP_OFFSET - CROP_LEN, TARGET_H)
    c.line(0, TARGET_H + CROP_OFFSET, 0, TARGET_H + CROP_OFFSET + CROP_LEN)

    # 우상단
    c.line(TARGET_W + CROP_OFFSET, TARGET_H, TARGET_W + CROP_OFFSET + CROP_LEN, TARGET_H)
    c.line(TARGET_W, TARGET_H + CROP_OFFSET, TARGET_W, TARGET_H + CROP_OFFSET + CROP_LEN)

    # --- 네 변 중앙 ---
    # 상단 중앙
    c.line(mid_x, TARGET_H + CROP_OFFSET, mid_x, TARGET_H + CROP_OFFSET + CROP_LEN)
    # 하단 중앙
    c.line(mid_x, -CROP_OFFSET, mid_x, -CROP_OFFSET - CROP_LEN)
    # 좌측 중앙
    c.line(-CROP_OFFSET, mid_y, -CROP_OFFSET - CROP_LEN, mid_y)
    # 우측 중앙
    c.line(TARGET_W + CROP_OFFSET, mid_y, TARGET_W + CROP_OFFSET + CROP_LEN, mid_y)


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
        if orig_w < TARGET_W and orig_h < TARGET_H:
            scale_w = TARGET_W / orig_w
            scale_h = TARGET_H / orig_h
            scale = min(scale_w, scale_h)
        else:
            scale = 1.0

        new_w = orig_w * scale
        new_h = orig_h * scale

        c = canvas.Canvas("temp.pdf", pagesize=(TARGET_W, TARGET_H))

        # 원본 PDF → 이미지 렌더링
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(scale, scale))
        imgdata = pix.tobytes("png")
        img = ImageReader(io.BytesIO(imgdata))

        # 중앙 배치
        offset_x = (TARGET_W - new_w) / 2
        offset_y = (TARGET_H - new_h) / 2
        c.drawImage(img, offset_x, offset_y, new_w, new_h, mask='auto')

        # 크롭마크 추가
        draw_cropmarks(c)

        c.showPage()
        c.save()

        temp_reader = PdfReader("temp.pdf")
        writer.add_page(temp_reader.pages[0])

    with open(output_pdf, "wb") as f:
        writer.write(f)

    print(f"✅ 저장 완료: {output_pdf}")


if __name__ == "__main__":
    filename = input("PDF 파일명을 입력하세요: ").strip()
    resize_with_cropmarks(filename)
