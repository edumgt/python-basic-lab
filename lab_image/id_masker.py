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

from __future__ import annotations  # 최신 타입 힌트 문법을 안정적으로 사용합니다.

import os  # 경로 결합, 파일 존재 확인, 폴더 순회에 사용합니다.
import re  # 주민등록번호 정규식 패턴 검출에 사용합니다.
import sys  # 실행 인자 처리와 번들 경로 판별에 사용합니다.

import cv2  # 이미지 로드/저장과 도형 마스킹 처리에 사용합니다.
import pytesseract  # OCR 엔진 호출을 위한 파이썬 래퍼입니다.

# === Tesseract 경로 설정 (번들 실행 파일 기준) ===
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))  # PyInstaller 번들 환경이면 _MEIPASS를, 아니면 현재 파일 경로를 기준 디렉터리로 사용합니다.
TESSERACT_EXE = os.path.join(BASE_DIR, "tesseract", "tesseract.exe")  # 번들 내부 tesseract 실행 파일 경로를 구성합니다.
TESSDATA_DIR = os.path.join(BASE_DIR, "tesseract", "tessdata")  # OCR 언어 데이터(tessdata) 디렉터리 경로를 구성합니다.

pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE  # pytesseract가 사용할 tesseract 실행 파일을 명시적으로 지정합니다.
os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR  # tesseract가 언어 데이터 폴더를 올바르게 찾도록 환경 변수를 설정합니다.

# === 주민등록번호 자리수 상수 ===
JUMIN_FRONT_LENGTH = 6  # 주민번호 앞자리(생년월일) 길이입니다.
JUMIN_BACK_LENGTH = 7  # 주민번호 뒷자리(성별+일련번호) 길이입니다.
JUMIN_TOTAL_LENGTH = JUMIN_FRONT_LENGTH + JUMIN_BACK_LENGTH  # 전체 자리수(13자리)를 계산해 비율 계산에 재사용합니다.


# === 단일 이미지 마스킹 ===
def mask_jumin_number(image_path: str, output_path: str) -> None:
    """
    image_path 에서 주민등록번호를 찾아 뒷자리를 마스킹하고
    output_path 에 저장합니다. 검출되지 않으면 생략합니다.
    """
    image = cv2.imread(image_path)  # 입력 이미지를 메모리로 읽습니다.
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # OCR 인식률을 위해 그레이스케일 이미지로 변환합니다.
    data = pytesseract.image_to_data(gray, lang="kor", output_type=pytesseract.Output.DICT)  # OCR 결과를 단어 단위 좌표/텍스트 딕셔너리로 추출합니다.

    found = False  # 주민번호 검출 여부를 추적해 저장 여부를 결정합니다.
    for i, text in enumerate(data["text"]):  # OCR이 반환한 각 단어를 순회합니다.
        match = re.match(r"(\d{6})[- ]?(\d{7})", text)  # 6자리-7자리(하이픈/공백 선택) 패턴인지 검사합니다.
        if match:  # 주민번호 형태가 맞으면 마스킹 로직을 실행합니다.
            found = True  # 하나라도 발견되면 결과 이미지를 저장하도록 플래그를 켭니다.
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]  # 해당 텍스트 박스의 위치와 크기를 가져옵니다.
            front_width = int(w * JUMIN_FRONT_LENGTH / JUMIN_TOTAL_LENGTH)  # 전체 박스 폭에서 앞자리 비율에 해당하는 너비를 계산합니다.
            mask_x = x + front_width + 5  # 앞자리 뒤쪽으로 약간 여유를 두고 마스킹 시작 x 좌표를 계산합니다.
            mask_w = w - front_width - 5  # 뒷자리 영역의 마스킹 폭을 계산합니다.
            cv2.rectangle(image, (mask_x, y), (mask_x + mask_w, y + h), (0, 0, 0), -1)  # 뒷자리 영역을 검은 사각형으로 채워 가립니다.

    if found:  # 주민번호를 최소 1개 이상 찾은 경우입니다.
        cv2.imwrite(output_path, image)  # 마스킹된 이미지를 결과 경로에 저장합니다.
        print(f"[✅] 마스킹 저장: {output_path}")  # 성공 저장 로그를 출력합니다.
    else:  # 주민번호 패턴을 전혀 찾지 못한 경우입니다.
        print(f"[ℹ️] 주민번호 미검출 → 생략: {os.path.basename(image_path)}")  # 저장하지 않고 스킵했음을 안내합니다.


# === 폴더 일괄 처리 ===
def process_folder(org_folder: str = "org", upd_folder: str = "upd") -> None:
    """
    org_folder 의 이미지를 마스킹하여 upd_folder 에 저장합니다.
    이미 처리된 파일은 건너뜁니다.
    """
    os.makedirs(upd_folder, exist_ok=True)  # 결과 폴더가 없으면 생성하고 이미 있으면 그대로 사용합니다.

    for filename in os.listdir(org_folder):  # 원본 폴더의 모든 파일명을 순회합니다.
        if not filename.lower().endswith((".png", ".jpg", ".jpeg")):  # 이미지 확장자가 아닌 파일은 처리 대상에서 제외합니다.
            continue  # 다음 파일로 즉시 넘어갑니다.

        org_path = os.path.join(org_folder, filename)  # 원본 이미지의 전체 경로를 만듭니다.
        upd_path = os.path.join(upd_folder, filename)  # 결과 이미지의 전체 경로를 만듭니다.

        if not os.path.exists(upd_path):  # 아직 처리되지 않은 새 파일인 경우입니다.
            print(f"[🔍] 새 파일 감지: {filename}")  # 신규 처리 시작 로그를 출력합니다.
            mask_jumin_number(org_path, upd_path)  # 주민번호 마스킹 함수를 호출해 결과를 생성합니다.
        else:  # 이미 결과 파일이 존재하는 경우입니다.
            print(f"[⏩] 이미 처리됨: {filename}")  # 중복 처리를 피하기 위해 건너뜁니다.


# === 진입점 ===
if __name__ == "__main__":  # 스크립트를 직접 실행했을 때만 CLI 로직을 수행합니다.
    if len(sys.argv) == 3:  # 입력/출력 폴더를 사용자 인자로 준 경우입니다.
        process_folder(sys.argv[1], sys.argv[2])  # 사용자 지정 폴더 쌍으로 배치 처리를 실행합니다.
    else:  # 인자를 주지 않은 기본 실행 경로입니다.
        process_folder()  # 기본 org → upd 폴더를 대상으로 처리합니다.
