# Rust Minidump MCP

[![CI](https://github.com/bahamoth/rust-minidump-mcp/workflows/CI/badge.svg)](https://github.com/bahamoth/rust-minidump-mcp/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io)
[![uv](https://img.shields.io/badge/uv-package%20manager-yellow)](https://github.com/astral-sh/uv)

AI 에이전트와 개발자가 애플리케이션 크래시를 이해할 수 있도록 돕는 MCP (Model Context Protocol) 서버입니다. 강력한 Rust 기반 크래시 분석 도구와 AI 기능을 연결하여, 알아보기 어려운 크래시 덤프를 명확하고 실행 가능한 인사이트로 변환합니다. 이를 통해 근본 원인을 빠르게 파악하고 중요한 문제를 해결할 수 있습니다.

## 🚀 주요 기능

- **Minidump 분석**: Windows 크래시 덤프 파일(`.dmp`)을 분석하여 상세한 스택 트레이스 제공
- **심볼 추출**: 바이너리 파일(PDB, DWARF 형식)에서 Breakpad 심볼 추출
- **다중 전송 방식**: stdio, HTTP, SSE 전송 방식 지원
- **AI 기반 분석**: AI 지원 크래시 디버깅을 위한 내장 프롬프트
- **크로스 플랫폼**: Windows, macOS, Linux에서 동작
- **포괄적인 오류 처리**: 실행 가능한 제안과 함께 상세한 오류 메시지 제공

## 📋 사전 요구사항

- Python 3.11 이상
- [uv](https://github.com/astral-sh/uv) 패키지 관리자
- [just](https://github.com/casey/just) 명령 실행기 (선택사항)

## 🛠️ 설치

### 1. 저장소 복제

```bash
git clone https://github.com/bahamoth/rust-minidump-mcp.git
cd rust-minidump-mcp
```

### 2. 가상 환경 생성 및 의존성 설치

```bash
uv venv
uv sync
```

### 3. Rust 도구 설치

프로젝트에는 사전 컴파일된 Rust 바이너리가 포함되어 있습니다. 다음 명령으로 설치하세요:

```bash
just install-tools
```

설치되는 도구:
- `minidump-stackwalk`: minidump 파일 분석용
- `dump_syms`: Breakpad 심볼 추출용

## 🚀 빠른 시작

### 방법 1: uvx 사용 (설치 불필요)

[uvx](https://github.com/astral-sh/uv)를 사용하여 설치 없이 도구를 직접 실행할 수 있습니다:

```bash
# 프로젝트 디렉토리에서
uvx --from . minidump-mcp server
uvx --from . minidump-mcp client

# PyPI 배포 후 (향후)
uvx minidump-mcp server
uvx minidump-mcp client
```

### 방법 2: 전통적인 설치

`uv sync`로 설치 후 표준 명령 사용:

### 서버 실행

#### STDIO 전송 (기본값)
```bash
minidump-mcp server
```

#### HTTP 전송
```bash
minidump-mcp server --transport streamable-http --port 8000
```

#### SSE 전송
```bash
minidump-mcp server --transport sse --port 9000
```

### 클라이언트 실행

```bash
# 기본 설정으로 연결
minidump-mcp client

# 사용자 지정 서버에 연결
minidump-mcp client --url http://localhost:8080/mcp

# 환경 변수 사용
export MINIDUMP_MCP_CLIENT_URL=http://localhost:8080/mcp
minidump-mcp client
```

## 📚 MCP 도구

### stackwalk_minidump

minidump 크래시 파일을 분석하여 사람이 읽을 수 있는 스택 트레이스를 생성합니다.

**매개변수:**
- `minidump_path` (str, 필수): minidump 파일 경로
- `symbols_path` (str, 선택): 심볼 파일 또는 디렉토리 경로
- `verbose` (bool, 선택): 상세 출력 포함 (기본값: False)

**예시:**
```python
result = await stackwalk_minidump(
    minidump_path="/path/to/crash.dmp",
    symbols_path="/path/to/symbols"
)
```

### extract_symbols

바이너리 파일(PDB, DWARF)에서 Breakpad 심볼 파일을 추출합니다.

**매개변수:**
- `binary_path` (str, 필수): 바이너리 파일 경로
- `output_dir` (str, 선택): 심볼 저장 디렉토리 (기본값: ./symbols/)

**예시:**
```python
result = await extract_symbols(
    binary_path="/path/to/app.exe",
    output_dir="./symbols"
)
# 생성됨: ./symbols/app.exe/1234ABCD/app.exe.sym
```

## 🔧 구성

### 환경 변수

`.env.example`을 `.env`로 복사하고 사용자 지정:

```bash
# 서버 구성
MINIDUMP_MCP_NAME=my-minidump-server
MINIDUMP_MCP_LOG_LEVEL=INFO
MINIDUMP_MCP_TRANSPORT=streamable-http
MINIDUMP_MCP_STREAMABLE_HTTP__HOST=127.0.0.1
MINIDUMP_MCP_STREAMABLE_HTTP__PORT=8000

# 클라이언트 구성
MINIDUMP_MCP_CLIENT_URL=http://localhost:8000/mcp
MINIDUMP_MCP_CLIENT_TRANSPORT=streamable-http
MINIDUMP_MCP_CLIENT_TIMEOUT=30.0
```

### 구성 우선순위

1. CLI 인수 (최우선)
2. 환경 변수
3. `.env` 파일
4. 기본값 (최하위)

## 🏗️ 아키텍처

### 프로젝트 구조

```
rust-minidump-mcp/
├── minidumpmcp/
│   ├── __init__.py
│   ├── server.py          # FastMCP 서버 진입점
│   ├── cli.py             # Typer 기반 CLI
│   ├── exceptions.py      # 사용자 정의 오류 처리
│   ├── config/
│   │   ├── settings.py    # 서버 구성
│   │   └── client_settings.py  # 클라이언트 구성
│   ├── tools/
│   │   ├── stackwalk.py   # Minidump 분석 도구
│   │   ├── dump_syms.py   # 심볼 추출 도구
│   │   └── bin/           # 플랫폼별 바이너리
│   └── prompts/           # AI 지원 디버깅 프롬프트
├── tests/                 # 테스트 스위트
├── justfile              # 작업 자동화
└── pyproject.toml        # 프로젝트 구성
```

### 전송 방식 지원

- **stdio**: CLI 통합을 위한 표준 입출력
- **streamable-http**: 웹 서비스를 위한 HTTP 기반 전송
- **sse**: 실시간 스트리밍을 위한 서버 전송 이벤트

## 🧪 개발

### 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_stackwalk.py

# 커버리지와 함께 실행
pytest --cov=minidumpmcp
```

### 코드 품질

```bash
# 코드 린트
ruff check

# 코드 포맷
ruff format

# 타입 체크
mypy .
```

### 사용 가능한 명령

모든 사용 가능한 명령 보기:
```bash
just --list
```

주요 명령:
- `just install-tools`: Rust 바이너리 설치
- `just test`: 테스트 실행
- `just lint`: 린터 실행
- `just format`: 코드 포맷

## 🐛 문제 해결

### 일반적인 문제

1. **바이너리를 찾을 수 없음 오류**
   ```
   해결: 'just install-tools'를 실행하여 필요한 바이너리 설치
   ```

2. **연결 거부 오류**
   ```
   해결: 서버가 올바른 포트에서 실행 중인지 확인
   확인: minidump-mcp server --transport streamable-http --port 8000
   ```

3. **잘못된 minidump 형식**
   ```
   해결: 파일이 유효한 Windows minidump (.dmp) 파일인지 확인
   ```

## 📝 라이선스

이 프로젝트는 MIT 라이선스로 배포됩니다 - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 기여하기

기여를 환영합니다! Pull Request를 제출해 주세요.

1. 저장소 포크
2. 기능 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시 (`git push origin feature/AmazingFeature`)
5. Pull Request 열기

## 📊 크래시 분석 이해하기

### Minidump 파일

Minidump 파일(`.dmp`)은 Windows 애플리케이션이 크래시할 때 생성되는 압축된 크래시 보고서입니다. 포함된 내용:
- 스레드 정보 및 스택 트레이스
- CPU 레지스터 상태
- 로드된 모듈 목록
- 예외 정보
- 시스템 정보

### 심볼 파일

심볼 파일은 메모리 주소를 사람이 읽을 수 있는 함수 이름과 소스 위치로 매핑합니다:
- **PDB 파일**: Windows 디버그 심볼
- **DWARF**: Linux/macOS 디버그 정보
- **Breakpad 형식**: 크로스 플랫폼 심볼 형식 (`.sym`)

### 분석 워크플로우

1. **크래시 발생**: 애플리케이션이 minidump 생성
2. **심볼 추출**: 크래시한 바이너리에서 `extract_symbols` 사용
3. **덤프 분석**: 심볼과 함께 `stackwalk_minidump` 사용
4. **결과 해석**: 함수 이름, 파일 경로, 줄 번호 확인

워크플로우 예시:
```bash
# 1. 애플리케이션에서 심볼 추출
minidump-mcp extract-symbols /path/to/app.exe --output ./symbols

# 2. 크래시 덤프 분석
minidump-mcp analyze /path/to/crash.dmp --symbols ./symbols
```

## 📁 심볼 디렉토리 구조

Breakpad 심볼은 특정 디렉토리 구조를 따릅니다:
```
symbols/
└── app.exe/
    └── 1234ABCD5678EF90/  # 모듈 ID
        └── app.exe.sym    # 심볼 파일
```

이 구조를 통해 분석기가 크래시 덤프의 각 모듈에 대한 올바른 심볼을 자동으로 찾을 수 있습니다.

## 🔗 관련 프로젝트

- [rust-minidump](https://github.com/rust-minidump/rust-minidump): 분석 도구를 구동하는 Rust 라이브러리
- [FastMCP](https://github.com/jlowin/fastmcp): 서버/클라이언트 구현에 사용된 MCP 프레임워크
- [Breakpad](https://chromium.googlesource.com/breakpad/breakpad/): 심볼 형식을 정의하는 크래시 보고 시스템