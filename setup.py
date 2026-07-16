"""프로젝트 전용 가상환경을 만들고 필요한 라이브러리를 설치합니다."""

# 운영체제별 실행 파일 경로를 구분하기 위해 불러옵니다.
import os

# 외부 명령어를 안전하게 실행하기 위해 불러옵니다.
import subprocess

# 현재 Python 실행 파일과 종료 코드를 사용하기 위해 불러옵니다.
import sys

# 파일과 폴더 경로를 편리하게 다루기 위해 불러옵니다.
from pathlib import Path

# 파일을 복사하기 위해 불러옵니다.
import shutil


# setup.py가 들어 있는 프로젝트 폴더를 기준 경로로 사용합니다.
BASE_DIR = Path(__file__).resolve().parent

# 강의에서 만든 기존 venv와 충돌하지 않도록 별도의 가상환경 이름을 사용합니다.
VENV_DIR = BASE_DIR / ".poster_venv"

# 필요한 라이브러리 목록 파일의 위치입니다.
REQUIREMENTS_FILE = BASE_DIR / "requirements.txt"

# API 환경설정 예시 파일의 위치입니다.
ENV_EXAMPLE_FILE = BASE_DIR / ".env.example"

# 실제 API 키를 저장할 파일의 위치입니다.
ENV_FILE = BASE_DIR / ".env"

def get_venv_python() -> Path:
    """현재 운영체제에 맞는 가상환경 Python 경로를 반환합니다."""

    # Windows에서는 Scripts 폴더의 python.exe를 사용합니다.
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"

    # macOS와 Linux에서는 bin 폴더의 python을 사용합니다.
    return VENV_DIR / "bin" / "python"


def run_command(command: list[str], message: str) -> None:
    """명령어를 실행하고 실패하면 설치를 중단합니다."""

    # 현재 진행 중인 작업을 화면에 표시합니다.
    print(f"\n{message}")

    # 프로젝트 폴더에서 명령어를 실행하고 오류가 있으면 예외를 발생시킵니다.
    subprocess.run(
        command,
        cwd=BASE_DIR,
        check=True,
    )


def main() -> None:
    """가상환경 생성부터 라이브러리 설치까지 순서대로 진행합니다."""

    # 설치 시작 안내를 표시합니다.
    print("=" * 62)
    print("AI 제품광고 포스터 생성기 v2 설치")
    print("=" * 62)

    # 현재 Python 버전을 표시합니다.
    print(f"현재 Python: {sys.version.split()[0]}")

    # 현재 Python이 3.10보다 낮으면 프로그램 실행을 중단합니다.
    if sys.version_info < (3, 10):
        print("\nPython 3.10 이상이 필요합니다.")
        print("Python 3.11 또는 3.12 설치를 권장합니다.")
        sys.exit(1)

    # 프로젝트 전용 가상환경이 없으면 새로 만듭니다.
    if not VENV_DIR.exists():
        run_command(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            "[1/4] 프로젝트 전용 가상환경을 만들고 있습니다...",
        )
    else:
        # 기존 강의 venv가 아니라 이 프로젝트 전용 가상환경을 재사용합니다.
        print("\n[1/4] 기존 .poster_venv 가상환경을 사용합니다.")

    # 가상환경 안의 Python 실행 파일 경로를 가져옵니다.
    venv_python = get_venv_python()

    # 폴더는 있지만 Python 실행 파일이 없다면 깨진 환경으로 안내합니다.
    if not venv_python.exists():
        print("\n.poster_venv 폴더가 정상적으로 만들어지지 않았습니다.")
        print("해당 폴더를 삭제한 뒤 다시 'py setup.py'를 실행해 주세요.")
        sys.exit(1)

    # 가상환경의 pip를 최신 버전으로 올립니다.
    run_command(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
        "[2/4] pip를 업데이트하고 있습니다...",
    )

    # requirements.txt의 라이브러리를 설치합니다.
    run_command(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "-r",
            str(REQUIREMENTS_FILE),
        ],
        "[3/4] 필요한 라이브러리를 설치하고 있습니다...",
    )

    # .env 파일이 없으면 예시 파일을 복사해 자동으로 만듭니다.
    if not ENV_FILE.exists() and ENV_EXAMPLE_FILE.exists():
        shutil.copy2(ENV_EXAMPLE_FILE, ENV_FILE)
        print("\n[4/4] .env 파일을 만들었습니다.")
        print("API 키는 프로그램 화면의 왼쪽 사이드바에 직접 입력해도 됩니다.")
    else:
        print("\n[4/4] 기존 .env 파일을 유지합니다.")

    # 설치 완료 안내를 표시합니다.
    print("\n" + "=" * 62)
    print("설치가 완료되었습니다.")
    print("다음 명령으로 실행하세요: py run.py")
    print("=" * 62)


# 이 파일을 직접 실행했을 때만 main 함수를 실행합니다.
if __name__ == "__main__":
    try:
        # 전체 설치 과정을 시작합니다.
        main()
    except subprocess.CalledProcessError as error:
        # 라이브러리 설치 명령이 실패했을 때 원인을 안내합니다.
        print("\n설치 중 오류가 발생했습니다.")
        print(f"실패한 명령 종료 코드: {error.returncode}")
        sys.exit(error.returncode)
    except KeyboardInterrupt:
        # 사용자가 Ctrl+C로 설치를 취소한 경우를 처리합니다.
        print("\n사용자가 설치를 취소했습니다.")
        sys.exit(1)
