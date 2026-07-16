"""AI 제품광고 포스터 생성기의 Streamlit 메인 화면입니다."""

# 작업 정보 다운로드와 입력값 비교를 위해 JSON을 불러옵니다.
import json

# .env 파일과 운영체제 환경변수에서 설정을 읽기 위해 불러옵니다.
import os

# OpenAI API 클라이언트와 주요 오류 종류를 불러옵니다.
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    RateLimitError,
)

# 프로젝트 폴더의 .env 파일을 읽기 위해 불러옵니다.
from dotenv import load_dotenv

# 웹 화면을 만들기 위해 Streamlit을 불러옵니다.
import streamlit as st

# 화면 옵션과 프로젝트 정보를 불러옵니다.
from config import (
    APP_NAME,
    APP_VERSION,
    BACKGROUND_TYPES,
    CATEGORIES,
    COLOR_TONES,
    OUTPUT_TYPES,
    POSTER_STYLES,
    QUALITY_MAP,
    TARGET_CUSTOMERS,
    TEAM_NAME,
    TEXT_AMOUNTS,
    USAGE_OPTIONS,
)

# 이미지 생성과 출력 파일 변환 함수를 불러옵니다.
from image_service import (
    build_export_files,
    generate_poster_image,
    get_output_spec,
    normalize_uploaded_image,
)

# 광고 문구 생성 함수를 불러옵니다.
from llm_service import generate_ad_copy

# 제품 정보와 광고 문구 데이터 형식을 불러옵니다.
from models import AdCopy, ProductBrief

# 이미지 AI에 전달할 포스터 프롬프트 함수를 불러옵니다.
from prompt_service import build_image_prompt

# 작업 번호 생성과 파일 저장 함수를 불러옵니다.
from storage import (
    create_job_id,
    ensure_storage_directories,
    save_generation_result,
)


# 프로젝트 폴더의 .env 설정을 읽습니다.
load_dotenv()

# 업로드, 결과와 메타데이터 저장 폴더를 준비합니다.
ensure_storage_directories()


# test모드 설정
DEBUG_MODE = True


# 브라우저 탭 제목, 아이콘과 넓은 화면 구성을 설정합니다.
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🖼️",
    layout="wide",
)

