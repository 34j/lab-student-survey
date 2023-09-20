from __future__ import annotations

import base64
from io import BytesIO, StringIO
from logging import getLogger
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.style
import matplotx
import numpy as np
import pandas as pd
import pingouin as pg
import seaborn as sns
from matplotlib.figure import Figure
from scipy.stats import pearsonr

LIKERT_SCALE = ["全く当てはまる", "当てはまる", "どちらともいえない", "あまり当てはまらない", "全く当てはまらない"]


LOG = getLogger(__name__)


def export_multiple_frames_to_html(
    dfs: list[pd.DataFrame | pd.Series | str | Figure], path: Path | str
) -> None:
    dfs = [df.to_frame() if isinstance(df, pd.Series) else df for df in dfs]
    with open(path, "w", encoding="utf-8") as f:
        f.write("<html><meta charset='UTF-8'><body>")
        for df in dfs:
            if isinstance(df, str):
                f.write(f"<h2>{df}</h2>")
            elif isinstance(df, Figure):
                with BytesIO() as buf:
                    try:
                        df.tight_layout()
                    except Exception as e:
                        LOG.warning(e)
                    df.savefig(buf, format="png")
                    f.write(
                        "<img src='data:image/png;base64,"
                        f"{base64.b64encode(buf.getvalue()).decode('utf-8')}'/>"
                    )
            else:
                # replace \n with <br> tag
                f.write(df.to_html().replace("\\n", "<br>"))
        f.write("</body></html>")


