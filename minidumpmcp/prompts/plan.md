# FastMCP Prompt 작성 계획

## 개요
**Rust Minidump MCP**는 크래시 덤프 분석을 위한 FastMCP 서버입니다. 현재 `stackwalk_minidump` 도구가 구현되어 있으며, 이를 활용한 AI 크래시 분석 전문가 시스템을 위한 prompt들을 작성합니다.

## 현재 구현된 Tool 분석

### `stackwalk_minidump` Tool
- **입력**: minidump 파일 경로, 심볼 경로(선택), 출력 형식
- **출력**: JSON 형태의 크래시 분석 데이터
- **주요 데이터**: crash_info, system_info, modules, threads, crashing_thread

### 분석 가능한 데이터 구조
```json
{
  "crash_info": {
    "type": "EXCEPTION_ACCESS_VIOLATION_WRITE",
    "address": "0x00000045",
    "crashing_thread": 0
  },
  "system_info": {
    "os": "Windows NT",
    "cpu_arch": "x86"
  },
  "crashing_thread": {
    "thread_id": 3060,
    "frames": [
      {
        "function": "`anonymous namespace'::CrashFunction", 
        "file": "c:\\test_app.cc",
        "line": 58,
        "missing_symbols": false
      }
    ]
  }
}
```

## FastMCP Prompts 설계

### 1. `crash_analyzer.md` - 메인 크래시 분석 전문가
**역할**: stackwalk_minidump 도구 결과를 해석하는 크래시 분석 전문가

**기능**:
- minidump 분석 결과 JSON을 받아 크래시 원인 분석
- 스택 트레이스에서 크래시 지점 식별
- 수정 권장사항 제시
- 우선순위 기반 분석 보고서 생성

**프롬프트 매개변수**:
- `analysis_data`: stackwalk_minidump 도구의 JSON 출력
- `analysis_depth`: 분석 깊이 (basic/detailed/comprehensive)
- `focus_area`: 집중 분석 영역 (memory/threading/logic)

### 2. `stack_interpreter.md` - 스택 트레이스 해석 전문가
**역할**: 복잡한 스택 트레이스를 분석하고 호출 체인을 해석

**기능**:
- 함수 호출 경로 추적
- 크래시 루트 코즈 역추적
- 예외 전파 경로 분석
- 재귀/무한루프 패턴 감지

**프롬프트 매개변수**:
- `stack_frames`: crashing_thread의 frames 배열
- `symbol_quality`: 심볼 정보 품질 (with_symbols/without_symbols)
- `frame_limit`: 분석할 프레임 수 제한 (기본 20)

### 3. `exception_decoder.md` - 예외 유형별 분석 전문가
**역할**: crash_info의 예외 유형을 분석하고 구체적인 해결책 제시

**기능**:
- EXCEPTION_ACCESS_VIOLATION 패턴 분석
- 메모리 주소 패턴 해석
- 일반적인 수정 패턴 제안
- 플랫폼별 예외 특성 설명

**프롬프트 매개변수**:
- `exception_type`: crash_info.type
- `exception_address`: crash_info.address  
- `system_context`: system_info (OS, CPU 아키텍처)

### 4. `symbol_advisor.md` - 심볼 정보 활용 가이드
**역할**: 심볼 정보 품질을 평가하고 개선 방안 제시

**기능**:
- 심볼 로딩 상태 평가 (loaded_symbols, missing_symbols 필드 분석)
- missing_symbols=true인 모듈에 대한 해결 가이드
- 심볼 품질이 분석 결과에 미치는 영향 설명

**프롬프트 매개변수**:
- `modules_info`: modules 배열의 심볼 상태
- `symbol_quality_summary`: 전체 심볼 품질 요약

## 구현 계획

### Phase 1: 핵심 분석 프롬프트 (주 1)
1. **crash_analyzer.md** 작성 및 테스트
   - stackwalk_minidump 출력을 받는 기본 분석 프롬프트
   - 실제 test.dmp 파일로 검증
   
2. **stack_interpreter.md** 작성
   - 스택 프레임 배열 처리 로직
   - 함수명/파일명/라인 정보 활용

### Phase 2: 전문 분석 프롬프트 (주 2)  
1. **exception_decoder.md** 작성
   - Windows 예외 유형별 분석 패턴
   - 메모리 주소 해석 로직

2. **symbol_advisor.md** 작성
   - 심볼 품질 평가 및 개선 가이드
   - dump_syms 도구 활용 권장사항

### Phase 3: 통합 및 최적화 (주 3)
1. 프롬프트 체이닝 테스트
2. 토큰 사용량 최적화 (4k 토큰 제한 준수)
3. 실제 크래시 시나리오 검증

## 기술적 구현 사항

### FastMCP Prompts 구조
```python
# server.py에서 프롬프트 등록 예시
from minidumpmcp.prompts import CrashAnalyzer, StackInterpreter

