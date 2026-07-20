"""사용자 입력값과 AI 광고 문구의 데이터 형식을 정의합니다."""

# 입력값과 AI 결과를 자동 검사하기 위해 Pydantic을 불러옵니다.
from pydantic import BaseModel, ConfigDict, Field


class ProductBrief(BaseModel):
    """사용자가 입력한 제품 정보와 포스터 옵션을 한 묶음으로 관리합니다."""

    # 모든 문자열의 앞뒤 공백을 자동으로 제거합니다.
    model_config = ConfigDict(str_strip_whitespace=True)

    # 포스터의 핵심 제품명입니다.
    product_name: str = Field(min_length=1, max_length=100)

    # 브랜드가 없을 수도 있으므로 빈 문자열을 허용합니다.
    brand_name: str = Field(default="", max_length=100)

    # 가격은 선택 입력입니다.
    price: str = Field(default="", max_length=50)

    # 수량이나 구성은 선택 입력입니다.
    quantity: str = Field(default="", max_length=80)

    # 사용자가 확인한 실제 제품 특징입니다.
    features: str = Field(min_length=1, max_length=1200)

    # 제품 종류입니다.
    category: str = Field(min_length=1, max_length=50)

    # 광고의 주요 고객입니다.
    target_customer: str = Field(min_length=1, max_length=100)

    # 포스터 사용 목적입니다.
    usage: str = Field(min_length=1, max_length=100)

    # 사용자가 선택한 포스터 스타일입니다.
    style: str = Field(min_length=1, max_length=100)

    # 포스터 전체 색감입니다.
    color_tone: str = Field(min_length=1, max_length=100)

    # 포스터 배경 분위기입니다.
    background_type: str = Field(min_length=1, max_length=100)

    # 포스터 안에 들어갈 글자 양입니다.
    text_amount: str = Field(min_length=1, max_length=50)

    # A4, A5 또는 SNS 등 최종 출력 규격입니다.
    output_type: str = Field(min_length=1, max_length=50)

    # 사용자가 추가로 입력한 디자인 요청입니다.
    extra_request: str = Field(default="", max_length=1200)

    # 참조할 이미지 링크입니다. 필수 입력이 아니므로 빈 문자열을 허용합니다.
    reference_image_link: str = Field(default="", max_length=500)


class AdCopy(BaseModel):
    """텍스트 AI가 반환해야 하는 광고 문구의 정확한 형식입니다."""

    # 포스터에서 가장 크게 표시할 제목입니다.
    title: str = Field(min_length=1, max_length=40)

    # 제목을 보충하는 짧은 문구입니다.
    subtitle: str = Field(min_length=1, max_length=60)

    # 실제 제품 특징을 바탕으로 만든 짧은 설명입니다.
    description: str = Field(min_length=1, max_length=140)

    # 구매나 문의를 유도하는 짧은 문구입니다.
    cta: str = Field(min_length=1, max_length=30)

    # 작은 강조 배지에 사용할 문구입니다.
    badge: str = Field(min_length=1, max_length=24)

    # 가격이 입력되지 않은 경우 빈 문자열을 허용합니다.
    price_text: str = Field(default="", max_length=50)

    # 수량이 입력되지 않은 경우 빈 문자열을 허용합니다.
    quantity_text: str = Field(default="", max_length=80)

    # 결과 화면에 표시할 한글 해시태그입니다.
    hashtags: list[str] = Field(min_length=3, max_length=5)

    # 이미지 생성 API에 실제 전달된 최종 프롬프트를 저장합니다.
    generated_prompt: str = Field(default="")
