# Price Compare Mobile (Flet Edition)

안드로이드 빌드 오류와 파이썬 버전 문제를 해결하기 위해, 최신 프레임워크인 **Flet**을 사용하여 새로 개발한 모바일 버전입니다.

## 특징
- **초고속 확인:** 빌드 대기 없이 즉시 실행 가능합니다.
- **Material 3 디자인:** 안드로이드 최신 디자인 가이드라인을 따릅니다.
- **통합 로직:** 윈도우 버전에서 검증된 스크래핑 및 DB 로직을 그대로 사용합니다.

## 실행 방법 (PC에서 미리보기)
1. **라이브러리 설치:**
   ```bash
   pip install flet requests beautifulsoup4
   ```
2. **실행:**
   ```bash
   cd c:\Users\hyh01\Antigravity_project_flet
   python main.py
   ```

## 스마트폰에서 즉시 실행하기 (추천!)
APK를 만들지 않고도 현재 내 폰에서 바로 앱을 띄워볼 수 있습니다:

1. 스마트폰의 **Play 스토어**에서 `Flet` 앱을 설치합니다.
2. PC에서 아래 명령어로 실행합니다 (웹 브라우저 모드):
   ```bash
   flet run --web main.py
   ```
3. 터미널에 나오는 URL(예: `http://192.168.0.xxx:8550`)을 스마트폰 브라우저에 입력하거나, 스마트폰의 `Flet` 앱에 입력하면 **즉시 내 폰에서 실행**됩니다!

## APK 파일 만들기 (GitHub 이용 추천)
가장 안정적으로 APK를 만드는 방법입니다:

1. **GitHub 저장소 만들기:** GitHub에 새로운 저장소(Repository)를 만듭니다.
2. **코드 업로드:** `mobile_flet` 폴더 안의 모든 파일( `.github` 폴더 포함)을 업로드합니다.
3. **자동 빌드:** 파일을 올리면 GitHub Actions가 자동으로 빌드를 시작합니다.
4. **다운로드:** GitHub 저장소의 **[Actions]** 탭에서 빌드가 완료된 후 `price-compare-apk` 파일을 찾아 다운로드하면 됩니다!

이 방식은 사용자님 PC에 복잡한 도구를 깔지 않아도 되어 가장 권장합니다.