def analyze(
    csv_content: str, *, out_path: Path | str = "output.html", add_numeral: bool = True
) -> None:
    matplotlib.style.use(matplotx.styles.dracula)
    matplotlib.rcParams["font.family"] = "Yu Gothic"

    with StringIO(csv_content) as f:
        df = pd.read_csv(f, index_col=[2], header=0)
    df = df.drop(columns=["タイムスタンプ"])
    df = df.sort_index(axis=0)

    # get metadata
    metadata_path = Path("metadata.csv")
    if not metadata_path.exists():
        df_meta = df.columns.to_frame()
        # group=None means the question is not in any group
        df_meta["group"] = None
        # higher_is_better=False means the lower the score, the better
        df_meta["higher_is_better"] = False
        df_meta.to_csv(metadata_path, index=False)
        raise RuntimeError(
            "metadata.csv does not exist, please fill it in and run again. "
            "You can use `Edit csv` VSCode extension etc. to edit it. "
            "Using Microsoft Excel may cause encoding problems. "
        )
    df_meta = pd.read_csv(metadata_path, index_col=0, header=0)
    df_meta["group"] = df_meta["group"].astype(object)

    metadata_group_name_path = Path("metadata_group_name.csv")
    if metadata_group_name_path.exists():
        group_names = pd.read_csv(metadata_group_name_path, index_col=0, header=None)
        for i, group_name in group_names.iterrows():
            df_meta.loc[df_meta["group"] == i, "group"] = group_name[1]

    # extract likert scale questions and numerical columns
    likert_cols = df_meta["group"].notna()
    df_likert = df.loc[:, likert_cols].copy()
    df_free = df.loc[:, ~likert_cols].copy()
    df_likert_meta = df_meta[likert_cols].copy()

    # convert likert scale to numerical values
    for i, likert_scale in enumerate(LIKERT_SCALE):
        df_likert = df_likert.replace(likert_scale, len(LIKERT_SCALE) - i)
    df_likert = df_likert.astype(int)
    df_likert.loc[:, ~df_likert_meta["higher_is_better"]] = len(LIKERT_SCALE) - (
        df_likert.loc[:, ~df_likert_meta["higher_is_better"]] - 1
    )

    # multiindex by group and question
    df_likert.columns = pd.MultiIndex.from_frame(
        pd.DataFrame({"group": df_likert_meta["group"], "question": df_likert.columns})
    )
    if add_numeral:
        df_numeral = df.select_dtypes(include="number")
        df_numeral_columns = df_numeral.columns
        df_numeral.columns = pd.MultiIndex.from_frame(
            pd.DataFrame({"group": df_numeral.columns, "question": df_numeral.columns})
        )
        df_likert = pd.concat([df_likert, df_numeral], axis=1, join="outer")

    # calculate mean and std for each group per row
    df_likert_grouped = df_likert.groupby(level="group", axis=1, sort=False)
    df_likert_mean = df_likert_grouped.mean()
    if add_numeral:
        df_likert_mean["mean"] = df_likert_mean.drop(columns=df_numeral_columns).mean(
            axis=1
        )
    df_likert_std = df_likert_grouped.std()
    if add_numeral:
        df_likert_std["mean"] = df_likert_std.drop(columns=df_numeral_columns).mean(
            axis=1
        )

    # calculate corr
    df_likert_mean_corr = df_likert_mean.corr()
    fig_corr, ax_corr = plt.subplots(figsize=(10, 10))
    sns.heatmap(df_likert_mean_corr, annot=True, ax=ax_corr)

    # calculate p-values
    df_likert_mean_pval = df_likert_mean.corr(
        method=lambda x, y: pearsonr(x, y)[1]
    ) - np.eye(len(df_likert_mean_corr))

    # calculate mean and std for each column
    df_likert_grouped_colwise = df_likert.T.groupby(level="group", axis=0, sort=False)
    df_liekrt_mean_colwise = (
        df_likert_grouped_colwise.mean().mean(axis=1).rename("mean")
    )
    df_likert_std_colwise = df_likert_grouped_colwise.std().mean(axis=1).rename("std")

    def _parse_cronbach_alpha(x: pd.Series) -> dict[str, object]:
        if x.shape[1] <= 1:
            return {
                "alpha": float("nan"),
                "alpha_0.95": float("nan"),
                "internal_consistency": "N/A",
            }
        a = pg.cronbach_alpha(x)
        internal_consistency = {
            0.9: "Excellent",
            0.8: "Good",
            0.7: "Acceptable",
            0.6: "Questionable",
            0.5: "Poor",
            float("-inf"): "Unacceptable",
        }
        # internal_consistency = {
        #     0.9: "<span style='color: #00ff00'>Excellent</span>",
        #     0.8: "<span style='color: #00dd00'>Good</span>",
        #     0.7: "<span style='color: #00bb00'>Acceptable</span>",
        #     0.6: "<span style='color: #009900'>Questionable</span>",
        #     0.5: "<span style='color: #007700'>Poor</span>",
        #     float("-inf"): "<span style='color: #005500'>Unacceptable</span>"
        # }
        return {
            "alpha": a[0],
            "alpha_0.95": a[1],
            "internal_consistency": internal_consistency[
                max(filter(lambda x: x <= a[0], internal_consistency.keys()))
            ],
        }

    df_likert_alpha = df_likert_grouped.apply(lambda x: _parse_cronbach_alpha(x)).apply(
        pd.Series
    )
    df_likert_colwise = pd.concat(
        [df_liekrt_mean_colwise, df_likert_std_colwise, df_likert_alpha], axis=1
    )
    df_likert_colwise.plot(kind="barh", subplots=True, figsize=(10, 15))
    fig_colwise = plt.gcf()

    # export to html
    dfs_to_write = [
        "<h1>分析結果</h1>" f"最終更新: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "自由記述",
        df_free,
        "回答ごとのグループに関する平均（質問によって、良い方向の回答が高い値になるように変換しております）",
        df_likert_mean.round(2),
        "グループに関する平均の相関",
        df_likert_mean_corr.round(2),
        fig_corr,
        "グループに関する平均の相関のp値",
        df_likert_mean_pval.round(2),
        "回答ごとのグループに関する分散",
        df_likert_std.round(2),
        "グループに関する統計値",
        df_likert_colwise.round(2),
        fig_colwise,
        "選択型",
        df_likert,
    ]
    export_multiple_frames_to_html(dfs_to_write, Path(out_path))
