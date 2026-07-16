"""원본 제품 사진, 생성 포스터와 작업 정보를 로컬 폴더에 저장합니다."""

# 작업 정보를 JSON으로 저장하기 위해 불러옵니다.
import json

# 파일명에 현재 날짜와 시간을 넣기 위해 불러옵니다.
from datetime import datetime

# 파일과 폴더 경로를 편리하게 다루기 위해 불러옵니다.
from pathlib import Path

# 같은 초에 만든 파일명이 겹치지 않도록 고유값을 만들기 위해 불러옵니다.
from uuid import uuid4

# 제품 정보와 광고 문구 데이터 형식을 불러옵니다.
from models import AdCopy, ProductBrief


# 현재 파일이 들어 있는 프로젝트 폴더를 기준 경로로 사용합니다.
BASE_DIR = Path(__file__).resolve().parent

# 업로드한 원본 사진이 저장되는 폴더입니다.
UPLOAD_DIR = BASE_DIR / "uploads"

# 생성한 PNG, JPG와 PDF가 저장되는 폴더입니다.
OUTPUT_DIR = BASE_DIR / "outputs"

# 제품 정보와 생성 설정이 저장되는 폴더입니다.
METADATA_DIR = BASE_DIR / "metadata"


def ensure_storage_directories() -> None:
    """실행에 필요한 저장 폴더가 없으면 자동으로 만듭니다."""

    # 원본 제품 사진 저장 폴더를 만듭니다.
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 생성 결과 저장 폴더를 만듭니다.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 작업 정보 저장 폴더를 만듭니다.
    METADATA_DIR.mkdir(parents=True, exist_ok=True)


def create_job_id() -> str:
    """한 번의 광고 생성 작업을 구분할 고유 번호를 만듭니다."""

    # 현재 날짜와 시간을 파일명에 안전한 형식으로 만듭니다.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # UUID 앞 여덟 글자로 짧은 고유값을 만듭니다.
    short_id = uuid4().hex[:8]

    # 날짜, 시간과 고유값을 합쳐 반환합니다.
    return f"{timestamp}_{short_id}"


def save_generation_result(
    job_id: str,
    original_images: list[bytes],
    export_files: dict[str, object],
    brief: ProductBrief,
    ad_copy: AdCopy,
    text_model: str,
    image_model: str,
) -> dict[str, Path]:
    """원본 사진, 포스터 파일 세 종류와 생성 정보를 저장합니다."""

    # 저장 폴더가 존재하는지 먼저 확인합니다.
    ensure_storage_directories()

    # 저장된 원본 이미지 경로를 모을 목록입니다.
    source_paths: list[Path] = []

    # 원본 제품 사진을 순서대로 PNG 파일로 저장합니다.
    for index, image_bytes in enumerate(original_images, start=1):
        # 작업 번호와 순서를 조합해 원본 파일명을 만듭니다.
        source_path = UPLOAD_DIR / f"{job_id}_source_{index}.png"

        # 원본 이미지 바이트를 실제 파일로 저장합니다.
        source_path.write_bytes(image_bytes)

        # 저장된 경로를 목록에 추가합니다.
        source_paths.append(source_path)

    # 생성된 포스터 PNG 경로를 만듭니다.
    png_path = OUTPUT_DIR / f"{job_id}_poster.png"

    # 생성된 포스터 JPG 경로를 만듭니다.
    jpg_path = OUTPUT_DIR / f"{job_id}_poster.jpg"

    # 생성된 포스터 PDF 경로를 만듭니다.
    pdf_path = OUTPUT_DIR / f"{job_id}_poster.pdf"

    # 세 종류의 결과 파일을 실제 폴더에 저장합니다.
    png_path.write_bytes(export_files["png"])
    jpg_path.write_bytes(export_files["jpg"])
    pdf_path.write_bytes(export_files["pdf"])

    # 생성 설정과 광고 문구가 저장될 JSON 경로를 만듭니다.
    metadata_path = METADATA_DIR / f"{job_id}.json"

    # 나중에 결과를 다시 확인할 수 있도록 모든 작업 정보를 묶습니다.
    metadata = {
        "job_id": job_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "product": brief.model_dump(mode="json"),
        "ad_copy": ad_copy.model_dump(mode="json"),
        "generation": {
            "text_model": text_model,
            "image_model": image_model,
            "output_type": export_files["output_type"],
            "final_pixels": export_files["final_pixels"],
            "dpi": export_files["dpi"],
        },
        "files": {
            "source_images": [str(path) for path in source_paths],
            "poster_png": str(png_path),
            "poster_jpg": str(jpg_path),
            "poster_pdf": str(pdf_path),
        },
    }

    # 한글이 깨지지 않도록 UTF-8 JSON 파일로 저장합니다.
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 화면에서 필요한 주요 파일 경로를 반환합니다.
    return {
        "png_path": png_path,
        "jpg_path": jpg_path,
        "pdf_path": pdf_path,
        "metadata_path": metadata_path,
    }
