# ETF 데이터 업데이트 도구

이 프로젝트는 ETF 데이터를 자동으로 업데이트하고 분석하는 Streamlit 기반의 웹 애플리케이션입니다.

## 🌐 온라인 버전
Streamlit Cloud에서 바로 사용하실 수 있습니다:
[ETF 데이터 업데이트 도구](https://your-app-url.streamlit.app) (배포 후 URL 업데이트)

## 주요 기능

- Yahoo Finance에서 ETF 가격 데이터 자동 수집
- 일간/주간/월간/연간 수익률 계산
- 변동성과 MDD(Maximum Drawdown) 분석
- 그룹별 필터링 및 다양한 기준으로 정렬
- 데이터 엑셀 파일 다운로드

## 로컬 설치 방법

1. 저장소 클론
```bash
git clone [repository-url]
cd [repository-name]
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

## 사용 방법

### 온라인 (추천)
- 위의 Streamlit Cloud 링크를 클릭하여 바로 사용

### 로컬 실행
1. 애플리케이션 실행
```bash
streamlit run update_etf_data.py
```

2. 웹 브라우저에서 `http://localhost:8502` 접속

3. "데이터 새로고침" 버튼을 클릭하여 ETF 데이터 업데이트

4. 그룹 필터링과 정렬 기능을 사용하여 데이터 분석

## 데이터 파일

- `etf_data.xlsx`: 기본 ETF 데이터 파일
- `etf_data_with_returns.xlsx`: 수익률이 계산된 업데이트된 데이터 파일 (자동 생성)

## 주의사항

- Yahoo Finance API를 사용하므로 인터넷 연결이 필요합니다.
- 데이터 업데이트는 시장 거래 시간에 따라 다를 수 있습니다.
- 대량의 데이터를 처리하므로 충분한 메모리가 필요합니다.

## Streamlit Cloud 배포

이 앱은 Streamlit Cloud에 배포되어 있어 별도 설치 없이 사용 가능합니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 