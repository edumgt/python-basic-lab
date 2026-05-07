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

from __future__ import annotations  # 최신 타입 힌트 문법을 안전하게 사용합니다.

import io  # 메모리 버퍼(BytesIO)로 이미지를 전달하는 데 사용합니다.
import os  # 파일명 분리와 임시 파일 삭제에 사용합니다.
import tempfile  # 페이지별 임시 PDF 파일 생성에 사용합니다.

import fitz  # PyMuPDF로 원본 PDF 페이지를 이미지로 렌더링합니다.
from PyPDF2 import PdfReader, PdfWriter  # PDF 읽기/쓰기 병합 작업에 사용합니다.
from reportlab.lib.units import mm  # mm 단위를 포인트로 변환하는 상수를 제공합니다.
from reportlab.lib.utils import ImageReader  # reportlab 캔버스에 PIL/바이트 이미지를 넣기 위한 래퍼입니다.
from reportlab.pdfgen import canvas  # reportlab 캔버스 객체를 생성합니다.
from reportlab.pdfgen.canvas import Canvas  # draw_cropmarks 함수 타입 힌트에 사용합니다.

# === 상수 ===
TRIM_W = 460 * mm  # 최종 작업 캔버스 가로 크기(460mm)를 포인트로 계산합니다.
TRIM_H = 318 * mm  # 최종 작업 캔버스 세로 크기(318mm)를 포인트로 계산합니다.
CROP_LEN = 5 * mm  # 재단선 길이를 5mm로 설정합니다.


# === 크롭마크 그리기 ===
def draw_cropmarks(c: Canvas) -> None:
    """캔버스 c 위에 크롭마크(재단선)를 그립니다."""
    c.setStrokeColorRGB(0, 0, 0)  # 재단선 색상을 검정으로 지정합니다.
    c.setLineWidth(0.5)  # 재단선 두께를 0.5pt로 설정합니다.

    left, right = 0, TRIM_W  # 좌/우 경계 x 좌표를 정의합니다.
    bottom, top = 0, TRIM_H  # 하/상 경계 y 좌표를 정의합니다.
    mid_x, mid_y = TRIM_W / 2, TRIM_H / 2  # 상하좌우 중앙 마크용 중심 좌표를 계산합니다.

    c.line(left, bottom, left + CROP_LEN, bottom)  # 좌하단 가로 재단선을 그립니다.
    c.line(left, bottom, left, bottom + CROP_LEN)  # 좌하단 세로 재단선을 그립니다.
    c.line(right, bottom, right - CROP_LEN, bottom)  # 우하단 가로 재단선을 그립니다.
    c.line(right, bottom, right, bottom + CROP_LEN)  # 우하단 세로 재단선을 그립니다.
    c.line(left, top, left + CROP_LEN, top)  # 좌상단 가로 재단선을 그립니다.
    c.line(left, top, left, top - CROP_LEN)  # 좌상단 세로 재단선을 그립니다.
    c.line(right, top, right - CROP_LEN, top)  # 우상단 가로 재단선을 그립니다.
    c.line(right, top, right, top - CROP_LEN)  # 우상단 세로 재단선을 그립니다.

    c.line(mid_x, top, mid_x, top - CROP_LEN)  # 상단 중앙 재단선을 그립니다.
    c.line(mid_x, bottom, mid_x, bottom + CROP_LEN)  # 하단 중앙 재단선을 그립니다.
    c.line(left, mid_y, left + CROP_LEN, mid_y)  # 좌측 중앙 재단선을 그립니다.
    c.line(right, mid_y, right - CROP_LEN, mid_y)  # 우측 중앙 재단선을 그립니다.


