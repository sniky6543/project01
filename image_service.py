"""제품 사진 기반 포스터 생성과 A4·A5·SNS 파일 변환을 담당합니다."""

# OpenAI 이미지 결과의 Base64 문자열을 실제 바이트로 바꾸기 위해 불러옵니다.
import base64

# 메모리 안에서 이미지 파일을 다루기 위해 불러옵니다.
import io

# OpenAI SDK에 전달할 임시 파일을 만들기 위해 불러옵니다.
import tempfile

# 여러 파일을 안전하게 열고 닫기 위해 불러옵니다.
from contextlib import ExitStack

# 파일 경로를 편리하게 다루기 위해 불러옵니다.
from pathlib import Path

# OpenAI API 클라이언트 자료형을 불러옵니다.
from openai import OpenAI

# 이미지 회전, 크기 조절과 저장을 위해 Pillow를 불러옵니다.
from PIL import Image, ImageOps


# 최종 저장 규격과 AI 생성 단계의 권장 비율을 정의합니다.
FINAL_OUTPUT_SPECS: dict[str, dict[str, object]] = {
    "A4 세로 포스터": {
        "final_pixels": (2480, 3508),
        "api_size": "1536x2176",
    },
    "A4 가로 포스터": {
        "final_pixels": (3508, 2480),
        "api_size": "2176x1536",
    },
    "A5 세로 포스터": {
        "final_pixels": (1748, 2480),
        "api_size": "1536x2176",
    },
    "A5 가로 포스터": {
        "final_pixels": (2480, 1748),
        "api_size": "2176x1536",
    },
    "SNS 정사각형": {
        "final_pixels": (1080, 1080),
        "api_size": "1536x1536",
    },
}


def get_output_spec(output_type: str) -> dict[str, object]:
    """선택한 출력 유형의 최종 픽셀과 AI 생성 크기를 반환합니다."""

    # 등록된 출력 형식이면 해당 값을 반환합니다.
    if output_type in FINAL_OUTPUT_SPECS:
        return FINAL_OUTPUT_SPECS[output_type]

    # 예상하지 못한 값이면 A4 세로를 기본값으로 사용합니다.
    return FINAL_OUTPUT_SPECS["A4 세로 포스터"]


def normalize_uploaded_image(image_bytes: bytes) -> bytes:
    """업로드한 JPG, PNG와 WEBP를 표준 PNG로 변환합니다."""

    # 메모리 바이트에서 원본 이미지를 엽니다.
    with Image.open(io.BytesIO(image_bytes)) as image:
        # 휴대전화 사진의 EXIF 회전값을 실제 화면 방향에 적용합니다.
        image = ImageOps.exif_transpose(image)

        # 너무 큰 사진은 비율을 유지하면서 최대 4096픽셀 안으로 줄입니다.
        image.thumbnail((4096, 4096), Image.Resampling.LANCZOS)

        # 투명 정보가 있으면 RGBA 모드로 바꿉니다.
        if "A" in image.getbands():
            image = image.convert("RGBA")
        # 투명 정보가 없으면 RGB 모드로 바꿉니다.
        else:
            image = image.convert("RGB")

        # 변환 결과를 담을 메모리 공간을 만듭니다.
        buffer = io.BytesIO()

        # OpenAI 이미지 편집 API와 호환성이 좋은 PNG로 저장합니다.
        image.save(buffer, format="PNG", optimize=True)

        # 완성된 PNG 바이트를 반환합니다.
        return buffer.getvalue()


