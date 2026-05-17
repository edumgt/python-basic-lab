"""
PDF to DOCX 변환 모듈
사용법:
    python PdfToDocx.py input.pdf                     # 같은 폴더에 output.docx 생성
    python PdfToDocx.py input.pdf output.docx         # 지정 경로에 저장
    python PdfToDocx.py /folder/with/pdfs             # 폴더 내 모든 PDF 일괄 변환
    python PdfToDocx.py input.pdf --pages 0,1,2       # 특정 페이지만 변환 (0부터 시작)
"""

import sys
import os
from pathlib import Path
from pdf2docx import Converter


def convert_pdf_to_docx(pdf_path: str, docx_path: str = None, pages: list[int] = None) -> str:
    """
    단일 PDF 파일을 DOCX로 변환합니다.

    Args:
        pdf_path: 변환할 PDF 파일 경로
        docx_path: 저장할 DOCX 경로 (None이면 PDF와 같은 위치에 저장)
        pages: 변환할 페이지 번호 리스트 (None이면 전체)

    Returns:
        생성된 DOCX 파일 경로
    """
    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"PDF 파일이 아닙니다: {pdf_path}")

    if docx_path is None:
        docx_path = pdf_path.with_suffix(".docx")
    else:
        docx_path = Path(docx_path).resolve()
        docx_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"변환 중: {pdf_path.name} → {docx_path.name}")

    cv = Converter(str(pdf_path))
    cv.convert(str(docx_path), pages=pages)
    cv.close()

    print(f"완료: {docx_path}")
    return str(docx_path)


def convert_folder(folder_path: str, output_folder: str = None, pages: list[int] = None) -> list[str]:
    """
    폴더 내 모든 PDF 파일을 DOCX로 일괄 변환합니다.

    Args:
        folder_path: PDF 파일들이 있는 폴더 경로
        output_folder: 저장할 폴더 (None이면 원본과 같은 폴더)
        pages: 변환할 페이지 번호 리스트

    Returns:
        생성된 DOCX 파일 경로 리스트
    """
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        raise NotADirectoryError(f"폴더를 찾을 수 없습니다: {folder}")

    pdf_files = sorted(folder.glob("*.pdf"))
    if not pdf_files:
        print(f"PDF 파일이 없습니다: {folder}")
        return []

    out_dir = Path(output_folder).resolve() if output_folder else folder
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, pdf in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] ", end="")
        docx_path = out_dir / pdf.with_suffix(".docx").name
        try:
            result = convert_pdf_to_docx(str(pdf), str(docx_path), pages=pages)
            results.append(result)
        except Exception as e:
            print(f"오류 ({pdf.name}): {e}")

    print(f"\n총 {len(results)}/{len(pdf_files)}개 변환 완료")
    return results


def _parse_pages(pages_str: str) -> list[int]:
    """'0,1,2' 형식의 문자열을 정수 리스트로 변환"""
    try:
        return [int(p.strip()) for p in pages_str.split(",")]
    except ValueError:
        raise ValueError(f"페이지 형식이 잘못됐습니다. 예시: --pages 0,1,2 (입력값: {pages_str!r})")


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    pages = None
    if "--pages" in args:
        idx = args.index("--pages")
        if idx + 1 >= len(args):
            print("오류: --pages 뒤에 페이지 번호를 입력하세요. 예: --pages 0,1,2")
            sys.exit(1)
        pages = _parse_pages(args[idx + 1])
        args = args[:idx] + args[idx + 2:]

    if not args:
        print("오류: 변환할 PDF 파일 또는 폴더 경로를 입력하세요.")
        sys.exit(1)

    target = args[0]
    output = args[1] if len(args) > 1 else None

    if os.path.isdir(target):
        convert_folder(target, output, pages=pages)
    else:
        convert_pdf_to_docx(target, output, pages=pages)


if __name__ == "__main__":
    main()
