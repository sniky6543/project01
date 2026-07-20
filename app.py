"""AI 제품광고 포스터 생성기의 Streamlit 메인 화면입니다."""

# 업로드 사진을 브라우저용 미리보기 데이터로 변환하기 위해 불러옵니다.
import base64

# 파일명을 HTML에 안전하게 표시하기 위해 불러옵니다.
import html

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

# 업로드 사진의 표시 전용 갤러리를 격리된 HTML로 만들기 위해 불러옵니다.
import streamlit.components.v1 as components

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

# 브라우저 탭 제목, 아이콘과 넓은 화면 구성을 설정합니다.
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 화면의 폭과 버튼 모양을 보기 좋게 조절합니다.
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&family=Playfair+Display:wght@700;800&display=swap');

        :root {
            --app-bg: #f3f6fb;
            --surface: #ffffff;
            --panel: #ffffff;
            --panel-strong: #f7f9fd;
            --ink: #182033;
            --muted: #647087;
            --subtle: #8792a8;
            --line: #dce3ef;
            --line-strong: #c8d3e5;
            --accent: #3157e7;
            --accent-hover: #2446c7;
            --accent-soft: #eef2ff;
            --required: #c43d45;
            --radius-sm: 6px;
            --radius-md: 8px;
            --space-1: 4px;
            --space-2: 8px;
            --space-3: 12px;
            --space-4: 16px;
            --space-5: 20px;
            --space-6: 24px;
            --space-7: 28px;
            --font-xs: 0.78rem;
            --font-sm: 0.86rem;
            --font-md: 0.94rem;
            --control-height: 42px;
        }

        *, *::before, *::after {
            box-sizing: border-box;
        }

        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background: var(--app-bg) !important;
            color: var(--ink);
            font-family: 'Noto Sans KR', Arial, sans-serif;
        }

        [data-testid="stHeader"],
        [data-testid="stToolbar"] {
            height: 0;
            visibility: hidden;
        }

        .block-container {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: var(--radius-md);
            box-shadow: 0 2px 10px rgba(34, 55, 92, 0.05);
            margin: var(--space-3) auto var(--space-6);
            max-width: 1140px;
            padding: var(--space-6);
            width: calc(100% - 24px);
        }

        [data-testid="stMain"] [data-testid="stVerticalBlock"] {
            gap: var(--space-3) !important;
        }

        [data-testid="stSidebar"] {
            background: #f7f9fd;
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebar"] * {
            box-sizing: border-box;
            min-width: 0;
        }

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] summary {
            overflow-wrap: anywhere;
            word-break: keep-all;
        }

        [data-testid="stSidebarHeader"] {
            display: none !important;
        }

        [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            padding: var(--space-6);
        }

        [data-testid="stSidebarUserContent"] {
            padding-bottom: 0 !important;
            width: 100%;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: var(--space-4);
        }

        [data-testid="stSidebar"] h2 {
            align-items: center;
            color: var(--ink);
            display: grid;
            font-size: 1.12rem;
            font-weight: 700;
            grid-template-columns: 44px minmax(0, 1fr);
            grid-template-rows: auto auto;
            line-height: 1.25;
            margin: 0 0 var(--space-5);
            padding: 0;
        }

        [data-testid="stSidebar"] h2::before {
            align-items: center;
            align-self: stretch;
            background: var(--accent);
            border-radius: 10px;
            color: #ffffff;
            content: "✦";
            display: flex;
            font-size: 1.1rem;
            grid-column: 1;
            grid-row: 1 / span 2;
            justify-content: center;
            margin-right: var(--space-3);
            min-height: 44px;
        }

        [data-testid="stSidebar"] h2::after {
            color: var(--muted);
            content: "외부 API 연동을 설정하세요.";
            font-size: var(--font-xs);
            font-weight: 500;
            grid-column: 2;
            grid-row: 2;
            line-height: 1.45;
            margin-top: 2px;
        }

        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            font-size: var(--font-sm);
            font-weight: 600;
        }

        [data-testid="stSidebar"] [data-testid="stTextInput"] {
            height: auto !important;
            min-height: 0 !important;
        }

        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
            color: var(--muted);
            font-size: var(--font-xs);
            line-height: 1.5;
        }

        [data-testid="stSidebar"] [data-testid="stExpander"] {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: var(--radius-sm);
            box-shadow: 0 1px 2px rgba(35, 58, 97, 0.03);
            width: 100%;
        }

        [data-testid="stSidebar"] [data-testid="stAlert"],
        [data-testid="stSidebar"] [data-testid="stAlertContainer"],
        [data-testid="stSidebar"] [role="alert"] {
            background: var(--surface) !important;
            border-color: #d9e2f4 !important;
            border-radius: var(--radius-sm) !important;
            color: var(--muted) !important;
            width: 100%;
        }

        .app-hero {
            align-items: flex-start;
            background: var(--surface);
            border-bottom: 1px solid var(--line);
            display: flex;
            justify-content: space-between;
            margin-bottom: var(--space-5);
            padding: 0 0 var(--space-4);
        }

        .app-title {
            color: var(--ink);
            font-family: 'Noto Sans KR', Arial, sans-serif !important;
            font-size: 2.35rem;
            font-weight: 800;
            letter-spacing: 0;
            line-height: 1.2;
            margin: 0;
            padding: 0 !important;
        }

        .app-subtitle {
            color: var(--muted);
            font-size: var(--font-md);
            line-height: 1.55;
            margin: var(--space-2) 0 0;
        }

        .studio-badge {
            align-items: center;
            background: var(--surface);
            border: 1px solid #d8e1f6;
            border-radius: 999px;
            color: #33405a;
            display: flex;
            font-size: var(--font-xs);
            font-weight: 600;
            gap: var(--space-2);
            padding: 7px 10px;
            white-space: nowrap;
        }

        .studio-badge > b {
            color: var(--accent);
            font-size: 0.95rem;
        }

        .studio-badge > em {
            background: var(--accent-soft);
            border-radius: 999px;
            color: var(--accent);
            font-style: normal;
            padding: 2px 7px;
        }

        [data-testid="stHorizontalBlock"]:has(.panel-marker) {
            align-items: stretch;
            gap: var(--space-5);
        }

        [data-testid="stColumn"]:has(.panel-marker) {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: var(--radius-md);
            box-shadow: 0 2px 8px rgba(35, 58, 97, 0.035);
            min-width: 0;
            padding: var(--space-5);
        }

        [data-testid="stColumn"]:has(.panel-result) {
            background: var(--surface);
            border-color: #cbd8f4;
            box-shadow: 0 3px 12px rgba(49, 87, 231, 0.07);
        }

        .panel-marker {
            display: none;
        }

        .section-heading {
            align-items: center;
            display: flex;
            gap: var(--space-3);
            margin: 0 0 var(--space-5);
            min-height: 28px;
            text-transform: uppercase;
        }

        .section-heading.lower {
            margin-bottom: var(--space-5);
        }

        .section-heading .number {
            align-items: center;
            background: var(--accent);
            border-radius: var(--radius-sm);
            box-shadow: 0 3px 8px rgba(49, 87, 231, 0.18);
            color: #ffffff;
            display: inline-flex;
            font-family: 'Noto Sans KR', Arial, sans-serif;
            font-size: 0.82rem;
            font-weight: 700;
            height: 30px;
            justify-content: center;
            line-height: 30px;
            min-width: 30px;
            padding: 0 6px;
        }

        .section-heading .label {
            color: var(--ink);
            font-family: 'Noto Sans KR', Arial, sans-serif;
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.15;
        }

        .content-rule {
            border: 0;
            margin: var(--space-5) 0 !important;
        }

        .field-label {
            color: #34383d;
            font-size: var(--font-sm);
            font-weight: 600;
            line-height: var(--control-height);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .field-label.required::after {
            color: var(--required);
            content: " *";
        }

        .feature-label {
            line-height: 1.4;
            padding-top: var(--space-3);
        }

        .product-label-stack {
            display: grid;
            grid-template-rows: repeat(6, var(--control-height)) 108px;
            row-gap: 10px;
        }

        .product-label-stack .field-label {
            line-height: var(--control-height);
        }

        .product-label-stack .feature-label {
            line-height: 1.4;
            padding-top: var(--space-3);
        }

        .art-label-stack {
            display: grid;
            grid-template-rows: repeat(7, var(--control-height));
            row-gap: 10px;
        }

        .art-label-stack .field-label {
            line-height: var(--control-height);
        }

        .art-extra-label {
            border-top: 1px solid var(--line);
            color: #34383d;
            font-size: var(--font-sm);
            font-weight: 600;
            margin-top: var(--space-2);
            padding-top: var(--space-4);
        }

        [data-testid="stFileUploader"] {
            background: transparent;
            border: 0;
            padding: 0;
        }

        [data-testid="stFileUploader"] > label {
            color: var(--ink);
            display: block;
            font-size: var(--font-md);
            font-weight: 600;
            margin-bottom: var(--space-3);
        }

        [data-testid="stFileUploader"] section {
            align-items: center;
            background: var(--surface);
            border: 1.5px dashed #9fb4f4;
            border-radius: var(--radius-md);
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 230px;
            padding: var(--space-7);
            text-align: center;
            transition: background-color 160ms ease, border-color 160ms ease;
        }

        [data-testid="stFileUploader"] section:hover {
            background: #f8faff;
            border-color: var(--accent);
        }

        [data-testid="stFileUploader"] section:has([data-testid="stFileChip"]) {
            min-height: 160px;
            padding: var(--space-4);
        }

        [data-testid="stFileUploader"] section:has([data-testid="stFileChip"])::before {
            display: none;
        }

        [data-testid="stFileUploader"] section::before {
            align-items: center;
            background: var(--accent-soft);
            border: 1px solid #cdd8ff;
            border-radius: 50%;
            color: var(--accent);
            content: "↑";
            display: flex;
            font-size: 1.25rem;
            font-weight: 600;
            height: 44px;
            justify-content: center;
            margin-bottom: var(--space-3);
            width: 44px;
        }

        [data-testid="stFileUploader"] button {
            background: var(--surface);
            border: 1px solid var(--line-strong);
            border-radius: var(--radius-sm);
            color: var(--ink);
            font-weight: 600;
            min-height: 38px;
        }

        [data-testid="stFileUploader"] button:hover {
            background: var(--accent-soft);
            border-color: var(--accent);
            color: var(--accent);
        }

        [data-testid="stFileUploader"] section > button {
            font-size: 0;
        }

        [data-testid="stFileUploader"] section > button::after {
            content: "업로드";
            font-size: var(--font-sm);
        }

        [data-testid="stFileUploaderDropzoneInstructions"] {
            font-size: 0;
        }

        [data-testid="stFileUploaderDropzoneInstructions"]::before {
            color: var(--ink);
            content: "사진을 끌어놓거나 업로드 버튼을 눌러주세요.";
            display: block;
            font-size: var(--font-sm);
            font-weight: 600;
            line-height: 1.5;
        }

        [data-testid="stFileUploaderDropzoneInstructions"]::after {
            color: var(--muted);
            content: "PNG, JPG, WEBP 파일 · 최대 4장";
            display: block;
            font-size: var(--font-xs);
            line-height: 1.5;
            margin-top: var(--space-1);
        }

        [data-testid="stImage"] img {
            background: var(--panel-strong);
            border: 1px solid var(--line);
            border-radius: var(--radius-sm);
        }

        [data-testid="stForm"],
        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 0 !important;
            border-radius: var(--radius-sm);
            padding: 0 !important;
        }

        label,
        [data-testid="stWidgetLabel"] p {
            color: #34383d;
            font-size: var(--font-sm);
            font-weight: 600;
        }

        [data-testid="stTextInput"],
        [data-testid="stSelectbox"] {
            height: var(--control-height) !important;
            min-height: var(--control-height) !important;
        }

        [data-testid="stSelectbox"] [role="group"] {
            background: var(--surface) !important;
            border: 1px solid var(--line-strong) !important;
            border-radius: var(--radius-sm) !important;
            height: var(--control-height) !important;
            min-height: var(--control-height) !important;
            transition: border-color 150ms ease, box-shadow 150ms ease, background-color 150ms ease;
        }

        [data-testid="stSelectbox"] [role="group"]:hover {
            border-color: #9caed0 !important;
        }

        [data-testid="stSelectbox"] [role="group"]:focus-within {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px rgba(49, 87, 231, 0.12) !important;
        }

        div[data-baseweb="input"],
        div[data-baseweb="select"],
        div[data-baseweb="select"] > div,
        [data-testid="stTextInputRootElement"],
        [data-testid="stSelectboxRootElement"] {
            background: var(--surface) !important;
            border-color: var(--line-strong) !important;
            border-radius: var(--radius-sm) !important;
            box-shadow: none !important;
            height: var(--control-height) !important;
            min-height: var(--control-height) !important;
            transition: border-color 150ms ease, box-shadow 150ms ease, background-color 150ms ease;
        }

        input,
        textarea {
            color: var(--ink) !important;
            font-size: var(--font-sm) !important;
        }

        input::placeholder,
        textarea::placeholder {
            color: #9aa1aa !important;
            opacity: 1;
        }

        [data-testid="stTextAreaRootElement"],
        textarea {
            background: var(--surface) !important;
            border-color: var(--line-strong) !important;
            border-radius: var(--radius-sm) !important;
            box-shadow: none !important;
            min-height: 100px !important;
            transition: border-color 150ms ease, box-shadow 150ms ease, background-color 150ms ease;
        }

        div[data-baseweb="input"]:hover,
        div[data-baseweb="select"] > div:hover,
        [data-testid="stTextInputRootElement"]:hover,
        [data-testid="stSelectboxRootElement"]:hover,
        [data-testid="stTextAreaRootElement"]:hover {
            border-color: #9ca4ad !important;
        }

        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="select"] > div:focus-within,
        [data-testid="stTextInputRootElement"]:focus-within,
        [data-testid="stSelectboxRootElement"]:focus-within,
        [data-testid="stTextAreaRootElement"]:focus-within {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px rgba(49, 87, 231, 0.12) !important;
        }

        input:focus,
        textarea:focus,
        [role="combobox"]:focus {
            border-radius: var(--radius-sm);
            outline: 2px solid rgba(49, 87, 231, 0.24) !important;
            outline-offset: -2px;
        }

        input:disabled,
        textarea:disabled,
        [aria-disabled="true"] {
            background: #eef0f2 !important;
            color: var(--subtle) !important;
            cursor: not-allowed !important;
        }

        div.stButton > button,
        div.stDownloadButton > button {
            border-radius: var(--radius-sm);
            font-weight: 600;
            letter-spacing: 0;
            min-height: 46px;
            transition: background-color 150ms ease, border-color 150ms ease, transform 100ms ease;
        }

        div.stButton > button[kind="primary"] {
            background: var(--accent);
            border-color: var(--accent);
            color: var(--surface);
            min-height: 50px;
            box-shadow: 0 6px 14px rgba(49, 87, 231, 0.18);
        }

        div.stButton > button[kind="primary"]:hover {
            background: var(--accent-hover);
            border-color: var(--accent-hover);
            color: var(--surface);
        }

        div.stButton > button[kind="primary"]:active {
            background: #1d3bae;
            border-color: #1d3bae;
        }

        div.stDownloadButton > button {
            background: var(--surface);
            border-color: var(--line-strong);
            color: var(--ink);
        }

        div.stDownloadButton > button:hover {
            background: var(--accent-soft);
            border-color: var(--accent);
            color: var(--accent);
        }

        div[data-testid="stAlert"] {
            background: var(--surface) !important;
            border: 1px solid var(--line) !important;
            border-radius: var(--radius-sm);
            color: var(--muted) !important;
        }

        /* 생성 완료 상태: 포스터를 중심에 두고 정보와 후속 작업을 한 흐름으로 묶습니다. */
        [data-testid="stColumn"]:has(.panel-result) [data-testid="stImage"] {
            background: #f4f6fa;
            border: 1px solid var(--line);
            border-radius: var(--radius-sm);
            overflow: hidden;
            padding: var(--space-2);
        }

        [data-testid="stColumn"]:has(.panel-result) [data-testid="stImage"] img {
            border-radius: 4px;
            display: block;
            width: 100%;
        }

        [data-testid="stColumn"]:has(.panel-result) [data-testid="stImageCaption"] {
            color: var(--muted);
            font-size: var(--font-xs);
            padding: var(--space-2) var(--space-1) 0;
            text-align: left;
        }

        [data-testid="stColumn"]:has(.panel-result) [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--panel-strong);
            border: 1px solid var(--line) !important;
            border-radius: var(--radius-sm);
            box-shadow: none;
        }

        [data-testid="stColumn"]:has(.panel-result) [data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: var(--space-4);
        }

        [data-testid="stColumn"]:has(.panel-result) [data-testid="stVerticalBlockBorderWrapper"] h3 {
            color: var(--ink);
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.18rem;
            line-height: 1.3;
            margin-bottom: var(--space-2);
        }

        [data-testid="stColumn"]:has(.panel-result) [data-testid="stVerticalBlockBorderWrapper"] p {
            color: #455168;
            font-size: var(--font-xs);
            line-height: 1.55;
        }

        [data-testid="stColumn"]:has(.panel-result) div.stDownloadButton > button {
            background: var(--surface);
            border-color: var(--line-strong);
            color: #263148;
            font-size: var(--font-xs);
            min-height: 42px;
            padding: 8px 10px;
            width: 100%;
        }

        [data-testid="stColumn"]:has(.panel-result) div.stDownloadButton > button:hover {
            background: var(--accent-soft);
            border-color: var(--accent);
            color: var(--accent);
        }

        [data-testid="stColumn"]:has(.panel-result) [data-testid="stCheckbox"] {
            background: #f8faff;
            border: 1px solid var(--line);
            border-radius: var(--radius-sm);
            padding: 10px 12px;
        }

        [data-testid="stColumn"]:has(.panel-result) [data-testid="stCheckbox"] label {
            align-items: flex-start;
            color: #3c475c;
            font-size: var(--font-xs);
            line-height: 1.45;
        }

        [data-testid="stColumn"]:has(.panel-result) div.stButton > button {
            font-size: var(--font-xs);
            min-height: 44px;
            width: 100%;
        }

        [data-testid="stColumn"]:has(.panel-result) div.stButton > button:not([kind="primary"]) {
            background: var(--surface);
            border-color: var(--line-strong);
            color: var(--muted);
        }

        [data-testid="stColumn"]:has(.panel-result) div.stButton > button:not([kind="primary"]):hover {
            background: #f7f8fb;
            border-color: #aebbd0;
            color: var(--ink);
        }

        .result-empty {
            align-items: center;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 480px;
            padding: var(--space-4) 0 var(--space-3);
            text-align: center;
        }

        .poster-placeholder {
            aspect-ratio: 4 / 5;
            background: #f8faff;
            border: 1px solid #d5def5;
            border-radius: var(--radius-sm);
            display: flex;
            flex-direction: column;
            gap: 14px;
            justify-content: space-between;
            max-width: 250px;
            padding: 24px;
            position: relative;
            width: min(52%, 250px);
        }

        .poster-placeholder::before,
        .poster-placeholder::after {
            background: #dfe3e7;
            border-radius: 2px;
            content: "";
            display: block;
            height: 9px;
        }

        .poster-placeholder::before {
            width: 58%;
        }

        .poster-placeholder::after {
            width: 76%;
        }

        .poster-placeholder-visual {
            align-items: center;
            background: var(--accent-soft);
            border: 1px solid #d5defb;
            border-radius: 4px;
            color: #91a5e9;
            display: flex;
            flex: 1;
            font-family: 'Noto Sans KR', Arial, sans-serif;
            font-size: var(--font-sm);
            font-weight: 600;
            justify-content: center;
        }

        .result-empty-title {
            color: var(--ink);
            font-size: var(--font-md);
            font-weight: 600;
            margin: var(--space-5) 0 var(--space-1);
        }

        .result-empty-note {
            color: var(--subtle);
            font-size: var(--font-xs);
            margin: 0;
        }

        @media (min-width: 1101px) {
            [data-testid="stSidebar"] {
                max-width: 288px !important;
                min-width: 288px !important;
            }
        }

        @media (max-width: 1100px) {
            .block-container {
                margin: var(--space-3) auto;
                max-width: none;
                padding: var(--space-5);
                width: calc(100% - 24px);
            }

            [data-testid="stHorizontalBlock"]:has(.panel-marker) {
                flex-direction: column !important;
            }

            [data-testid="stHorizontalBlock"]:has(.panel-marker) > [data-testid="stColumn"] {
                flex: 1 1 auto !important;
                width: 100% !important;
            }

            .content-rule {
                margin: var(--space-4) 0 !important;
            }
        }

        @media (min-width: 901px) and (max-width: 1100px) {
            [data-testid="stSidebar"] {
                flex: 0 0 260px !important;
                max-width: 260px !important;
                min-width: 260px !important;
                width: 260px !important;
            }

            [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
                padding-left: var(--space-4);
                padding-right: var(--space-4);
            }

            [data-testid="stMain"] {
                flex: 1 1 auto !important;
                min-width: 0 !important;
                position: relative !important;
                width: auto !important;
            }
        }

        @media (max-width: 900px) {
            [data-testid="stAppViewContainer"] {
                display: block !important;
                min-height: 100vh;
                position: relative !important;
            }

            [data-testid="stSidebar"] {
                height: auto !important;
                max-width: none !important;
                min-height: 0 !important;
                min-width: 0 !important;
                position: static !important;
                width: 100% !important;
            }

            [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
                height: auto !important;
                max-width: none;
                padding: var(--space-5);
                width: 100%;
            }

            [data-testid="stSidebarUserContent"] {
                padding-bottom: 0 !important;
                width: 100%;
            }

            [data-testid="stMain"] {
                height: auto !important;
                left: 0 !important;
                min-height: 0 !important;
                position: static !important;
                width: 100% !important;
            }

            .block-container {
                margin: var(--space-2) auto;
                padding: var(--space-4);
                width: calc(100% - 16px);
            }

            .app-title {
                font-size: 2rem;
            }

            [data-testid="stColumn"]:has(.panel-marker) {
                padding: var(--space-5);
            }

            [data-testid="stFileUploader"] section {
                min-height: 210px;
            }

            [data-testid="stFileUploader"] section:has([data-testid="stFileChip"]) {
                min-height: 160px;
            }

            .result-empty {
                min-height: 430px;
            }

        }

        @media (max-width: 700px) {
            .app-title {
                font-size: 1.7rem;
            }

            .section-heading .label {
                font-size: 0.98rem;
            }

            .studio-badge {
                display: none;
            }

            [data-testid="stColumn"]:has(.panel-result) [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }

            [data-testid="stColumn"]:has(.panel-result) [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
                flex: 1 1 auto !important;
                width: 100% !important;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def build_upload_preview_gallery(uploaded_files: list) -> str:
    """업로드 파일을 생성 로직과 분리된 선택형 미리보기 HTML로 만듭니다."""

    large_previews = []
    thumbnail_controls = []

    for index, uploaded_file in enumerate(uploaded_files[:4]):
        preview_id = f"upload-preview-{index}"
        checked = " checked" if index == 0 else ""
        file_name = html.escape(uploaded_file.name)
        mime_type = html.escape(uploaded_file.type or "image/jpeg", quote=True)
        encoded_image = base64.b64encode(uploaded_file.getvalue()).decode("ascii")
        image_source = f"data:{mime_type};base64,{encoded_image}"

        large_previews.append(
            '<figure class="upload-preview-large">'
            f'<img src="{image_source}" alt="{file_name}">'
            f'<figcaption>{file_name}</figcaption>'
            '</figure>'
        )
        thumbnail_controls.append(
            f'<label class="upload-preview-thumb" title="{file_name}">'
            f'<input class="upload-preview-radio" type="radio" '
            f'name="upload-preview" id="{preview_id}"{checked}>'
            f'<img src="{image_source}" alt="{file_name} 미리보기">'
            f'<span>{file_name}</span>'
            '</label>'
        )

    return f"""
        <!doctype html>
        <html lang="ko">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * {{ box-sizing: border-box; }}
                html, body {{ margin: 0; padding: 0; background: transparent; }}
                body {{ color: #182033; font-family: 'Noto Sans KR', Arial, sans-serif; }}
                .upload-preview-gallery {{
                    background: #f7f9fd;
                    border: 1px solid #dce3ef;
                    border-radius: 8px;
                    padding: 16px;
                }}
                .upload-preview-guide {{
                    color: #647087;
                    font-size: 12px;
                    margin: 0 0 12px;
                }}
                .upload-preview-stage {{
                    background: #eef2f8;
                    border: 1px solid #c8d3e5;
                    border-radius: 6px;
                    height: clamp(240px, 68vw, 330px);
                    overflow: hidden;
                }}
                .upload-preview-large {{
                    display: none;
                    height: 100%;
                    margin: 0;
                    position: relative;
                    width: 100%;
                }}
                .upload-preview-large img {{
                    height: 100%;
                    object-fit: contain;
                    width: 100%;
                }}
                .upload-preview-large figcaption {{
                    background: rgba(24, 32, 51, 0.82);
                    bottom: 10px;
                    color: #ffffff;
                    font-size: 12px;
                    left: 10px;
                    max-width: calc(100% - 20px);
                    overflow: hidden;
                    padding: 6px 9px;
                    position: absolute;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .upload-preview-thumbnails {{
                    display: grid;
                    gap: 8px;
                    grid-template-columns: repeat(4, minmax(0, 1fr));
                    margin-top: 12px;
                }}
                .upload-preview-thumb {{
                    background: #ffffff;
                    border: 2px solid transparent;
                    border-radius: 6px;
                    cursor: pointer;
                    display: block;
                    min-width: 0;
                    padding: 4px;
                    position: relative;
                    transition: border-color 150ms ease, box-shadow 150ms ease, background-color 150ms ease;
                }}
                .upload-preview-thumb:hover {{
                    background: #eef2ff;
                    border-color: #9fb4f4;
                }}
                .upload-preview-radio {{
                    cursor: pointer;
                    height: 100%;
                    inset: 0;
                    margin: 0;
                    opacity: 0;
                    position: absolute;
                    width: 100%;
                    z-index: 2;
                }}
                .upload-preview-thumb img {{
                    aspect-ratio: 1 / 1;
                    background: #eef2f8;
                    border-radius: 4px;
                    display: block;
                    object-fit: cover;
                    width: 100%;
                }}
                .upload-preview-thumb span {{
                    color: #647087;
                    display: block;
                    font-size: 11px;
                    line-height: 1.35;
                    margin-top: 5px;
                    overflow: hidden;
                    text-align: center;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .upload-preview-gallery:has(#upload-preview-0:checked) .upload-preview-large:nth-child(1),
                .upload-preview-gallery:has(#upload-preview-1:checked) .upload-preview-large:nth-child(2),
                .upload-preview-gallery:has(#upload-preview-2:checked) .upload-preview-large:nth-child(3),
                .upload-preview-gallery:has(#upload-preview-3:checked) .upload-preview-large:nth-child(4) {{
                    display: block;
                }}
                .upload-preview-thumb:has(.upload-preview-radio:checked) {{
                    background: #eef2ff;
                    border-color: #3157e7;
                    box-shadow: 0 0 0 2px rgba(49, 87, 231, 0.12);
                }}
                @media (max-width: 380px) {{
                    .upload-preview-gallery {{ padding: 12px; }}
                    .upload-preview-thumb span {{ font-size: 10px; }}
                }}
            </style>
        </head>
        <body>
            <div class="upload-preview-gallery">
                <p class="upload-preview-guide">썸네일을 누르면 선택한 사진을 크게 볼 수 있습니다.</p>
                <div class="upload-preview-stage">{"".join(large_previews)}</div>
                <div class="upload-preview-thumbnails">{"".join(thumbnail_controls)}</div>
            </div>
        </body>
        </html>
    """


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
        return "왼쪽 사이드바에 OpenAI API 키를 입력해 주세요."

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

    # 포스터와 광고 문구를 좌우로 배치합니다.
    image_column, detail_column = st.columns([2.7, 1], gap="medium")

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
st.markdown(
    f"""
    <div class="app-hero">
        <div class="hero-copy">
            <h1 class="app-title">AI 제품광고 포스터 생성기</h1>
            <p class="app-subtitle">
                제품 사진으로 광고 포스터를 만드세요.
            </p>
        </div>
        <div class="studio-badge" aria-hidden="true">
            <b>✦</b><span>크리에이티브 스튜디오</span><em>베타</em>
        </div>
    </div>
    """,
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
        "OpenAI API 키",
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

# 제품 사진과 제품 정보 영역을 위쪽 작업 패널로 배치합니다.
image_panel, product_panel = st.columns([1, 1.04], gap="medium")

with image_panel:
    st.markdown('<div class="panel-marker panel-upload"></div>', unsafe_allow_html=True)

    # 제품 사진 업로드 영역을 표시합니다.
    st.markdown(
        '<div class="section-heading"><span class="number">01</span>'
        '<span class="label">제품 사진 업로드</span></div>',
        unsafe_allow_html=True,
    )

    # 제품의 앞면, 옆면과 구성품 사진을 최대 네 장까지 받습니다.
    uploaded_files = st.file_uploader(
        "제품 사진을 올려주세요.",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        help="선명한 제품 사진을 최대 4장까지 올릴 수 있습니다.",
    )

    # 업로드한 파일이 있으면 생성 전에도 즉시 미리보기를 보여줍니다.
    if uploaded_files:
        # 생성에 전달하는 원본 목록은 그대로 두고 브라우저용 선택 미리보기만 표시합니다.
        components.html(
            build_upload_preview_gallery(uploaded_files),
            height=570,
            scrolling=False,
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

with product_panel:
    st.markdown('<div class="panel-marker panel-product"></div>', unsafe_allow_html=True)

    # 제품 정보 영역을 표시합니다.
    st.markdown(
        '<div class="section-heading"><span class="number">02</span>'
        '<span class="label">제품 정보</span></div>',
        unsafe_allow_html=True,
    )

    # 제품명, 브랜드와 가격 입력창을 레이블과 입력창 행으로 배치합니다.
    label_column, field_column = st.columns([0.24, 0.76], gap="small")
    with label_column:
        st.markdown(
            """
            <div class="product-label-stack">
                <div class="field-label required">제품명</div>
                <div class="field-label">브랜드명</div>
                <div class="field-label">가격</div>
                <div class="field-label">수량·구성</div>
                <div class="field-label">제품 카테고리</div>
                <div class="field-label">주요 고객</div>
                <div class="field-label feature-label required">제품 특징</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with field_column:
        product_name = st.text_input(
            "제품명 *",
            placeholder="예: 캐릭터 텀블러",
            label_visibility="collapsed",
        )
        brand_name = st.text_input(
            "브랜드명",
            placeholder="브랜드가 없으면 비워두세요.",
            label_visibility="collapsed",
        )
        price = st.text_input(
            "가격",
            placeholder="예: 17,900원",
            label_visibility="collapsed",
        )
        quantity = st.text_input(
            "수량·구성",
            placeholder="예: 1세트 또는 1박스 20개",
            label_visibility="collapsed",
        )
        category = st.selectbox(
            "제품 카테고리",
            CATEGORIES,
            label_visibility="collapsed",
        )
        target_customer = st.selectbox(
            "주요 고객",
            TARGET_CUSTOMERS,
            label_visibility="collapsed",
        )

        # 실제로 확인한 제품 특징을 입력합니다.
        features = st.text_area(
            "제품 특징 *",
            placeholder=(
                "실제로 확인된 내용만 입력하세요.\n"
                "예: 빨대와 뚜껑 포함, 여러 캐릭터 디자인, 휴대하기 좋은 크기"
            ),
            height=92,
            label_visibility="collapsed",
        )

st.markdown('<hr class="content-rule" />', unsafe_allow_html=True)

# 아트 디렉션과 결과를 아래쪽 핵심 작업 패널로 배치합니다.
art_panel, result_panel = st.columns([0.35, 0.65], gap="medium")

with art_panel:
    st.markdown('<div class="panel-marker panel-art"></div>', unsafe_allow_html=True)

    # 포스터 설정 영역을 표시합니다.
    st.markdown(
        '<div class="section-heading lower"><span class="number">03</span>'
        '<span class="label">제품과 포스터 설정</span></div>',
        unsafe_allow_html=True,
    )

    art_label_column, art_field_column = st.columns([0.34, 0.66], gap="small")

    with art_label_column:
        st.markdown(
            """
            <div class="art-label-stack">
                <div class="field-label">사용 목적</div>
                <div class="field-label">포스터 스타일</div>
                <div class="field-label">전체 색감</div>
                <div class="field-label">배경 분위기</div>
                <div class="field-label">포스터 글자 양</div>
                <div class="field-label">최종 출력 규격</div>
                <div class="field-label">이미지 생성 품질</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with art_field_column:
        usage = st.selectbox(
            "사용 목적",
            USAGE_OPTIONS,
            label_visibility="collapsed",
        )
        style = st.selectbox(
            "포스터 스타일",
            POSTER_STYLES,
            label_visibility="collapsed",
        )
        color_tone = st.selectbox(
            "전체 색감",
            COLOR_TONES,
            label_visibility="collapsed",
        )
        background_type = st.selectbox(
            "배경 분위기",
            BACKGROUND_TYPES,
            label_visibility="collapsed",
        )
        text_amount = st.selectbox(
            "포스터 글자 양",
            TEXT_AMOUNTS,
            index=1,
            label_visibility="collapsed",
        )
        output_type = st.selectbox(
            "최종 출력 규격",
            OUTPUT_TYPES,
            label_visibility="collapsed",
        )
        quality_label = st.selectbox(
            "이미지 생성 품질",
            list(QUALITY_MAP.keys()),
            index=0,
            label_visibility="collapsed",
        )

    st.markdown('<div class="art-extra-label">추가 요청</div>', unsafe_allow_html=True)
    extra_request = st.text_area(
        "추가 요청",
        placeholder=(
            "예: 제품은 중앙에 크게, 배경은 연한 베이지, "
            "제목은 위쪽, 가격은 오른쪽 아래에 배치"
        ),
        height=80,
        label_visibility="collapsed",
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
            st.error("OpenAI API 키가 올바르지 않습니다. 키를 다시 확인해 주세요.")

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

# 결과 영역은 생성 전에도 같은 자리를 유지해 편집 그리드가 흐트러지지 않게 합니다.
with result_panel:
    st.markdown('<div class="panel-marker panel-result"></div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="section-heading lower"><span class="number">04</span>'
        '<span class="label">생성 결과</span></div>',
        unsafe_allow_html=True,
    )

    if "last_result" in st.session_state:
        remake_clicked, new_copy_on_remake = show_result(
            st.session_state["last_result"]
        )
    else:
        st.markdown(
            """
            <div class="result-empty">
                <div class="poster-placeholder" aria-hidden="true">
                    <div class="poster-placeholder-visual">미리보기</div>
                </div>
                <p class="result-empty-title">생성된 포스터가 여기에 표시됩니다</p>
                <p class="result-empty-note">제품 정보와 포스터 설정을 입력한 뒤 생성해 주세요.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# 이전에 생성한 결과가 세션에 있으면 다시 만들기 동작을 처리합니다.
if "last_result" in st.session_state:

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
                st.error("OpenAI API 키가 올바르지 않습니다.")

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