# 화면의 폭과 버튼 모양을 보기 좋게 조절합니다.
st.markdown(
    """
    <style>
        .block-container {
            max-width: 1260px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        div.stButton > button,
        div.stDownloadButton > button {
            min-height: 46px;
            border-radius: 12px;
            font-weight: 700;
        }

        .small-note {
            color: #667085;
            font-size: 0.92rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_default_api_key() -> str:
    """환경변수나 Streamlit Secrets에서 기본 API 키를 읽습니다."""

    # 먼저 프로젝트의 .env 또는 운영체제 환경변수에서 키를 찾습니다.
    environment_key = os.getenv("OPENAI_API_KEY", "").strip()

    # 환경변수에 키가 있으면 바로 반환합니다.
    if environment_key:
        return environment_key

    # Streamlit Cloud의 비밀 설정에서도 키를 찾아봅니다.
    try:
        secret_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        secret_key = ""

    # 키가 없으면 빈 문자열을 반환합니다.
    return secret_key


def make_copy_signature(brief: ProductBrief) -> str:
    """제품 내용이 같은지 비교해 광고 문구를 재사용할지 판단합니다."""

    # 광고 문구에 영향을 주는 제품 정보만 선택합니다.
    signature_data = {
        "product_name": brief.product_name,
        "brand_name": brief.brand_name,
        "price": brief.price,
        "quantity": brief.quantity,
        "features": brief.features,
        "category": brief.category,
        "target_customer": brief.target_customer,
        "usage": brief.usage,
        "text_amount": brief.text_amount,
    }

    # 항목 순서와 상관없이 비교할 수 있는 JSON 문자열로 반환합니다.
    return json.dumps(
        signature_data,
        ensure_ascii=False,
        sort_keys=True,
    )


def validate_inputs(
    api_key: str,
    product_name: str,
    features: str,
    uploaded_files: list,
) -> str:
    """필수 입력값을 검사하고 문제가 있으면 안내 문구를 반환합니다."""

    # API 키가 없으면 OpenAI 기능을 호출할 수 없습니다.
    if not api_key.strip():
        return "왼쪽 사이드바에 OpenAI API Key를 입력해 주세요."

    # 제품명이 없으면 포스터의 주제를 정할 수 없습니다.
    if not product_name.strip():
        return "제품명을 입력해 주세요."

    # 제품 특징이 없으면 정확한 광고 문구를 만들기 어렵습니다.
    if not features.strip():
        return "제품 특징을 입력해 주세요."

    # 제품 사진이 없으면 제품 기반 광고를 만들 수 없습니다.
    if not uploaded_files:
        return "제품 사진을 한 장 이상 업로드해 주세요."

    # 처리 시간과 비용을 고려해 사진을 최대 네 장으로 제한합니다.
    if len(uploaded_files) > 4:
        return "제품 사진은 최대 4장까지만 업로드해 주세요."

    # 문제가 없으면 빈 문자열을 반환합니다.
    return ""


def create_brief(
    product_name: str,
    brand_name: str,
    price: str,
    quantity: str,
    features: str,
    category: str,
    target_customer: str,
    usage: str,
    style: str,
    color_tone: str,
    background_type: str,
    text_amount: str,
    output_type: str,
    extra_request: str,
) -> ProductBrief:
    """현재 입력값을 ProductBrief 객체로 묶습니다."""

    # Pydantic 객체를 만들면서 글자 길이와 필수값을 함께 검사합니다.
    return ProductBrief(
        product_name=product_name,
        brand_name=brand_name,
        price=price,
        quantity=quantity,
        features=features,
        category=category,
        target_customer=target_customer,
        usage=usage,
        style=style,
        color_tone=color_tone,
        background_type=background_type,
        text_amount=text_amount,
        output_type=output_type,
        extra_request=extra_request,
    )


def perform_generation(
    api_key: str,
    brief: ProductBrief,
    uploaded_files: list,
    text_model: str,
    image_model: str,
    quality: str,
    reuse_copy_when_possible: bool,
) -> None:
    """문구 생성, 이미지 생성, 후처리와 저장을 차례대로 실행합니다."""

    # 화면에 전체 진행률 막대를 표시합니다.
    progress = st.progress(0, text="제품 사진을 준비하고 있습니다...")

    try:
        # 업로드한 각 파일의 원본 바이트를 읽습니다.
        original_image_bytes = [
            uploaded_file.getvalue()
            for uploaded_file in uploaded_files
        ]

        # OpenAI 전달과 원본 저장을 위해 제품 사진을 PNG로 정리합니다.
        normalized_images = [
            normalize_uploaded_image(image_bytes)
            for image_bytes in original_image_bytes
        ]

        # 제품 사진 준비가 끝났음을 진행률에 표시합니다.
        progress.progress(15, text="제품 사진 준비 완료")

        # 현재 제품 내용의 비교용 서명을 만듭니다.
        current_signature = make_copy_signature(brief)

        # 사용자가 입력한 API 키로 OpenAI 클라이언트를 만듭니다.
        client = OpenAI(api_key=api_key.strip())

        # 이전 결과가 있고 제품 내용이 같으면 광고 문구를 재사용할 수 있습니다.
        previous_result = st.session_state.get("last_result")
        can_reuse_copy = (
            reuse_copy_when_possible
            and previous_result is not None
            and previous_result.get("copy_signature") == current_signature
        )

        # 재사용 조건이 맞으면 이전 광고 문구를 다시 사용합니다.
        if can_reuse_copy:
            ad_copy = AdCopy.model_validate(previous_result["ad_copy"])
            progress.progress(35, text="기존 광고 문구를 유지합니다...")
        else:
            # 처음 생성하거나 제품 내용이 바뀌면 광고 문구를 새로 만듭니다.
            progress.progress(25, text="광고 문구를 생성하고 있습니다...")

            # 텍스트 AI를 호출해 구조화된 광고 문구를 받습니다.
            ad_copy = generate_ad_copy(
                client=client,
                brief=brief,
                model=text_model,
            )

            # 광고 문구 생성이 끝났음을 표시합니다.
            progress.progress(40, text="광고 문구 생성 완료")

        # 제품 정보와 문구로 이미지 AI 프롬프트를 만듭니다.
        image_prompt = build_image_prompt(
            brief=brief,
            ad_copy=ad_copy,
        )

        # 선택한 최종 출력 규격의 AI 생성 크기를 가져옵니다.
        output_spec = get_output_spec(brief.output_type)

        # 이미지 생성 단계임을 표시합니다.
        progress.progress(
            50,
            text="AI가 제품광고 포스터 한 장을 생성하고 있습니다...",
        )

        # 제품 사진을 참고해 광고 포스터를 생성합니다.
        generated_image = generate_poster_image(
            client=client,
            source_images=normalized_images,
            prompt=image_prompt,
            model=image_model,
            api_size=str(output_spec["api_size"]),
            quality=quality,
        )

        # 이미지 생성이 끝났음을 표시합니다.
        progress.progress(78, text="포스터 생성 완료, 인쇄 파일을 변환하고 있습니다...")

        # AI 이미지를 정확한 A4, A5 또는 SNS 규격으로 변환합니다.
        export_files = build_export_files(
            generated_image=generated_image,
            output_type=brief.output_type,
            dpi=300,
        )

        # 한 번의 작업을 구분할 고유 번호를 만듭니다.
        job_id = create_job_id()

        # 원본 사진과 결과 파일을 프로젝트 폴더에 저장합니다.
        saved_paths = save_generation_result(
            job_id=job_id,
            original_images=normalized_images,
            export_files=export_files,
            brief=brief,
            ad_copy=ad_copy,
            text_model=text_model,
            image_model=image_model,
        )

        # 화면과 JSON 다운로드에 사용할 작업 정보를 구성합니다.
        metadata = {
            "job_id": job_id,
            "product": brief.model_dump(mode="json"),
            "ad_copy": ad_copy.model_dump(mode="json"),
            "output": {
                "type": export_files["output_type"],
                "pixels": export_files["final_pixels"],
                "dpi": export_files["dpi"],
            },
            "models": {
                "text": text_model,
                "image": image_model,
            },
            "saved_files": {
                "png": str(saved_paths["png_path"]),
                "jpg": str(saved_paths["jpg_path"]),
                "pdf": str(saved_paths["pdf_path"]),
                "metadata": str(saved_paths["metadata_path"]),
            },
        }

        # Streamlit 화면이 다시 실행되어도 결과가 유지되도록 세션에 저장합니다.
        st.session_state["last_result"] = {
            "product_name": brief.product_name,
            "ad_copy": ad_copy.model_dump(mode="json"),
            "poster_png": export_files["png"],
            "poster_jpg": export_files["jpg"],
            "poster_pdf": export_files["pdf"],
            "output_type": export_files["output_type"],
            "final_pixels": export_files["final_pixels"],
            "dpi": export_files["dpi"],
            "metadata": metadata,
            "copy_signature": current_signature,
        }

        # 모든 작업이 완료되었음을 표시합니다.
        progress.progress(100, text="PNG, JPG와 PDF 저장 완료")

    finally:
        # 진행률이 끝난 뒤 화면을 깔끔하게 정리합니다.
        progress.empty()


def show_result(result: dict) -> tuple[bool, bool]:
    """결과 미리보기와 다운로드 버튼을 표시합니다."""

    # 결과 영역 제목을 표시합니다.
    st.markdown("## 3. 생성 결과")

    # 포스터와 광고 문구를 좌우로 배치합니다.
    image_column, detail_column = st.columns([1.2, 1], gap="large")

    # 왼쪽에는 생성된 포스터 한 장만 표시합니다.
    with image_column:
        st.image(
            result["poster_png"],
            caption="생성된 제품광고 포스터",
            use_container_width=True,
        )

    # 오른쪽에는 광고 문구와 다운로드 버튼을 표시합니다.
    with detail_column:
        # 결과 정보를 테두리가 있는 카드 안에 표시합니다.
        with st.container(border=True):
            # 저장된 광고 문구를 가져옵니다.
            copy_data = result["ad_copy"]

            # 광고 문구를 순서대로 보여줍니다.
            st.subheader(copy_data["title"])
            st.write(copy_data["subtitle"])
            st.write(copy_data["description"])
            st.caption(copy_data["cta"])

            # 가격이 입력된 경우에만 표시합니다.
            if copy_data["price_text"]:
                st.write(f"가격: {copy_data['price_text']}")

            # 수량이 입력된 경우에만 표시합니다.
            if copy_data["quantity_text"]:
                st.write(f"수량·구성: {copy_data['quantity_text']}")

            # 출력 규격, 픽셀과 dpi를 표시합니다.
            width, height = result["final_pixels"]
            st.write(
                f"출력: {result['output_type']} · "
                f"{width}×{height}px · {result['dpi']}dpi"
            )

            # 해시태그를 한 줄로 보여줍니다.
            st.caption(" ".join(copy_data["hashtags"]))

        # 제품명을 안전한 다운로드 파일명으로 바꿉니다.
        safe_name = (
            result["product_name"]
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )

        # PNG와 JPG 다운로드 버튼을 나란히 배치합니다.
        first_download, second_download = st.columns(2)

        # PNG 다운로드 버튼을 만듭니다.
        with first_download:
            st.download_button(
                label="PNG 다운로드",
                data=result["poster_png"],
                file_name=f"{safe_name}_poster.png",
                mime="image/png",
                use_container_width=True,
            )

        # JPG 다운로드 버튼을 만듭니다.
        with second_download:
            st.download_button(
                label="JPG 다운로드",
                data=result["poster_jpg"],
                file_name=f"{safe_name}_poster.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )

        # 인쇄용 PDF 다운로드 버튼을 만듭니다.
        st.download_button(
            label="인쇄용 PDF 다운로드",
            data=result["poster_pdf"],
            file_name=f"{safe_name}_poster.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        # 작업 정보를 한글 JSON 문자열로 만듭니다.
        metadata_json = json.dumps(
            result["metadata"],
            ensure_ascii=False,
            indent=2,
        )

        # 작업 정보 JSON 다운로드 버튼을 만듭니다.
        st.download_button(
            label="광고 문구와 설정 JSON 다운로드",
            data=metadata_json.encode("utf-8"),
            file_name=f"{safe_name}_poster_info.json",
            mime="application/json",
            use_container_width=True,
        )

        # 다시 만들 때 문구도 새로 생성할지 선택합니다.
        new_copy_on_remake = st.checkbox(
            "다시 만들 때 광고 문구도 새로 생성",
            value=False,
        )

        # 현재 위쪽의 스타일과 옵션으로 다시 만드는 버튼입니다.
        remake_clicked = st.button(
            "현재 설정으로 다시 만들기",
            type="primary",
            use_container_width=True,
            key="remake_button",
        )

        # 현재 결과를 화면에서 지우는 버튼입니다.
        if st.button(
            "현재 결과 지우기",
            use_container_width=True,
            key="clear_result_button",
        ):
            # 마지막 결과를 세션에서 삭제합니다.
            st.session_state.pop("last_result", None)

            # 화면을 새로 실행합니다.
            st.rerun()

    # 다시 만들기 클릭 여부와 문구 새 생성 여부를 반환합니다.
    return remake_clicked, new_copy_on_remake


# 프로그램 제목과 버전을 표시합니다.
st.title(APP_NAME)

# 발표용 프로그램 설명을 표시합니다.
st.write(
    "제품 사진과 정보를 입력하면 광고 문구와 제품광고 포스터 한 장을 생성하고, "
    "A4·A5 또는 SNS 규격의 PNG, JPG와 PDF로 저장합니다."
)

# 버전과 팀 이름을 작게 표시합니다.
st.markdown(
    f'<p class="small-note">Version {APP_VERSION} · {TEAM_NAME}</p>',
    unsafe_allow_html=True,
)

# 기본 API 키와 모델명을 환경설정에서 읽습니다.
default_api_key = read_default_api_key()
text_model = os.getenv("OPENAI_TEXT_MODEL", "gpt-5.6").strip()
image_model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2").strip()

# 왼쪽 사이드바에 API 설정을 표시합니다.
with st.sidebar:
    # 설정 영역 제목입니다.
    st.header("API 설정")

    # 사용자가 직접 API 키를 입력하거나 .env 값을 사용할 수 있게 합니다.
    api_key = st.text_input(
        "OpenAI API Key",
        value=default_api_key,
        type="password",
        help="키는 현재 프로그램에서 OpenAI API를 호출할 때만 사용됩니다.",
    )

    # 사용 중인 모델명을 보여줍니다.
    st.caption(f"광고 문구 모델: {text_model}")
    st.caption(f"이미지 모델: {image_model}")

    # .env 설정 방법을 접어서 안내합니다.
    with st.expander(".env 설정 방법"):
        st.code(
            'OPENAI_API_KEY="발급받은_API_키"\n'
            'OPENAI_TEXT_MODEL="gpt-5.6"\n'
            'OPENAI_IMAGE_MODEL="gpt-image-2"\n'
            'TEAM_NAME="팀 이름"',
            language="text",
        )

    # AI 이미지 결과를 반드시 확인해야 한다는 주의사항입니다.
    st.warning(
        "AI는 제품 형태와 한국어 글자를 완벽하게 유지하지 못할 수 있습니다. "
        "인쇄하거나 게시하기 전에 원본과 비교해 확인하세요."
    )

# 제품 사진 업로드 영역을 표시합니다.
st.markdown("## 1. 제품 사진 업로드")

# 제품의 앞면, 옆면과 구성품 사진을 최대 네 장까지 받습니다.
uploaded_files = st.file_uploader(
    "제품 사진을 올려주세요.",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
    help="선명한 제품 사진을 최대 4장까지 올릴 수 있습니다.",
)

# 업로드한 파일이 있으면 생성 전에도 즉시 미리보기를 보여줍니다.
if uploaded_files:
    # 업로드한 이미지 수에 맞춰 가로 열을 만듭니다.
    preview_columns = st.columns(min(len(uploaded_files), 4))

    # 각 제품 사진과 파일명을 표시합니다.
    for index, uploaded_file in enumerate(uploaded_files[:4]):
        with preview_columns[index]:
            st.image(
                uploaded_file,
                caption=uploaded_file.name,
                use_container_width=True,
            )

    # 업로드한 파일의 전체 용량을 계산합니다.
    total_size_mb = sum(
        uploaded_file.size
        for uploaded_file in uploaded_files
    ) / (1024 * 1024)

    # 업로드 개수와 용량을 간단히 표시합니다.
    st.caption(
        f"업로드 {len(uploaded_files)}개 · 전체 약 {total_size_mb:.1f}MB"
    )

# 제품 정보와 포스터 설정 영역을 표시합니다.
st.markdown("## 2. 제품과 포스터 설정")

# 제품명, 브랜드와 가격 입력창을 가로로 배치합니다.
name_column, brand_column, price_column = st.columns(3)

# 제품명은 필수 입력입니다.
with name_column:
    product_name = st.text_input(
        "제품명 *",
        placeholder="예: 캐릭터 텀블러",
    )

# 브랜드명은 선택 입력입니다.
with brand_column:
    brand_name = st.text_input(
        "브랜드명",
        placeholder="브랜드가 없으면 비워두세요.",
    )

# 가격은 선택 입력입니다.
with price_column:
    price = st.text_input(
        "가격",
        placeholder="예: 17,900원",
    )

# 수량, 카테고리와 주요 고객을 가로로 배치합니다.
quantity_column, category_column, customer_column = st.columns(3)

# 수량이나 구성은 선택 입력입니다.
with quantity_column:
    quantity = st.text_input(
        "수량·구성",
        placeholder="예: 1세트 또는 1박스 20개",
    )

# 제품 카테고리를 선택합니다.
with category_column:
    category = st.selectbox(
        "제품 카테고리",
        CATEGORIES,
    )

# 광고의 주요 고객을 선택합니다.
with customer_column:
    target_customer = st.selectbox(
        "주요 고객",
        TARGET_CUSTOMERS,
    )

# 실제로 확인한 제품 특징을 입력합니다.
features = st.text_area(
    "제품 특징 *",
    placeholder=(
        "실제로 확인된 내용만 입력하세요.\n"
        "예: 빨대와 뚜껑 포함, 여러 캐릭터 디자인, 휴대하기 좋은 크기"
    ),
    height=120,
)

# 사용 목적과 포스터 스타일을 가로로 배치합니다.
usage_column, style_column = st.columns(2)

# 포스터가 사용될 목적을 선택합니다.
with usage_column:
    usage = st.selectbox(
        "사용 목적",
        USAGE_OPTIONS,
    )

# 생성할 포스터 스타일을 선택합니다.
with style_column:
    style = st.selectbox(
        "포스터 스타일",
        POSTER_STYLES,
    )

# 색감, 배경과 글자 양을 가로로 배치합니다.
color_column, background_column, text_column = st.columns(3)

# 포스터 전체 색감을 선택합니다.
with color_column:
    color_tone = st.selectbox(
        "전체 색감",
        COLOR_TONES,
    )

# 포스터 배경 분위기를 선택합니다.
with background_column:
    background_type = st.selectbox(
        "배경 분위기",
        BACKGROUND_TYPES,
    )

# 포스터 안에 들어갈 글자 양을 선택합니다.
with text_column:
    text_amount = st.selectbox(
        "포스터 글자 양",
        TEXT_AMOUNTS,
        index=1,
    )

# 최종 출력 규격과 이미지 생성 품질을 가로로 배치합니다.
output_column, quality_column = st.columns(2)

# A4, A5 또는 SNS 규격을 선택합니다.
with output_column:
    output_type = st.selectbox(
        "최종 출력 규격",
        OUTPUT_TYPES,
    )

# 이미지 생성 품질을 선택합니다.
with quality_column:
    quality_label = st.selectbox(
        "이미지 생성 품질",
        list(QUALITY_MAP.keys()),
        index=0,
    )

# 추가로 원하는 디자인 요청을 입력합니다.
extra_request = st.text_area(
    "추가 요청",
    placeholder=(
        "예: 제품은 중앙에 크게, 배경은 연한 베이지, "
        "제목은 위쪽, 가격은 오른쪽 아래에 배치"
    ),
    height=90,
)

# 처음 포스터를 생성하는 버튼입니다.
generate_clicked = st.button(
    "AI 제품광고 포스터 생성",
    type="primary",
    use_container_width=True,
    key="generate_button",
)

# 처음 생성 버튼을 누른 경우에만 필수값을 확인하고 ProductBrief를 만듭니다.
if generate_clicked:
    # 현재 입력값에 문제가 있는지 확인합니다.
    validation_error = validate_inputs(
        api_key=api_key,
        product_name=product_name,
        features=features,
        uploaded_files=uploaded_files,
    )

    # 문제가 있으면 API를 호출하지 않고 오류를 표시합니다.
    if validation_error:
        st.error(validation_error)
    else:
        try:
            # 검사를 통과한 현재 입력값을 ProductBrief 객체로 묶습니다.
            brief = create_brief(
                product_name=product_name,
                brand_name=brand_name,
                price=price,
                quantity=quantity,
                features=features,
                category=category,
                target_customer=target_customer,
                usage=usage,
                style=style,
                color_tone=color_tone,
                background_type=background_type,
                text_amount=text_amount,
                output_type=output_type,
                extra_request=extra_request,
            )

            # 첫 생성이므로 광고 문구도 새로 생성합니다.
            perform_generation(
                api_key=api_key,
                brief=brief,
                uploaded_files=uploaded_files,
                text_model=text_model,
                image_model=image_model,
                quality=QUALITY_MAP[quality_label],
                reuse_copy_when_possible=False,
            )

            # 완료 메시지를 표시합니다.
            st.success("제품광고 포스터 생성이 완료되었습니다.")

        # API 키가 잘못된 경우를 처리합니다.
        except AuthenticationError:
            st.error("OpenAI API Key가 올바르지 않습니다. 키를 다시 확인해 주세요.")

        # API 사용 한도나 호출 제한 오류를 처리합니다.
        except RateLimitError:
            st.error(
                "OpenAI API 사용 한도 또는 호출 제한에 도달했습니다. "
                "API 결제와 사용량을 확인해 주세요."
            )

        # 인터넷 연결 오류를 처리합니다.
        except APIConnectionError:
            st.error("OpenAI 서버에 연결하지 못했습니다. 인터넷 연결을 확인해 주세요.")

        # API 응답 시간이 너무 길어진 경우를 처리합니다.
        except APITimeoutError:
            st.error("AI 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.")

        # 잘못된 요청, 모델 권한 또는 이미지 형식 오류를 처리합니다.
        except BadRequestError as error:
            st.error(
                "OpenAI API가 요청을 처리하지 못했습니다. "
                "모델 사용 권한과 입력 이미지 형식을 확인해 주세요."
            )

            # 오류 내용을 복사할 수 있도록 상세 정보를 표시합니다.
            with st.expander("상세 오류 보기"):
                st.code(str(error))

        # 그 밖의 예기치 못한 오류도 앱이 종료되지 않게 처리합니다.
        except Exception as error:
            st.error("포스터 생성 중 예상하지 못한 오류가 발생했습니다.")

            # 정확한 오류 내용을 접어서 표시합니다.
            with st.expander("상세 오류 보기"):
                st.code(str(error))

# 이전에 생성한 결과가 세션에 있으면 화면 아래에 표시합니다.
if "last_result" in st.session_state:
    # 입력 영역과 결과 영역 사이에 구분선을 표시합니다.
    st.divider()

    # 결과를 표시하고 다시 만들기 선택값을 받습니다.
    remake_clicked, new_copy_on_remake = show_result(
        st.session_state["last_result"]
    )

    # 사용자가 위의 옵션을 변경한 뒤 다시 만들기를 누른 경우입니다.
    if remake_clicked:
        # 현재 입력값을 다시 확인합니다.
        validation_error = validate_inputs(
            api_key=api_key,
            product_name=product_name,
            features=features,
            uploaded_files=uploaded_files,
        )

        # 필수값에 문제가 있으면 재생성하지 않습니다.
        if validation_error:
            st.error(validation_error)
        else:
            try:
                # 현재 입력값으로 새 ProductBrief 객체를 만듭니다.
                brief = create_brief(
                    product_name=product_name,
                    brand_name=brand_name,
                    price=price,
                    quantity=quantity,
                    features=features,
                    category=category,
                    target_customer=target_customer,
                    usage=usage,
                    style=style,
                    color_tone=color_tone,
                    background_type=background_type,
                    text_amount=text_amount,
                    output_type=output_type,
                    extra_request=extra_request,
                )

                # 체크하지 않았다면 제품 정보가 같을 때 기존 문구를 유지합니다.
                perform_generation(
                    api_key=api_key,
                    brief=brief,
                    uploaded_files=uploaded_files,
                    text_model=text_model,
                    image_model=image_model,
                    quality=QUALITY_MAP[quality_label],
                    reuse_copy_when_possible=not new_copy_on_remake,
                )

                # 새 결과를 깨끗하게 표시하기 위해 화면을 다시 실행합니다.
                st.rerun()

            # API 키 오류를 처리합니다.
            except AuthenticationError:
                st.error("OpenAI API Key가 올바르지 않습니다.")

            # API 한도 오류를 처리합니다.
            except RateLimitError:
                st.error("OpenAI API 사용 한도 또는 호출 제한에 도달했습니다.")

            # 인터넷 연결 오류를 처리합니다.
            except APIConnectionError:
                st.error("OpenAI 서버에 연결하지 못했습니다.")

            # API 시간 초과 오류를 처리합니다.
            except APITimeoutError:
                st.error("AI 응답 시간이 초과되었습니다.")

            # 요청 오류의 상세 내용을 표시합니다.
            except BadRequestError as error:
                st.error("이미지를 다시 만드는 중 API 요청 오류가 발생했습니다.")

                with st.expander("상세 오류 보기"):
                    st.code(str(error))

            # 예상하지 못한 나머지 오류를 처리합니다.
            except Exception as error:
                st.error("이미지를 다시 만드는 중 오류가 발생했습니다.")

                with st.expander("상세 오류 보기"):
                    st.code(str(error))
