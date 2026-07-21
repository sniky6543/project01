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
            grid-template-rows: repeat(7, var(--control-height)) 108px;
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

        /* BaseWeb 셀렉트 메뉴는 본문 바깥 포털에 열리므로 옵션 목록도 별도로 흰색 처리합니다. */
        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        ul[role="listbox"],
        div[role="listbox"] {
            background: #ffffff !important;
            border-color: var(--line-strong) !important;
        }

        li[role="option"],
        div[role="option"] {
            background: #ffffff !important;
            color: var(--ink) !important;
        }

        li[role="option"]:hover,
        div[role="option"]:hover,
        li[role="option"][aria-selected="true"],
        div[role="option"][aria-selected="true"] {
            background: var(--accent-soft) !important;
            color: var(--accent) !important;
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


        .result-loading {
            align-items: center;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 480px;
            padding: var(--space-4) 0 var(--space-3);
        }

        .loading-poster {
            align-items: center;
            aspect-ratio: 4 / 5;
            background: linear-gradient(145deg, #f8faff 0%, #edf2ff 100%);
            border: 1px solid #cbd8f4;
            border-radius: var(--radius-sm);
            box-shadow: 0 10px 28px rgba(49, 87, 231, 0.10);
            display: flex;
            justify-content: center;
            max-width: 250px;
            overflow: hidden;
            position: relative;
            width: min(52%, 250px);
        }

        .loading-poster::before {
            background: linear-gradient(
                100deg,
                transparent 20%,
                rgba(255, 255, 255, 0.82) 50%,
                transparent 80%
            );
            content: "";
            inset: 0;
            position: absolute;
            transform: translateX(-120%);
            animation: poster-shimmer 1.5s infinite;
        }

        .loading-image-symbol {
            align-items: center;
            background: #ffffff;
            border: 1px solid #d5defb;
            border-radius: 50%;
            color: var(--accent);
            display: flex;
            font-size: 1.4rem;
            font-weight: 700;
            height: 62px;
            justify-content: center;
            width: 62px;
        }

        .loading-status {
            align-items: center;
            color: var(--muted);
            display: flex;
            font-size: var(--font-xs);
            font-weight: 600;
            gap: 8px;
            margin-top: var(--space-4);
        }

        .loading-spinner {
            animation: loading-spin 0.9s linear infinite;
            border: 2px solid #d5defb;
            border-radius: 50%;
            border-top-color: var(--accent);
            height: 16px;
            width: 16px;
        }

        @keyframes poster-shimmer {
            to { transform: translateX(120%); }
        }

        @keyframes loading-spin {
            to { transform: rotate(360deg); }
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

        /* =========================================================
           Streamlit 다크모드에서도 셀렉트박스를 밝은 테마로 고정
           ========================================================= */
        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"] {
            color-scheme: light !important;
        }

        /* 셀렉트박스 본체 */
        [data-testid="stSelectbox"],
        [data-testid="stSelectboxRootElement"],
        [data-testid="stSelectbox"] [role="group"],
        div[data-baseweb="select"],
        div[data-baseweb="select"] > div,
        div[data-baseweb="select"] [role="combobox"] {
            background-color: #ffffff !important;
            color: #20242a !important;
            -webkit-text-fill-color: #20242a !important;
        }

        /* 현재 선택된 값 */
        [data-testid="stSelectbox"] [role="combobox"],
        [data-testid="stSelectbox"] [role="combobox"] *,
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] [role="combobox"] span,
        div[data-baseweb="select"] input {
            color: #20242a !important;
            -webkit-text-fill-color: #20242a !important;
            opacity: 1 !important;
        }

        /* 우측 드롭다운 화살표 */
        [data-testid="stSelectbox"] svg,
        [data-testid="stSelectboxRootElement"] svg,
        div[data-baseweb="select"] svg,
        div[data-baseweb="select"] svg path {
            color: #667085 !important;
            fill: #667085 !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        /* 클릭했을 때 열리는 옵션 목록 */
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] > div,
        div[data-baseweb="menu"],
        ul[role="listbox"],
        div[role="listbox"] {
            background-color: #ffffff !important;
            color: #20242a !important;
            color-scheme: light !important;
        }

        /* 개별 옵션 및 내부 글자 */
        li[role="option"],
        div[role="option"],
        li[role="option"] *,
        div[role="option"] * {
            background-color: #ffffff !important;
            color: #20242a !important;
            -webkit-text-fill-color: #20242a !important;
            opacity: 1 !important;
        }

        /* 마우스 오버 및 선택된 옵션 */
        li[role="option"]:hover,
        div[role="option"]:hover,
        li[role="option"][aria-selected="true"],
        div[role="option"][aria-selected="true"] {
            background-color: #eef2ff !important;
            color: #3157e7 !important;
        }

        li[role="option"]:hover *,
        div[role="option"]:hover *,
        li[role="option"][aria-selected="true"] *,
        div[role="option"][aria-selected="true"] * {
            background-color: transparent !important;
            color: #3157e7 !important;
            -webkit-text-fill-color: #3157e7 !important;
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


# 업로드 가능한 이미지 형식과 최대 개수를 한 곳에서 관리합니다.
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_IMAGE_MIME_TYPES = {
    "",
    #"application/octet-stream",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
}
MAX_UPLOAD_FILES = 4

# 금지할 위험 확장자 패턴
FORBIDDEN_EXTENSIONS = {".exe", ".php", ".js", ".py", ".sh", ".html", ".bat"}


def detect_uploaded_image_format(uploaded_file) -> str:
    """파일 앞부분의 실제 바이트를 확인해 PNG, JPEG 또는 WEBP인지 판별합니다."""

    try:
        # 전체 파일을 복사하지 않고 시그니처 확인에 필요한 앞부분만 읽습니다.
        header = bytes(uploaded_file.getbuffer()[:12])
    except Exception:
        # getbuffer를 지원하지 않는 경우에도 현재 읽기 위치를 복구합니다.
        current_position = uploaded_file.tell()
        uploaded_file.seek(0)
        header = uploaded_file.read(12)
        uploaded_file.seek(current_position)

    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"

    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"

    return ""


# ==============================================================================
# [수정 2] 파일명 기반 안전성 검사 함수 신설 및 validate_uploaded_images 연동
# ==============================================================================
def is_safe_filename(file_name: str) -> tuple[bool, str]:
    """파일명의 길이, 이중 확장자 및 보안 위험 패턴을 검사합니다."""
    if not file_name:
        return False, "이름 없는 파일"

    # 1. 파일명 길이 검사
    if len(file_name) > 100:
        return False, f"{file_name[:20]}... (파일명 100자 초과)"

    lower_name = file_name.lower()

    # 2. 위험 확장자 및 이중 확장자 패턴 검사 (예: image.py.png, script.exe 등)
    for forbidden in FORBIDDEN_EXTENSIONS:
        if lower_name.endswith(forbidden) or (forbidden + ".") in lower_name:
            return False, f"{file_name} (안전하지 않은 파일명 패턴)"

    return True, ""


def validate_uploaded_images(uploaded_files: list) -> tuple[str, list]:
    """확장자, MIME 타입, 파일명 패턴, 실제 파일 시그니처와 업로드 개수를 검사합니다."""

    if not uploaded_files:
        return "", []

    error_messages = []
    valid_preview_files = []
    invalid_file_names = []

    for uploaded_file in uploaded_files:
        file_name = str(getattr(uploaded_file, "name", "") or "")
        
        # [신규] 1단계: 파일명 제어 검사 (길이, 위험 패턴)
        is_safe, unsafe_reason = is_safe_filename(file_name)
        if not is_safe:
            invalid_file_names.append(unsafe_reason)
            continue

        extension = (
            file_name.rsplit(".", 1)[-1].lower()
            if "." in file_name
            else ""
        )
        mime_type = str(getattr(uploaded_file, "type", "") or "").lower()
        detected_format = detect_uploaded_image_format(uploaded_file)

        expected_formats = {
            "png": {"png"},
            "jpg": {"jpeg"},
            "jpeg": {"jpeg"},
            "webp": {"webp"},
        }

        extension_is_valid = extension in ALLOWED_IMAGE_EXTENSIONS
        mime_is_valid = mime_type in ALLOWED_IMAGE_MIME_TYPES
        signature_is_valid = (
            extension_is_valid
            and detected_format in expected_formats.get(extension, set())
        )

        # 모든 검증 조건을 통과해야 유효한 파일로 처리합니다.
        if extension_is_valid and mime_is_valid and signature_is_valid:
            valid_preview_files.append(uploaded_file)
        else:
            invalid_file_names.append(file_name or "이름 없는 파일")

    if invalid_file_names:
        invalid_names = ", ".join(invalid_file_names)
        error_messages.append(
            "허용되지 않거나 형식에 문제가 있는 파일입니다: "
            f"{invalid_names}. (PNG, JPG, JPEG, WEBP 파일만 가능)"
        )

    if len(uploaded_files) > MAX_UPLOAD_FILES:
        error_messages.append(
            f"최대 업로드 개수는 {MAX_UPLOAD_FILES}개입니다. "
            f"현재 {len(uploaded_files)}개가 선택되었습니다. "
            "초과한 파일을 제거해 주세요."
        )

    return "\n\n".join(error_messages), valid_preview_files[:MAX_UPLOAD_FILES]


def read_default_api_key() -> str:
    """환경변수나 Streamlit Secrets에서 기본 API 키를 읽습니다."""

    # 먼저 프로젝트의 .env 또는 운영체제 환경변수에서 키를 찾습니다.
    environment_ke... (29KB 남음)