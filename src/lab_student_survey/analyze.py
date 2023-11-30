from __future__ import annotations

import base64
from io import BytesIO, StringIO
from logging import getLogger
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import pandas as pd
import pdfkit
import pingouin as pg
import seaborn as sns
import sklearn
import sklearn.cluster
from japanize_matplotlib import japanize
from matplotlib.figure import Figure
from scipy.stats import pearsonr
from sklearn.discriminant_analysis import StandardScaler
from sklearn.manifold import MDS, TSNE
from xhtml2pdf import pisa

sklearn.set_config(transform_output="pandas")

LIKERT_SCALE_TEXTS = ["全く当てはまる", "当てはまる", "どちらともいえない", "あまり当てはまらない", "全く当てはまらない"]
TIMESTAMP_TEXT = "タイムスタンプ"
HTML_FONT_FAMILY = "HeiseiKakuGo-W5"
PDFKIT_FONT_FAMILY = "IPAexGothic"
MATPLOTLIB_FONT_FAMILY = "IPAexGothic"
PRIVACY_TEXT = "公開範囲"

LOG = getLogger(__name__)


def export_multiple_frames_to_html(
    dfs: list[pd.DataFrame | pd.Series | str | Figure],
    path: Path | str,
    pdf: bool = True,
) -> None:
    dfs = [df.to_frame() if isinstance(df, pd.Series) else df for df in dfs]
    with open(path, "w", encoding="utf-8") as f:
        # for xhtml2pdf support, set font-family to HeiseiKakuGo-W5
        f.write(
            """<html>
<meta charset='UTF-8'>
<style>
 @page {
        size: A1;
    }
    body { font-family: HeiseiKakuGo-W5; font-size: 5pt; }
    table { font-family: HeiseiKakuGo-W5; font-size: 5pt; }
    th { font-family: HeiseiKakuGo-W5; font-size: 5pt; }
    td { font-family: HeiseiKakuGo-W5; font-size: 5pt; }
</style>
<body>"""
        )
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

    if pdf:
        pdf_path = Path(path).with_suffix(".pdf")
        try:
            content = (
                Path(path)
                .read_text(encoding="utf-8")
                .replace(HTML_FONT_FAMILY, PDFKIT_FONT_FAMILY)
            )
            with StringIO(content) as f:
                pdfkit.from_file(f, pdf_path)
        except Exception as e:
            LOG.exception(e)
            LOG.warning("Failed to convert to pdf using pdfkit, trying xhtml2pdf")
            with Path(path).with_suffix(".pdf").open("wb") as f:
                pisa.CreatePDF(
                    Path(path).read_text(encoding="utf-8"),
                    f,
                    encoding="utf-8",
                    link_callback=lambda uri, _: uri.replace(" ", "%20"),
                )


def find_best_k(
    X: pd.DataFrame, max_k: int = 10
) -> tuple[int, list[float], sklearn.cluster.KMeans]:
    scores = []
    models = []
    for k in range(1, min(max_k, len(X)) + 1):
        model = sklearn.cluster.KMeans(n_clusters=k, n_init="auto")
        model.fit(X)
        scores.append(model.inertia_)
        models.append(model)
    return np.argmin(scores) + 1, scores, models[np.argmin(scores)]