mcp = FastMCP(name="RustMinidumpMcp")
mcp.prompt(CrashAnalyzer())
mcp.prompt(StackInterpreter())
```

### 프롬프트 파일 형식
```markdown
# Crash Analyzer

You are an expert crash analysis specialist...

## Parameters
- analysis_data (required): JSON output from stackwalk_minidump
- analysis_depth (optional): basic|detailed|comprehensive

## Output Format
Return structured analysis in JSON format...
```

### 안전성 고려사항
- **PII 제거**: 파일 경로에서 사용자명 마스킹
- **토큰 제한**: 스택 프레임을 상위 50개로 제한
- **입력 검증**: JSON 스키마 검증
- **에러 처리**: 잘못된 minidump 데이터 처리

## 검증 기준

### 기능 검증
- [ ] test.dmp 파일로 모든 프롬프트 테스트
- [ ] 심볼 있음/없음 시나리오 모두 처리
- [ ] 다양한 예외 유형 분석 가능
- [ ] 4k 토큰 제한 내에서 동작

### 품질 검증  
- [ ] 일관된 JSON 출력 형식
- [ ] 실행 가능한 수정 권장사항
- [ ] 거짓 양성 최소화
- [ ] 사용자 친화적 설명

### 성능 검증
- [ ] 프롬프트 실행 시간 < 5초
- [ ] 메모리 사용량 적정 수준
- [ ] 동시 요청 처리 가능

## 사용 시나리오

### MCP 클라이언트 워크플로우
```python
# 1. 클라이언트가 도구 호출 (파일 경로 제공)
result = await mcp.call_tool("stackwalk_minidump", {
    "minidump_path": "/path/to/crash.dmp",
    "symbols_path": "/path/to/symbols"  # 클라이언트가 제공
})

# 2. 도구 출력을 프롬프트에 전달하여 분석
analysis = await mcp.call_prompt("crash_analyzer", {
    "analysis_data": result["data"]  # stackwalk_minidump의 JSON 출력
})
```

### 역할 분리
- **Tool**: 파일 시스템 접근, 바이너리 실행, 데이터 추출
- **Prompt**: 추출된 데이터 해석, 패턴 분석, 권장사항 생성

### 예상 출력
```json
{
  "crash_summary": "ACCESS_VIOLATION in CrashFunction at test_app.cc:58",
  "root_cause": "Null pointer dereference at address 0x00000045",
  "fix_recommendations": [
    "Add null pointer check before dereferencing",
    "Initialize pointer variables properly"
  ],
  "severity": "HIGH",
  "confidence": 0.95
}
```

## 구현 우선순위

**현재 구현된 `stackwalk_minidump` 도구의 출력을 분석하는 것이 유일한 목표입니다.**

모든 프롬프트는 다음 JSON 출력을 입력으로 받습니다:
- crash_info, system_info, modules, threads, crashing_thread 데이터
- 심볼 정보 포함/불포함 시나리오 모두 처리
- Windows minidump 분석에 특화
