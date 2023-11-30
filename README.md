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
  <a href="https://python-poetry.org/">
    <img src="https://img.shields.io/badge/packaging-poetry-299bd7?style=flat-square&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAASCAYAAABrXO8xAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAJJSURBVHgBfZLPa1NBEMe/s7tNXoxW1KJQKaUHkXhQvHgW6UHQQ09CBS/6V3hKc/AP8CqCrUcpmop3Cx48eDB4yEECjVQrlZb80CRN8t6OM/teagVxYZi38+Yz853dJbzoMV3MM8cJUcLMSUKIE8AzQ2PieZzFxEJOHMOgMQQ+dUgSAckNXhapU/NMhDSWLs1B24A8sO1xrN4NECkcAC9ASkiIJc6k5TRiUDPhnyMMdhKc+Zx19l6SgyeW76BEONY9exVQMzKExGKwwPsCzza7KGSSWRWEQhyEaDXp6ZHEr416ygbiKYOd7TEWvvcQIeusHYMJGhTwF9y7sGnSwaWyFAiyoxzqW0PM/RjghPxF2pWReAowTEXnDh0xgcLs8l2YQmOrj3N7ByiqEoH0cARs4u78WgAVkoEDIDoOi3AkcLOHU60RIg5wC4ZuTC7FaHKQm8Hq1fQuSOBvX/sodmNJSB5geaF5CPIkUeecdMxieoRO5jz9bheL6/tXjrwCyX/UYBUcjCaWHljx1xiX6z9xEjkYAzbGVnB8pvLmyXm9ep+W8CmsSHQQY77Zx1zboxAV0w7ybMhQmfqdmmw3nEp1I0Z+FGO6M8LZdoyZnuzzBdjISicKRnpxzI9fPb+0oYXsNdyi+d3h9bm9MWYHFtPeIZfLwzmFDKy1ai3p+PDls1Llz4yyFpferxjnyjJDSEy9CaCx5m2cJPerq6Xm34eTrZt3PqxYO1XOwDYZrFlH1fWnpU38Y9HRze3lj0vOujZcXKuuXm3jP+s3KbZVra7y2EAAAAAASUVORK5CYII=" alt="Poetry">
  </a>
  <a href="https://github.com/ambv/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square" alt="black">
  </a>
  <a href="https://github.com/pre-commit/pre-commit">
    <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=flat-square" alt="pre-commit">
  </a>
</p>
<p align="center">
  <a href="https://pypi.org/project/lab-student-survey/">
    <img src="https://img.shields.io/pypi/v/lab-student-survey.svg?logo=python&logoColor=fff&style=flat-square" alt="PyPI Version">
  </a>
  <img src="https://img.shields.io/pypi/pyversions/lab-student-survey.svg?style=flat-square&logo=python&amp;logoColor=fff" alt="Supported Python versions">
  <img src="https://img.shields.io/pypi/l/lab-student-survey.svg?style=flat-square" alt="License">
</p>

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

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- prettier-ignore-start -->
<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- markdownlint-disable -->
<!-- markdownlint-enable -->
<!-- ALL-CONTRIBUTORS-LIST:END -->
<!-- prettier-ignore-end -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