def analyze(
    csv_content: str,
    *,
    out_path: Path | str = "output.html",
    add_numeral: bool = True,
    pdf: bool = True,
    privacy_scopes: list[str] | None = None,
) -> None:
    # matplotlib.style.use(matplotx.styles.dracula)
    if MATPLOTLIB_FONT_FAMILY == "IPAexGothic":
        japanize()
    else:
        matplotlib.rcParams["font.family"] = MATPLOTLIB_FONT_FAMILY

    with StringIO(csv_content) as f:
        df = pd.read_csv(f, index_col=[2], header=0)
    last_timestamp = df[TIMESTAMP_TEXT].max()
    PRIVACY_COL = df.columns[df.columns.str.contains(PRIVACY_TEXT)].tolist()[0]
    if privacy_scopes is not None:
        df = df[df[PRIVACY_COL].str.contains("|".join(privacy_scopes), regex=True)]
    df = df.drop(columns=[TIMESTAMP_TEXT])
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
    for i, likert_scale in enumerate(LIKERT_SCALE_TEXTS):
        df_likert = df_likert.replace(likert_scale, len(LIKERT_SCALE_TEXTS) - i)
    df_likert = df_likert.astype(int)
    df_likert.loc[:, ~df_likert_meta["higher_is_better"]] = len(LIKERT_SCALE_TEXTS) - (
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

    # clustering
    if add_numeral:
        df_likert_dropna = df_likert.drop(columns=df_numeral.columns)
    df_likert_dropna = df_likert_dropna.dropna(axis=1)
    df_likert_dropna = StandardScaler().fit_transform(df_likert_dropna)
    best_k, scores, cluster_model = find_best_k(df_likert_dropna, max_k=3)
    fig_c_elbow, ax = plt.subplots()
    ax.set_title("Elbow method for optimal k")
    ax.plot(range(1, len(scores) + 1), scores)

    fig_c_scatters = []
    for j, embedding in enumerate(
        [
            MDS(n_components=2, normalized_stress="auto"),
        ]
        + (
            [TSNE(n_components=2, perplexity=min(2, len(df_likert_dropna) - 1))]
            if len(df_likert_dropna) > 1
            else []
        )
    ):
        emb_res = pd.DataFrame(
            embedding.fit_transform(df_likert_dropna), index=df_likert_dropna.index
        )
        emb_res["cluster"] = cluster_model.predict(df_likert_dropna)
        fig_c_scatter, ax = plt.subplots(figsize=(7, 7))
        fig_c_scatters.append(fig_c_scatter)
        ax.set_title(f"Scatter plot of {embedding.__class__.__name__}")
        # annotate index
        sns.scatterplot(data=emb_res, x=0, y=1, hue="cluster", ax=ax)
        for i, row in emb_res.iterrows():
            ax.annotate(i, (row.iat[0], row.iat[1]))

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
    fig_mean, ax = plt.subplots(figsize=(12, 10), ncols=2)
    sns.barplot(
        y=df_likert_mean["mean"].index, x=df_likert_mean["mean"], orient="h", ax=ax[0]
    )
    df_likert_mean.sort_index(axis=0, inplace=False, ascending=False).drop(
        columns=list(df_numeral_columns) + ["mean"], inplace=False
    ).plot(kind="barh", ax=ax[1], stacked=True)
    # sns.barplot(df_likert_mean, orient="h", ax=ax[1])

    # calculate corr
    print(df_likert_mean)
    if len(df_likert_mean) < 2:
        df_likert_mean_corr = pd.DataFrame()
        fig_corr = plt.figure()
        df_likert_mean_pval = pd.DataFrame()
        df_likert_std = pd.DataFrame()
        df_likert_colwise = pd.DataFrame()
        fig_colwise = plt.figure()
    else:
        df_likert_mean_corr = df_likert_mean.corr()
        fig_corr, ax_corr = plt.subplots(figsize=(10, 10))
        sns.heatmap(df_likert_mean_corr, annot=True, ax=ax_corr)
        if add_numeral:
            fig_corr_dropped, ax_corr_dropped = plt.subplots(figsize=(10, 10))
            df_corr_dropped = df_likert_mean_corr.drop(
                index=df_numeral_columns, columns=df_numeral_columns
            )
            sns.heatmap(df_corr_dropped, annot=True, ax=ax_corr_dropped)

        # calculate p-values
        def try_peasonr(x: pd.Series, y: pd.Series) -> float:
            try:
                return pearsonr(x, y)[1]
            except Exception as e:
                LOG.warning(e)
                return float("nan")

        df_likert_mean_pval = df_likert_mean.corr(
            method=lambda x, y: try_peasonr(x, y)
        ) - np.eye(len(df_likert_mean_corr))

        # calculate mean and std for each column
        df_likert_grouped_colwise = df_likert.T.groupby(
            level="group", axis=0, sort=False
        )
        df_liekrt_mean_colwise = (
            df_likert_grouped_colwise.mean().mean(axis=1).rename("mean")
        )
        df_likert_std_colwise = (
            df_likert_grouped_colwise.std().mean(axis=1).rename("std")
        )

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
                    max(
                        list(filter(lambda x: x <= a[0], internal_consistency.keys()))
                        or [float("-inf")]
                    )
                ],
            }

        df_likert_alpha = df_likert_grouped.apply(
            lambda x: _parse_cronbach_alpha(x)
        ).apply(pd.Series)
        df_likert_colwise = pd.concat(
            [df_liekrt_mean_colwise, df_likert_std_colwise, df_likert_alpha], axis=1
        )
        if add_numeral:
            df_likert_colwise.drop(index=df_numeral_columns, inplace=False).plot(
                kind="barh", subplots=True, figsize=(10, 10), sharex=False
            )
        else:
            df_likert_colwise.plot(kind="barh", subplots=True, figsize=(10, 10))
        fig_colwise = plt.gcf()

    idx_unique = df.index.unique()
    # export to html
    dfs_to_write = [
        "<h1>分析結果</h1>"
        f"最終更新: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} "
        f"最終回答: {last_timestamp} 回答数: {len(df)} 指導教員数: {len(idx_unique)}/47 "
        f"機械A: {(~idx_unique.str.contains('機械B')).sum()}/32 "
        f"({(~idx_unique.str.contains('機械B')).sum()/32:.2%}) "
        f"機械B: {(idx_unique.str.contains('機械B')).sum()}/15 "
        f"({(idx_unique.str.contains('機械B')).sum()/15:.2%}) "
        f"{PRIVACY_TEXT}: "
        + (", ".join(privacy_scopes) if privacy_scopes is not None else "全て"),
        "自由記述",
        df_free,
        "回答ごとのグループに関する平均（質問によって、良い方向の回答が高い値になるように変換しております）",
        df_likert_mean.round(2),
        fig_mean,
        "クラスタリング（失敗）",
        fig_c_elbow,
        *fig_c_scatters,
        "グループに関する平均の相関",
        df_likert_mean_corr.round(2),
        fig_corr,
        fig_corr_dropped if add_numeral else pd.DataFrame(),
        "グループに関する平均の相関のp値",
        df_likert_mean_pval.round(2),
        "回答ごとのグループに関する分散",
        df_likert_std.round(2),
        "グループに関する統計値",
        df_likert_colwise.round(2),
        fig_colwise,
        "選択型（質問によって、良い方向の回答が高い値になるように変換しております）",
        df_likert,
        "生の値",
        df,
    ]
    export_multiple_frames_to_html(dfs_to_write, Path(out_path), pdf=pdf)
