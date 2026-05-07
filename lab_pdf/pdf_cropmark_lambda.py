"""
Lab: PDF 재단선(크롭마크) 추가 — AWS Lambda 버전
=================================================
S3 이벤트 트리거로 실행되며, 입력 PDF를 460×318mm 캔버스에
중앙 배치하고 크롭마크를 추가한 뒤 결과를 S3에 업로드합니다.

Lambda 핸들러: lambda_handler(event, context)
로컬 CLI 사용법:
    python pdf_cropmark_lambda.py <input.pdf> <output.pdf>
"""

from __future__ import annotations  # 최신 타입 힌트 문법을 안전하게 사용합니다.

import io  # 메모리 바이트 버퍼로 렌더링 이미지를 전달할 때 사용합니다.
import os  # 경로 조합과 임시 경로/키 변환에 사용합니다.
import tempfile  # Lambda 임시 디렉터리(/tmp) 경로를 얻는 데 사용합니다.
from typing import Any  # Lambda event 타입 힌트를 유연하게 표현하기 위해 사용합니다.

import fitz  # PyMuPDF로 PDF 페이지를 이미지로 렌더링합니다.
from PyPDF2 import PdfReader, PdfWriter  # PDF 읽기/쓰기 병합 작업에 사용합니다.
from reportlab.lib.units import mm  # mm 단위를 포인트 단위로 환산합니다.
from reportlab.lib.utils import ImageReader  # 이미지 바이트를 reportlab drawImage 입력으로 변환합니다.
from reportlab.pdfgen import canvas  # 페이지 캔버스 생성을 담당합니다.
from reportlab.pdfgen.canvas import Canvas  # draw_cropmarks 함수 타입 힌트에 사용합니다.

# === 상수 ===
TRIM_W = 460 * mm  # 최종 캔버스 가로 길이(460mm)를 포인트로 계산합니다.
TRIM_H = 318 * mm  # 최종 캔버스 세로 길이(318mm)를 포인트로 계산합니다.
CROP_LEN = 5 * mm  # 재단선 선분 길이를 5mm로 설정합니다.


# === 크롭마크 그리기 ===
def draw_cropmarks(c: Canvas) -> None:
    """캔버스 c 위에 크롭마크(재단선)를 그립니다."""
    c.setStrokeColorRGB(0, 0, 0)  # 재단선 색상을 검정으로 지정합니다.
    c.setLineWidth(0.5)  # 재단선 두께를 얇게 0.5pt로 고정합니다.

    left, right = 0, TRIM_W  # 좌우 경계 좌표를 설정합니다.
    bottom, top = 0, TRIM_H  # 상하 경계 좌표를 설정합니다.
    mid_x, mid_y = TRIM_W / 2, TRIM_H / 2  # 각 변 중앙 표시를 위한 중심 좌표를 계산합니다.

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
def resize_with_cropmarks(input_pdf: str, output_pdf: str) -> None:
    """
    input_pdf 를 460×318mm 캔버스에 맞게 조정하고 크롭마크를 추가합니다.
    결과는 output_pdf 경로에 저장됩니다.
    """
    reader = PdfReader(input_pdf)  # 입력 PDF를 페이지 단위로 읽기 위한 객체를 생성합니다.
    writer = PdfWriter()  # 변환된 페이지를 누적 저장할 writer 객체를 생성합니다.
    doc = fitz.open(input_pdf)  # 페이지 렌더링을 위해 PyMuPDF 문서를 엽니다.

    for i, page in enumerate(reader.pages):  # 모든 페이지를 순회하며 동일한 처리를 적용합니다.
        orig_w = float(page.mediabox.width)  # 원본 페이지 가로 크기를 읽습니다.
        orig_h = float(page.mediabox.height)  # 원본 페이지 세로 크기를 읽습니다.

        if orig_w < TRIM_W and orig_h < TRIM_H:  # 페이지가 목표 캔버스보다 작은 경우입니다.
            scale = min(TRIM_W / orig_w, TRIM_H / orig_h)  # 비율을 유지하며 캔버스 안에 최대한 크게 맞춥니다.
        else:  # 이미 목표 캔버스보다 크거나 같은 경우입니다.
            scale = 1.0  # 크기 변경 없이 원본 스케일을 유지합니다.

        new_w, new_h = orig_w * scale, orig_h * scale  # 배율 적용 후 실제 배치 크기를 계산합니다.
        temp_pdf = os.path.join(tempfile.gettempdir(), f"temp_{i}.pdf")  # Lambda /tmp에 페이지별 임시 PDF 경로를 생성합니다.

        c = canvas.Canvas(temp_pdf, pagesize=(TRIM_W, TRIM_H))  # 고정 크기 캔버스를 임시 파일에 생성합니다.
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(scale, scale))  # 원본 페이지를 현재 배율로 렌더링합니다.
        img = ImageReader(io.BytesIO(pix.tobytes("png")))  # 렌더링된 PNG 바이트를 reportlab 이미지로 래핑합니다.

        offset_x = (TRIM_W - new_w) / 2  # 가로 중앙 정렬 오프셋을 계산합니다.
        offset_y = (TRIM_H - new_h) / 2  # 세로 중앙 정렬 오프셋을 계산합니다.
        c.drawImage(img, offset_x, offset_y, new_w, new_h, mask="auto")  # 렌더링 이미지를 캔버스 중앙에 배치합니다.

        draw_cropmarks(c)  # 페이지에 재단선을 추가합니다.
        c.showPage()  # 현재 페이지를 확정합니다.
        c.save()  # 임시 PDF 파일로 저장합니다.

        temp_reader = PdfReader(temp_pdf)  # 생성된 임시 PDF를 다시 읽습니다.
        writer.add_page(temp_reader.pages[0])  # 임시 PDF 첫 페이지를 최종 writer에 추가합니다.

    with open(output_pdf, "wb") as f:  # 최종 결과 PDF를 바이너리 쓰기 모드로 엽니다.
        writer.write(f)  # 누적된 페이지를 결과 파일로 기록합니다.