def generate_poster_image(
    client: OpenAI,
    source_images: list[bytes],
    prompt: str,
    model: str,
    api_size: str,
    quality: str,
) -> bytes:
    """제품 사진 1~4장을 참고해 제품광고 포스터 한 장을 생성합니다."""

    # 제품 사진이 없으면 생성할 수 없으므로 오류를 발생시킵니다.
    if not source_images:
        raise ValueError("제품 사진이 한 장 이상 필요합니다.")

    # 생성이 끝난 뒤 삭제할 임시 파일 경로를 저장합니다.
    temporary_paths: list[Path] = []

    try:
        # 각 제품 사진을 OpenAI SDK에 전달할 임시 PNG 파일로 만듭니다.
        for image_bytes in source_images:
            # 업로드 이미지를 표준 PNG로 정리합니다.
            normalized_image = normalize_uploaded_image(image_bytes)

            # 자동 삭제하지 않는 임시 PNG 파일을 생성합니다.
            with tempfile.NamedTemporaryFile(
                suffix=".png",
                delete=False,
            ) as temporary_file:
                # 정리한 이미지 바이트를 임시 파일에 씁니다.
                temporary_file.write(normalized_image)

                # 나중에 삭제할 수 있도록 경로를 저장합니다.
                temporary_paths.append(Path(temporary_file.name))

        # 오류가 생겨도 열린 파일을 안전하게 닫도록 ExitStack을 사용합니다.
        with ExitStack() as stack:
            # 모든 임시 이미지를 이진 읽기 모드로 엽니다.
            opened_images = [
                stack.enter_context(path.open("rb"))
                for path in temporary_paths
            ]

            # 사진이 한 장이면 단일 파일로, 여러 장이면 목록으로 전달합니다.
            image_argument = (
                opened_images[0]
                if len(opened_images) == 1
                else opened_images
            )

            # OpenAI 이미지 편집 API에 제품 사진과 광고 지시를 전달합니다.
            result = client.images.edit(
                # 환경설정에 지정된 이미지 모델을 사용합니다.
                model=model,
                # 제품 원본 사진 한 장 또는 여러 장을 전달합니다.
                image=image_argument,
                # 포스터 제작 지시문을 전달합니다.
                prompt=prompt,
                # 선택한 종이 비율에 가까운 이미지 크기를 요청합니다.
                size=api_size,
                # 빠른 초안, 일반 또는 고품질 값을 전달합니다.
                quality=quality,
            )

        # 결과 목록이 비어 있으면 정상적인 생성 결과가 아닙니다.
        if not result.data:
            raise RuntimeError("AI 이미지 생성 결과가 비어 있습니다.")

        # 첫 번째 결과의 Base64 이미지 문자열을 가져옵니다.
        image_base64 = result.data[0].b64_json

        # 이미지 데이터가 없으면 오류를 발생시킵니다.
        if not image_base64:
            raise RuntimeError("생성된 이미지 데이터를 받지 못했습니다.")

        # Base64 문자열을 실제 PNG 바이트로 변환해 반환합니다.
        return base64.b64decode(image_base64)

    finally:
        # 성공하거나 오류가 나더라도 임시 파일을 모두 삭제합니다.
        for path in temporary_paths:
            path.unlink(missing_ok=True)


def _fit_to_final_canvas(
    generated_image: bytes,
    final_pixels: tuple[int, int],
) -> Image.Image:
    """AI 이미지를 늘이지 않고 최종 출력 캔버스 비율에 맞춰 배치합니다."""

    # AI가 만든 PNG 바이트를 Pillow 이미지로 엽니다.
    with Image.open(io.BytesIO(generated_image)) as image:
        # 이미지 방향 정보를 바로잡습니다.
        image = ImageOps.exif_transpose(image)

        # PNG, JPG와 PDF 저장에 적합한 RGB로 변환합니다.
        image = image.convert("RGB")

        # 원본 비율을 유지한 채 최종 캔버스를 빈틈없이 채웁니다.
        fitted = ImageOps.fit(
            image,
            final_pixels,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

        # 원본 파일이 닫혀도 사용할 수 있도록 복사본을 반환합니다.
        return fitted.copy()


def build_export_files(
    generated_image: bytes,
    output_type: str,
    dpi: int = 300,
) -> dict[str, object]:
    """AI 이미지를 정확한 최종 규격의 PNG, JPG와 PDF로 변환합니다."""

    # 선택한 출력 형식의 정보를 가져옵니다.
    output_spec = get_output_spec(output_type)

    # 최종 픽셀 값을 정수 튜플로 변환합니다.
    final_pixels = tuple(output_spec["final_pixels"])

    # AI 이미지를 최종 A4, A5 또는 SNS 캔버스에 맞춥니다.
    poster = _fit_to_final_canvas(
        generated_image=generated_image,
        final_pixels=final_pixels,
    )

    # PNG 파일을 메모리에 저장할 공간을 만듭니다.
    png_buffer = io.BytesIO()

    # 최종 픽셀과 300dpi 정보를 포함해 PNG로 저장합니다.
    poster.save(
        png_buffer,
        format="PNG",
        dpi=(dpi, dpi),
        optimize=True,
    )

    # JPG 파일을 메모리에 저장할 공간을 만듭니다.
    jpg_buffer = io.BytesIO()

    # 고품질 인쇄용 JPG로 저장합니다.
    poster.save(
        jpg_buffer,
        format="JPEG",
        quality=95,
        subsampling=0,
        optimize=True,
        dpi=(dpi, dpi),
    )

    # PDF 파일을 메모리에 저장할 공간을 만듭니다.
    pdf_buffer = io.BytesIO()

    # 선택한 픽셀과 300dpi를 기준으로 PDF를 저장합니다.
    poster.save(
        pdf_buffer,
        format="PDF",
        resolution=float(dpi),
    )

    # 화면 미리보기와 다운로드에 필요한 모든 데이터를 반환합니다.
    return {
        "png": png_buffer.getvalue(),
        "jpg": jpg_buffer.getvalue(),
        "pdf": pdf_buffer.getvalue(),
        "output_type": output_type,
        "final_pixels": final_pixels,
        "dpi": dpi,
    }
