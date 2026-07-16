"""프로젝트 전용 가상환경으로 Streamlit 앱을 실행합니다."""

# 운영체제별 실행 파일 경로를 구분하기 위해 불러옵니다.
import os

# Streamlit 실행 명령을 호출하기 위해 불러옵니다.
import subprocess

# 오류 발생 시 종료 코드를 반환하기 위해 불러옵니다.
import sys

# 프로젝트 경로를 다루기 위해 불러옵니다.
from pathlib import Path


# run.py가 들어 있는 프로젝트 폴더를 기준 경로로 사용합니다.
BASE_DIR = Path(__file__).resolve().parent

# setup.py가 만드는 프로젝트 전용 가상환경 폴더입니다.
VENV_DIR = BASE_DIR / ".poster_venv"

# 실행할 Streamlit 메인 파일입니다.
APP_FILE = BASE_DIR / "app.py"


def get_venv_python() -> Path:
    """현재 운영체제에 맞는 가상환경 Python 경로를 반환합니다."""

    # Windows에서는 Scripts 폴더의 python.exe를 사용합니다.
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"

    # macOS와 Linux에서는 bin 폴더의 python을 사용합니다.
    return VENV_DIR / "bin" / "python"


def main() -> None:
    """프로젝트 전용 Python으로 Streamlit 앱을 실행합니다."""

    # 가상환경 Python 경로를 가져옵니다.
    venv_python = get_venv_python()

    # 아직 설치하지 않았다면 setup.py 실행 방법을 안내합니다.
    if not venv_python.exists():
        print("프로젝트 전용 가상환경을 찾을 수 없습니다.")
        print("VS Code 터미널에서 먼저 다음 명령을 실행하세요:")
        print("py setup.py")
        sys.exit(1)

    # app.py 파일이 없으면 프로젝트가 정상적으로 풀리지 않은 상태입니다.
    if not APP_FILE.exists():
        print("app.py 파일을 찾을 수 없습니다.")
        print("ZIP 압축을 다시 풀고 프로젝트 폴더 전체를 열어 주세요.")
        sys.exit(1)

    # 실행 주소를 안내합니다.
    print("=" * 62)
    print("AI 제품광고 포스터 생성기를 실행합니다.")
    print("브라우저가 자동으로 열리지 않으면 아래 주소를 입력하세요.")
    print("http://localhost:8501")
    print("=" * 62)

    # 가상환경의 Python으로 Streamlit을 실행합니다.
    completed = subprocess.run(
        [
            str(venv_python),
            "-m",
            "streamlit",
            "run",
            str(APP_FILE),
        ],
        cwd=BASE_DIR,
        check=False,
    )

    # Streamlit 종료 코드를 그대로 반환합니다.
    sys.exit(completed.returncode)


# 이 파일을 직접 실행했을 때만 main 함수를 실행합니다.
if __name__ == "__main__":
    main()
