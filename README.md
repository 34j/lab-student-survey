# Lab Student Survey

<p align="center">
  <a href="https://github.com/34j/lab-student-survey/actions/workflows/ci.yml?query=branch%3Amain">
    <img src="https://img.shields.io/github/actions/workflow/status/34j/lab-student-survey/ci.yml?branch=main&label=CI&logo=github&style=flat-square" alt="CI Status" >
  </a>
  <a href="https://lab-student-survey.readthedocs.io">
    <img src="https://img.shields.io/readthedocs/lab-student-survey.svg?logo=read-the-docs&logoColor=fff&style=flat-square" alt="Documentation Status">
  </a>
  <a href="https://codecov.io/gh/34j/lab-student-survey">
    <img src="https://img.shields.io/codecov/c/github/34j/lab-student-survey.svg?logo=codecov&logoColor=fff&style=flat-square" alt="Test coverage percentage">
  </a>
</p>
<p align="center">
  <a href="https://github.com/astral-sh/uv">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff">
  </a>
  <a href="https://github.com/j178/prek">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/j178/prek/master/docs/assets/badge-v0.json" alt="prek">
  </a>
</p>
<p align="center">
  <a href="https://pypi.org/project/lab-student-survey/">
    <img src="https://img.shields.io/pypi/v/lab-student-survey.svg?logo=python&logoColor=fff&style=flat-square" alt="PyPI Version">
  </a>
  <img src="https://img.shields.io/pypi/pyversions/lab-student-survey.svg?style=flat-square&logo=python&amp;logoColor=fff" alt="Supported Python versions">
  <img src="https://img.shields.io/pypi/l/lab-student-survey.svg?style=flat-square" alt="License">
</p>

---

**Documentation**: <a href="https://lab-student-survey.readthedocs.io" target="_blank">https://lab-student-survey.readthedocs.io</a>

**Source Code**: <a href="https://github.com/34j/lab-student-survey" target="_blank">https://github.com/34j/lab-student-survey</a>

---

Python package for lab student survey.
A single command fetches the spreadsheet generated from Google Forms and uploads the analysis results to Google Drive.

## Usage

- Create `student-lab-survey` (or any name) project in Google Cloud Platform.
- Enable `Google Drive API` in Google Cloud Platform.
- Create a `Service Account` in Google Cloud Platform.
- Download the `Service Account` credentials as JSON in Google Cloud Platform and save it as `service-secrets.json` in the working directory or set it as `GDRIVE_SERVICE_ACCOUNT` environment variable (via GitHub Secrets).
- Create `student-lab-survey` (or any name) folder in Google Drive.
- Add the `Service Account` email to the `student-lab-survey` folder with `Editor` permissions.
- Create a `Google Form` for the lab student survey. The second question should be the name of the supervisor.
- Create a `Google Sheet` in the `student-lab-survey` folder from the `Google Form`.
- Create `metadata.csv` and `metadata_group_name.csv` in the working directory or `student-lab-survey` folder in Google Drive to specify the question groups. The former will be automatically generated in the working directory if it does not exist. The latter is optional.

### Environment Variables

- Set the `Google Sheet` ID as `LAB_STUDENT_SURVEY_FILE_ID` environment variable (via GitHub Secrets).
- Set the `student-lab-survey` folder ID as `LAB_STUDENT_SURVEY_FOLDER_ID` environment variable (via GitHub Secrets). (Optional.) If not set, the parent folder ID of the `Google Sheet` will be used.
- (Set the `Service Account` credentials as `GDRIVE_SERVICE_ACCOUNT` environment variable (via GitHub Secrets).)

### Running commands

```shell
lss
```

### Github Actions

```yaml
name: Run lab-student-survey

on:
  schedule:
    # every day at 00:00 UTC
    - cron: "0 0 * * *"
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install wkhtmltopdf
        run: sudo apt-get install -y wkhtmltopdf
      - name: Install and run lab-student-survey
        run: pipx run lab-student-survey
        env:
          LAB_STUDENT_SURVEY_FILE_URL: ${{ secrets.LAB_STUDENT_SURVEY_FILE_URL }}
          LAB_STUDENT_SURVEY_FOLDER_URL: ${{ secrets.LAB_STUDENT_SURVEY_FOLDER_URL }}
          GDRIVE_SERVICE_SECRETS: ${{ secrets.GDRIVE_SERVICE_SECRETS }}
```

## Installation

Install this via pip or pipx (or your favourite package manager):

```shell
pipx install lab-student-survey
```

## Alternatives

As far as I could find, there is no repository on GitHub for this particular topic. Instead, you may want to check out the following alternative websites. However, as there are too few people in a lab, with the effect of diminishing anonymity, most of these websites do not seem to attract many reviews.

### 国内

- [理系研究室のクチコミサイト｜OpenLab](https://openlabmg.com/): **募集停止中**, 投稿するとAmazonギフト券（100円）がもらえる, ほとんど情報なし(100程度?)
- [LabBase 研究室サーチ](https://lab-search.app.labbase.jp/): **入力方法不明**, 上よりも情報なし
- [研究室ナビ](http://kenkyu-navi.com): リンク切れ [Forms](https://docs.google.com/forms/d/1s-c8tGOCGLv35KimBo9U7d3MKPyXpDl_QcHLozppAgM/viewform?edit_requested=true)

[研究室　口コミ \-満載 \-学べます \- Search / X](https://twitter.com/search?q=%E7%A0%94%E7%A9%B6%E5%AE%A4%E3%80%80%E5%8F%A3%E3%82%B3%E3%83%9F%20-%E6%BA%80%E8%BC%89%20-%E5%AD%A6%E3%81%B9%E3%81%BE%E3%81%99)

### 海外

- [PI Review](https://pi-review.com/): 231 reviews (2021/09/21)
- [GradPI](https://www.gradpi.com/): 329 reviews (2023/09/21), Must have a .edu or .ac.uk domain email address to even view the site.
- [RMGA](https://ratemygradadvisor.com/): 3 reviews? (2021/09/21)
- ratemypi.com, qcist.com: リンク切れ
- [한국에너지공과대학교 에너지공학부 구근호 \- 김박사넷](https://phdkim.net/professor/9877/info): かなり多い(1000以上?)

[pi rate website phd site:www\.reddit\.com \- Google Search](https://www.google.com/search?q=pi+rate+website+phd)
