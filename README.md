<div align=center>

# FourKa-AI

### KEA 6th - FourKa AI 레포지토리
#### [노션 링크]()

## AI Members
<img width="160px" src="https://github.com/yoonjiseok.png"/> | <img width="160px" src="https://github.com/G9bonwook.png"/> | <img width="160px" src="https://github.com/dukesugar.png"/> |  <img width="160px" src="https://github.com/KwonHalim.png"/> |
|:-----:|:-----:|:-----:|:-----:|
|팀장 👨🏻‍💻|팀원 👨🏻‍💻|팀원 👨🏻‍💻|팀원 👨🏻‍💻|
|[윤지석](https://github.com/yoonjiseok)|[구본욱](https://github.com/G9bonwook)|[이재모](https://github.com/dukesugar)|[권하림](https://github.com/KwonHalim)|

</div>
<br/>

## 🛠️ Development Environment 🛠️
![vscode](https://img.shields.io/badge/VSCode-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)

## 🥞 Stacks 🥞
| Name         | Description                                 |
| ------------ |---------------------------------------------|
| <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"> | Python 기반의 고성능 비동기 웹 프레임워크로, 빠른 개발과 자동 문서화를 지원. |
| <img src="https://img.shields.io/badge/Notion-%23000000.svg?style=for-the-badge&logo=notion&logoColor=white"> | 작업 관리 및 문서화를 위한 통합 협업 도구.                   |


## 💻 Convention 💻
## 🌲 Branch Convention 🌲
## 🧑‍💻 Code Convention 🧑‍💻
## 💬 Issue Convention 💬
## 🫷 PR Convention 🫸
## 🙏 Commit Convention 🙏
## 📁 Foldering Convention 📁
=======
| Name         | Description                                                 |
| ------------ |-------------------------------------------------------------|
| <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"> | Python 기반의 고성능 비동기 웹 프레임워크로, 빠른 개발과 자동 문서화를 지원. |
| <img src="https://img.shields.io/badge/Notion-%23000000.svg?style=for-the-badge&logo=notion&logoColor=white"> | 작업 관리 및 문서화를 위한 통합 협업 도구.                    |

---

## 💻 Convention 💻

> 🧨 **주의: `application.yaml` 관련 파일 절대 올리지 말 것!**
> - 인텔리제이 환경변수 설정을 사용한다면 상관 없을 수 있습니다.
> - `.gitignore` 파일에 추가하여 관리하며, 이미 추적 중이라면 아래 명령어로 캐시를 삭제하세요.
>   ```bash
>   git rm -r --cached .
>   ```

## 🌲 Branch Convention 🌲

* **Strategy :** Git Flow 활용
    * `main` 브랜치 : 배포 브랜치
    * `develop` 브랜치 : 개발 브랜치 (Default)
    * 모든 작업 브랜치는 `develop` 브랜치에서 파생됩니다.
* **작업 규칙**
    * **PR 전 필수 사항:** 본인 브랜치에 `develop`을 Pull 받아 최신화하고, 빌드 에러 여부를 반드시 확인하세요.
    * **Merge 규칙:** 리뷰어 2명(PL @윤지석 포함)의 승인이 있어야 Merge가 가능합니다.
    * **금지 사항:** `develop` 직접 Push 금지, 강제 Push(`--force`) 금지.

**Branch Naming Format**
```text
{type}/#Issue Number
ex) feature/#1, bug/#2, refactor/#3

💬 Issue Convention 💬
이슈 단위는 세밀하게 분할 부탁드립니다. (예: 기능 구현, 로그인 구현 등)

이슈 생성 시 Assignees, Labels 설정, 브랜치 연동을 완료해주세요.

Issue Naming Format

Plaintext
[type] 작업내용
ex) [feat] 규칙 뷰 구현


## Issue : ✅ Feature
작업하고자 하는 기능을 입력해주세요.

## ✅ TODO
구현 내용을 입력해주세요.
1. [ ] task1
2. [ ] task2

## 📎 ETC
이외에 논의가 필요한 사항이나 참고해야 할 내용이 있다면 적어주세요.

## Issue : ♻️ Refactor
리팩토링이 필요한 내용을 작성해주세요.

## Before
변경 전의 상황과 변경 이유를 작성해주세요.

## After
변경 후의 예상하는 구조를 작성해주세요.

## ✅ TODO
변경 내용을 입력해주세요.
1. [ ] task1
2. [ ] task2

## 1. Issue : 🐞 Fix / Bug
발생한 문제에 대해 설명해주세요.

## 2. 원인 파악
1. [ ] factor

## 3. 해결 방안 
1. [ ] solution