# === AWS Lambda 핸들러 ===
def lambda_handler(event: dict[str, Any], context: object) -> dict[str, str]:
    """
    S3 트리거 기반 Lambda 핸들러.
    업로드된 PDF에 크롭마크를 추가하고 *_work.pdf 로 저장합니다.
    """
    import boto3  # Lambda 환경에서만 필요한 의존성을 함수 내부에서 지연 임포트합니다.

    s3 = boto3.client("s3")  # S3 다운로드/업로드를 위한 클라이언트를 생성합니다.
    bucket = event["Records"][0]["s3"]["bucket"]["name"]  # 이벤트에서 대상 버킷 이름을 추출합니다.
    key = event["Records"][0]["s3"]["object"]["key"]  # 이벤트에서 업로드된 객체 키를 추출합니다.

    input_path = os.path.join(tempfile.gettempdir(), "input.pdf")  # Lambda 임시 디렉터리에 입력 파일 경로를 지정합니다.
    output_path = os.path.join(tempfile.gettempdir(), "output.pdf")  # Lambda 임시 디렉터리에 출력 파일 경로를 지정합니다.

    s3.download_file(bucket, key, input_path)  # 원본 PDF를 S3에서 로컬 임시 경로로 다운로드합니다.
    resize_with_cropmarks(input_path, output_path)  # 다운로드한 PDF에 크롭마크를 적용해 결과를 생성합니다.
    s3.upload_file(output_path, bucket, key.replace(".pdf", "_work.pdf"))  # 처리 결과를 *_work.pdf 키로 업로드합니다.

    return {"status": "done", "bucket": bucket, "key": key}  # 호출자에게 처리 결과 메타데이터를 반환합니다.


# === 로컬 실행 ===
if __name__ == "__main__":  # 로컬에서 스크립트를 직접 실행할 때만 CLI 모드를 수행합니다.
    import sys  # 로컬 실행 인자 개수 검증과 값 참조를 위해 sys를 임포트합니다.

    if len(sys.argv) != 3:  # 입력/출력 PDF 경로 2개가 모두 전달되었는지 확인합니다.
        print("Usage: python pdf_cropmark_lambda.py <input.pdf> <output.pdf>")  # 올바른 사용법을 안내합니다.
        sys.exit(1)  # 잘못된 사용이면 오류 코드로 종료합니다.

    resize_with_cropmarks(sys.argv[1], sys.argv[2])  # 전달된 입력 PDF를 처리해 지정된 출력 PDF로 저장합니다.
    print(f"✅ 저장 완료: {sys.argv[2]}")  # 로컬 실행 완료 메시지를 출력합니다.
