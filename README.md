# AI 제품광고 포스터 생성기 v2

제품 사진과 제품 정보를 입력하면 광고 문구와 포스터 한 장을 생성하고  
A4·A5 또는 SNS 규격의 **PNG, JPG, PDF**로 저장하는 과제용 생성기입니다.

---

## 가장 간단한 실행 방법

### 1. ZIP 압축 풀기

압축을 푼 뒤 VS Code에서 아래 폴더 전체를 엽니다.

```text
AI_Product_Poster_Generator_v2
```

### 2. VS Code 터미널 열기

```text
상단 메뉴 → 터미널 → 새 터미널
```

### 3. 처음 한 번만 설치

```powershell
py setup.py
```

이 프로젝트는 강의에서 만든 기존 `venv`와 충돌하지 않도록  
프로젝트 안에 **`.poster_venv`**라는 별도 가상환경을 만듭니다.

### 4. 프로그램 실행

```powershell
py run.py
```

브라우저가 자동으로 열립니다.

```text
http://localhost:8501
```

### 5. 두 번째 실행부터

설치는 다시 하지 않고 아래 명령만 실행합니다.

```powershell
py run.py
```

---

## OpenAI API Key

프로그램이 실행되면 왼쪽 사이드바에 API 키를 직접 입력할 수 있습니다.

`.env` 파일에 저장하려면 다음처럼 입력합니다.

```text
OPENAI_API_KEY="발급받은_API_키"
OPENAI_TEXT_MODEL="gpt-5.6"
OPENAI_IMAGE_MODEL="gpt-image-2"
TEAM_NAME="팀 이름"
```

`.env` 파일은 팀원에게 보내거나 GitHub에 올리지 마세요.

---

## 주요 기능

- 제품 이미지 1~4장 업로드
- 업로드 즉시 이미지와 파일명 미리보기
- 제품명과 제품 특징 입력
- 브랜드, 가격과 수량 선택 입력
- 포스터 스타일 5종
- 색감과 배경 분위기 선택
- 글자 양 선택
- 결과 포스터 한 장 미리보기
- 스타일 변경 후 다시 만들기
- 광고 문구 유지 또는 새로 만들기 선택
- A4 세로·가로
- A5 세로·가로
- SNS 정사각형
- 300dpi 정보 저장
- PNG, JPG와 인쇄용 PDF 다운로드
- 원본, 결과 파일과 작업 정보 자동 저장
- 생성 진행률 표시

---

## 저장 위치

프로그램으로 생성한 파일은 다운로드 버튼 외에도 프로젝트 폴더에 저장됩니다.

```text
uploads/     업로드한 원본 사진
outputs/     생성된 PNG, JPG, PDF
metadata/    제품 정보와 생성 설정 JSON
```

---

## 인쇄 규격

```text
A4 세로: 2480 × 3508px
A4 가로: 3508 × 2480px
A5 세로: 1748 × 2480px
A5 가로: 2480 × 1748px
```

AI는 종이와 비슷한 비율로 이미지를 생성하고,  
Python이 마지막에 정확한 A4·A5 픽셀과 300dpi 정보로 변환합니다.

300dpi 정보를 넣더라도 낮은 해상도의 원본에 실제 세부 묘사가 새로 생기는 것은 아닙니다.  
따라서 최종 인쇄 전에는 제품 모양, 한글, 가격과 선명도를 반드시 확인하세요.

---

## 파일 구조

```text
AI_Product_Poster_Generator_v2/
├─ app.py
├─ config.py
├─ models.py
├─ prompt_service.py
├─ llm_service.py
├─ image_service.py
├─ storage.py
├─ setup.py
├─ run.py
├─ requirements.txt
├─ .env.example
├─ .gitignore
├─ render.yaml
├─ README.md
├─ uploads/
├─ outputs/
└─ metadata/
```

---

## Render는 선택 기능

발표용 로컬 실행에는 Render가 필요하지 않습니다.

시간이 남으면 프로젝트를 GitHub에 올린 뒤  
포함된 `render.yaml`을 이용해 Render 배포를 시도할 수 있습니다.

Render에서는 API 키를 코드에 넣지 말고  
환경변수 `OPENAI_API_KEY`로 등록해야 합니다.

---

## 오류가 날 때 팀원에게 공유할 내용

오류 화면 전체보다 다음 세 가지를 공유하면 원인을 빨리 찾을 수 있습니다.

```text
1. 오류가 난 파일명
2. 줄 번호
3. 마지막 오류 문장
```

예:

```text
File "app.py", line 123
NameError: name 'uploaded_files' is not defined
```
