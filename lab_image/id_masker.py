"""
Lab: OCR 기반 주민등록번호 자동 마스킹
========================================
Tesseract OCR로 이미지에서 주민등록번호 패턴을 검출하고
뒷자리 7자리를 검은 사각형으로 마스킹합니다.

사용법:
    python id_masker.py            # org/ → upd/ 폴더 일괄 처리 (기본값)
    python id_masker.py <org_folder> <upd_folder>

의존성: opencv-python, pytesseract, tesseract-ocr (시스템 설치 필요)
"""

import os
import re
import sys

import cv2
import pytesseract

# === Tesseract 경로 설정 (번들 실행 파일 기준) ===
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
TESSERACT_EXE = os.path.join(BASE_DIR, "tesseract", "tesseract.exe")
TESSDATA_DIR = os.path.join(BASE_DIR, "tesseract", "tessdata")

pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE
os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR


# === 단일 이미지 마스킹 ===
def mask_jumin_number(image_path, output_path):
    """
    image_path 에서 주민등록번호를 찾아 뒷자리를 마스킹하고
    output_path 에 저장합니다. 검출되지 않으면 생략합니다.
    """
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    data = pytesseract.image_to_data(gray, lang="kor", output_type=pytesseract.Output.DICT)

    found = False
    for i, text in enumerate(data["text"]):
        match = re.match(r"(\d{6})[- ]?(\d{7})", text)
        if match:
            found = True
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            front_width = int(w * 6 / 13)
            mask_x = x + front_width + 5
            mask_w = w - front_width - 5
            cv2.rectangle(image, (mask_x, y), (mask_x + mask_w, y + h), (0, 0, 0), -1)

    if found:
        cv2.imwrite(output_path, image)
        print(f"[✅] 마스킹 저장: {output_path}")
    else:
        print(f"[ℹ️] 주민번호 미검출 → 생략: {os.path.basename(image_path)}")


# === 폴더 일괄 처리 ===
def process_folder(org_folder="org", upd_folder="upd"):
    """
    org_folder 의 이미지를 마스킹하여 upd_folder 에 저장합니다.
    이미 처리된 파일은 건너뜁니다.
    """
    os.makedirs(upd_folder, exist_ok=True)

    for filename in os.listdir(org_folder):
        if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        org_path = os.path.join(org_folder, filename)
        upd_path = os.path.join(upd_folder, filename)

        if not os.path.exists(upd_path):
            print(f"[🔍] 새 파일 감지: {filename}")
            mask_jumin_number(org_path, upd_path)
        else:
            print(f"[⏩] 이미 처리됨: {filename}")


# === 진입점 ===
if __name__ == "__main__":
    if len(sys.argv) == 3:
        process_folder(sys.argv[1], sys.argv[2])
    else:
        process_folder()