# === 핵심 변환 ===
def resize_with_cropmarks(input_pdf: str) -> None:
    """
    input_pdf 를 460×318mm 캔버스에 맞게 조정하고 크롭마크를 추가합니다.
    결과는 <원본명>_work.pdf 로 저장됩니다.
    """
    base, _ = os.path.splitext(input_pdf)  # 입력 파일의 확장자를 제거한 기본 이름을 얻습니다.
    output_pdf = f"{base}_work.pdf"  # 결과 파일명을 원본 기준 *_work.pdf 형식으로 만듭니다.

    reader = PdfReader(input_pdf)  # 원본 PDF 페이지를 순회하기 위해 읽기 객체를 생성합니다.
    writer = PdfWriter()  # 변환 결과 페이지를 누적할 쓰기 객체를 생성합니다.
    doc = fitz.open(input_pdf)  # 페이지 렌더링을 위해 PyMuPDF 문서를 엽니다.

    for i, page in enumerate(reader.pages):  # 원본 PDF의 각 페이지를 인덱스와 함께 순회합니다.
        orig_w = float(page.mediabox.width)  # 원본 페이지 가로 크기를 float로 읽습니다.
        orig_h = float(page.mediabox.height)  # 원본 페이지 세로 크기를 float로 읽습니다.

        if orig_w < TRIM_W and orig_h < TRIM_H:  # 원본이 캔버스보다 작은 경우에만 확대를 허용합니다.
            scale = min(TRIM_W / orig_w, TRIM_H / orig_h)  # 가로/세로 중 더 작은 배율을 사용해 비율 왜곡 없이 맞춥니다.
        else:  # 원본이 이미 충분히 크거나 한쪽이 큰 경우입니다.
            scale = 1.0  # 확대/축소 없이 원본 비율과 크기를 유지합니다.

        new_w = orig_w * scale  # 스케일 적용 후 실제 배치 가로 크기를 계산합니다.
        new_h = orig_h * scale  # 스케일 적용 후 실제 배치 세로 크기를 계산합니다.

        fd, temp_path = tempfile.mkstemp(suffix=".pdf")  # 페이지 단위 임시 PDF 파일 경로를 생성합니다.
        os.close(fd)  # 저수준 파일 디스크립터는 reportlab이 다시 열 수 있도록 즉시 닫습니다.
        c = canvas.Canvas(temp_path, pagesize=(TRIM_W, TRIM_H))  # 고정 재단 사이즈 캔버스를 새 임시 PDF에 생성합니다.

        pix = doc[i].get_pixmap(matrix=fitz.Matrix(scale, scale))  # 원본 페이지를 현재 배율로 렌더링한 픽스맵을 만듭니다.
        img = ImageReader(io.BytesIO(pix.tobytes("png")))  # 렌더링 결과 PNG 바이트를 reportlab이 읽을 이미지 객체로 감쌉니다.

        offset_x = (TRIM_W - new_w) / 2  # 캔버스 중앙 정렬을 위한 x 오프셋을 계산합니다.
        offset_y = (TRIM_H - new_h) / 2  # 캔버스 중앙 정렬을 위한 y 오프셋을 계산합니다.
        c.drawImage(img, offset_x, offset_y, new_w, new_h, mask="auto")  # 렌더링 이미지를 계산된 위치와 크기로 캔버스에 배치합니다.

        draw_cropmarks(c)  # 해당 페이지 캔버스 위에 재단선을 그립니다.
        c.showPage()  # 현재 페이지를 캔버스 문서에 확정합니다.
        c.save()  # 임시 PDF 파일로 페이지를 저장 완료합니다.

        temp_reader = PdfReader(temp_path)  # 방금 생성한 임시 PDF를 다시 읽습니다.
        writer.add_page(temp_reader.pages[0])  # 임시 PDF의 첫 페이지를 최종 writer에 추가합니다.
        os.remove(temp_path)  # 사용이 끝난 임시 파일을 삭제해 디스크를 정리합니다.

    with open(output_pdf, "wb") as f:  # 최종 출력 파일을 바이너리 쓰기 모드로 엽니다.
        writer.write(f)  # 누적된 모든 결과 페이지를 출력 PDF로 기록합니다.

    print(f"✅ 저장 완료: {output_pdf}")  # 사용자에게 결과 저장 경로를 안내합니다.


# === 진입점 ===
if __name__ == "__main__":  # 스크립트를 직접 실행했을 때만 CLI 입력 흐름을 수행합니다.
    filename = input("PDF 파일명을 입력하세요: ").strip()  # 사용자로부터 입력 PDF 파일명을 받아 양끝 공백을 제거합니다.
    resize_with_cropmarks(filename)  # 입력받은 PDF를 변환해 크롭마크 결과물을 생성합니다.
