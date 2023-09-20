from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd
import pingouin as pg

LIKERT_SCALE = ["全く当てはまる", "当てはまる", "どちらともいえない", "あまり当てはまらない", "全く当てはまらない"]


def export_multiple_frames_to_html(
    dfs: list[pd.DataFrame | pd.Series | str], path: Path | str
) -> None:
    dfs = [df.to_frame() if isinstance(df, pd.Series) else df for df in dfs]
    with open(path, "w") as f:
        f.write("<html><body>")
        for df in dfs:
            if isinstance(df, str):
                f.write(f"<h2>{df}</h2>")
            else:
                f.write(df.to_html())
        f.write("</body></html>")


def analyze(csv_content: str, *, out_path: Path | str = "output.html") -> None:
    with StringIO(csv_content) as f:
        df = pd.read_csv(f, index_col=[2, 0], header=0)

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

    metadata_group_name_path = Path("metadata_group_name.csv")
    if metadata_group_name_path.exists():
        group_names = pd.read_csv(metadata_group_name_path, index_col=0, header=None)
        for i, group_name in group_names.iterrows():
            df_meta.loc[df_meta["group"] == i, "group"] = group_name[1]

    # extract likert scale questions
    likert_cols = df_meta["group"].notna()
    df_likert = df.loc[:, likert_cols]
    df_free = df.loc[:, ~likert_cols]
    df_likert_meta = df_meta[likert_cols]

    # convert likert scale to numerical values
    for i, likert_scale in enumerate(LIKERT_SCALE):
        df_likert = df_likert.replace(likert_scale, len(LIKERT_SCALE) - i)
    df_likert = df_likert.astype(int)
    df_likert.loc[:, ~df_likert_meta["higher_is_better"]] = len(LIKERT_SCALE) - (
        df_likert.loc[:, ~df_likert_meta["higher_is_better"]] - 1
    )

    # group by question groups
    # df_grouped = df_likert.groupby(df_likert_meta["group"], axis=1)
    # calculate mean and std for each group

    # multiindex by group and question
    df_likert.columns = pd.MultiIndex.from_frame(
        pd.DataFrame({"group": df_likert_meta["group"], "question": df_likert.columns})
    )
    # calculate mean and std for each group per row
    df_likert_grouped = df_likert.groupby(level="group", axis=1, sort=False)
    df_likert_mean = df_likert_grouped.mean()
    df_likert_mean["mean"] = df_likert_mean.mean(axis=1)
    df_likert_std = df_likert_grouped.std()
    df_likert_std["mean"] = df_likert_std.mean(axis=1)

    # calculate corr
    df_likert_mean_corr = df_likert_mean.corr()

    # calculate mean and std for each column
    df_likert_grouped_colwise = df_likert.T.groupby(level="group", axis=0, sort=False)
    df_liekrt_mean_colwise = (
        df_likert_grouped_colwise.mean().mean(axis=1).rename("mean")
    )
    df_likert_std_colwise = df_likert_grouped_colwise.std().mean(axis=1).rename("std")
    df_likert_alpha = df_likert_grouped.apply(lambda x: pg.cronbach_alpha(x)).rename(
        "cronbach_alpha"
    )
    df_likert_colwise = pd.concat(
        [df_liekrt_mean_colwise, df_likert_std_colwise, df_likert_alpha], axis=1
    )

    # export to html
    dfs_to_write = [
        "自由記述",
        df_free,
        "回答ごとのグループに関する平均",
        df_likert_mean.round(2),
        "グループに関する平均の相関",
        df_likert_mean_corr.round(2),
        "回答ごとのグループに関する分散",
        df_likert_std.round(2),
        "グループに関する統計値",
        df_likert_colwise.round(2),
        "選択型",
        df_likert,
    ]
    export_multiple_frames_to_html(dfs_to_write, Path(out_path))
