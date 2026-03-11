import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# load the prmon output - tab separated, first col is unix timestamp
df = pd.read_csv("prmon_dataset2.txt", sep="\t")
df["elapsed"] = df["wtime"]  # wtime = seconds since prmon started

# I'll use memory + io + process count as features.
# rchar/wchar captures the IO burst in faz 4 which PSS alone would miss.
features = ["pss", "rss", "nprocs", "nthreads", "rchar", "wchar"]
X = df[features].copy()

# these windows come from the workload script I wrote.
# determined by watching nprocs transitions with awk.
anomaly_windows = [
    (302,  542,  "Anomaly 1: Gradual RAM ramp-up"),
    (842,  878,  "Anomaly 2: IO burst (io-burner)"),
    (1240, 1254, "Anomaly 3: Short spike 977MB/7procs"),
    (1314, 1330, "Anomaly 4: Short spike 1221MB/9procs"),
    (1390, 1406, "Anomaly 5: Short spike 880MB/6procs"),
]

df["true_anomaly"] = df["elapsed"].apply(
    lambda t: int(any(lo <= t <= hi for lo, hi, _ in anomaly_windows))
)

n_anom = df["true_anomaly"].sum()
contamination = n_anom / len(df)
print(f"anomaly ratio: {contamination:.3f}  ({n_anom} out of {len(df)} samples)")

# --- baseline: z-score on PSS only ---
# simple but only looks at one dimension
pss_mean, pss_std = df["pss"].mean(), df["pss"].std()
df["z_pss"] = (df["pss"] - pss_mean) / pss_std
df["zscore_pred"] = (df["z_pss"].abs() > 2.5).astype(int)

# --- Isolation Forest on all features ---
# chose IF because it handles multivariate data without assuming
# a distribution, and works well on the kind of step-function
# anomalies prmon produces. contamination set from ground truth above.
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

iforest = IsolationForest(n_estimators=200, contamination=contamination, random_state=42)
iforest.fit(X_scaled)

df["if_score"] = iforest.decision_function(X_scaled)  # negative = more anomalous
df["if_pred"]  = (iforest.predict(X_scaled) == -1).astype(int)


def metrics(pred_col, name):
    tp = ((df[pred_col]==1) & (df["true_anomaly"]==1)).sum()
    fp = ((df[pred_col]==1) & (df["true_anomaly"]==0)).sum()
    fn = ((df[pred_col]==0) & (df["true_anomaly"]==1)).sum()
    tn = ((df[pred_col]==0) & (df["true_anomaly"]==0)).sum()
    prec = tp/(tp+fp) if tp+fp else 0
    rec  = tp/(tp+fn) if tp+fn else 0
    f1   = 2*prec*rec/(prec+rec) if prec+rec else 0
    print(f"\n{name}:  precision={prec:.3f}  recall={rec:.3f}  f1={f1:.3f}")
    print(f"  tp={tp}  fp={fp}  fn={fn}  tn={tn}")
    return prec, rec, f1

metrics("zscore_pred", "Z-score (PSS only)")
metrics("if_pred",     "Isolation Forest (6 features)")

# ---- plotting ----
fig, axes = plt.subplots(4, 1, figsize=(16, 14), sharex=True)
fig.suptitle("prmon Anomaly Detection: Z-score vs Isolation Forest — Dataset 2",
             fontsize=13, fontweight="bold")

def shade(ax):
    for lo, hi, _ in anomaly_windows:
        ax.axvspan(lo, hi, alpha=0.12, color="green")

# panel 1 - memory
ax = axes[0]
ax.plot(df["elapsed"], df["pss"]/1024, color="steelblue", lw=0.8, label="PSS (MB)")
ax.scatter(df.loc[df["zscore_pred"]==1, "elapsed"],
           df.loc[df["zscore_pred"]==1, "pss"]/1024,
           color="orange", s=14, zorder=5, marker="^", label="Z-score")
ax.scatter(df.loc[df["if_pred"]==1, "elapsed"],
           df.loc[df["if_pred"]==1, "pss"]/1024,
           color="red", s=8, zorder=6, label="Isolation Forest")
shade(ax)
ax.set_ylabel("PSS (MB)")
ax.legend(fontsize=8, loc="upper right")
ax.grid(alpha=0.3)

# panel 2 - write bytes (catches io burst)
ax = axes[1]
ax.plot(df["elapsed"], df["wchar"]/1e6, color="saddlebrown", lw=0.8, label="wchar (MB)")
ax.scatter(df.loc[df["if_pred"]==1, "elapsed"],
           df.loc[df["if_pred"]==1, "wchar"]/1e6,
           color="red", s=8, zorder=5)
shade(ax)
ax.set_ylabel("wchar (MB)")
ax.legend(fontsize=8, loc="upper right")
ax.grid(alpha=0.3)

# panel 3 - process count
ax = axes[2]
ax.plot(df["elapsed"], df["nprocs"], color="darkgreen", lw=0.8, label="nprocs")
ax.scatter(df.loc[df["if_pred"]==1, "elapsed"],
           df.loc[df["if_pred"]==1, "nprocs"],
           color="red", s=8, zorder=5)
shade(ax)
ax.set_ylabel("nprocs")
ax.legend(fontsize=8, loc="upper right")
ax.grid(alpha=0.3)

# panel 4 - IF anomaly score
ax = axes[3]
ax.plot(df["elapsed"], df["if_score"], color="dimgray", lw=0.8, label="IF score")
thr = np.percentile(df["if_score"], contamination*100)
ax.axhline(thr, color="red", ls="--", lw=1, label=f"threshold ({thr:.3f})")
shade(ax)
ax.set_ylabel("score (lower = anomalous)")
ax.set_xlabel("elapsed time (s)")
ax.legend(fontsize=7, loc="upper right")
ax.grid(alpha=0.3)

fig.legend(
    handles=[mpatches.Patch(color="green", alpha=0.3, label="injected anomaly window")],
    loc="lower center", fontsize=9
)
plt.tight_layout(rect=[0, 0.03, 1, 1])
plt.savefig("anomaly_detection2.png", dpi=150, bbox_inches="tight")
plt.show()
print("saved anomaly_detection2.png")
