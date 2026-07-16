"""OpenAI 텍스트 모델을 호출해 구조화된 광고 문구를 만듭니다."""

# OpenAI API 클라이언트 자료형을 불러옵니다.
from openai import OpenAI

# 제품 입력과 광고 문구 데이터 형식을 불러옵니다.
from models import AdCopy, ProductBrief

# 광고 문구용 시스템 규칙과 사용자 프롬프트 함수를 불러옵니다.
from prompt_service import COPY_SYSTEM_PROMPT, build_copy_user_prompt


def generate_ad_copy(
    client: OpenAI,
    brief: ProductBrief,
    model: str,
) -> AdCopy:
    """제품 정보를 바탕으로 정해진 형식의 광고 문구를 생성합니다."""

    # Responses API의 구조화 출력 기능으로 AdCopy 형식의 응답을 받습니다.
    response = client.responses.parse(
        # 환경설정에 지정된 텍스트 모델을 사용합니다.
        model=model,
        # 시스템 규칙과 실제 제품 정보를 차례대로 전달합니다.
        input=[
            {
                "role": "system",
                "content": COPY_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_copy_user_prompt(brief),
            },
        ],
        # 응답 형식을 Pydantic AdCopy 모델로 고정합니다.
        text_format=AdCopy,
    )

    # 정상적인 구조화 결과가 없으면 오류를 발생시킵니다.
    if response.output_parsed is None:
        raise RuntimeError("광고 문구를 정해진 형식으로 받지 못했습니다.")

    # 검사가 완료된 광고 문구를 반환합니다.
    return response.output_parsed
