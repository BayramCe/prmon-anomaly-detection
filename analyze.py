import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# dataset 1 - simple workload with 3 clear anomaly phases
df = pd.read_csv("prmon_dataset.txt", sep="\t")
df["elapsed"] = df["wtime"]

# using 4 features here - no IO metrics since this workload was memory/proc only
features = ["pss", "rss", "nprocs", "nthreads"]
X = df[features].copy()

# anomaly windows determined from nprocs transitions (checked with awk)
anomaly_windows = [
    (602,  782,  "Anomaly 1: 3000MB, 8 procs"),
    (1382, 1622, "Anomaly 2: 1000MB, 16 procs"),
    (2224, 2314, "Anomaly 3: 4000MB, 4 procs"),
]

df["true_anomaly"] = df["elapsed"].apply(
    lambda t: int(any(lo <= t <= hi for lo, hi, _ in anomaly_windows))
)

n_anom = df["true_anomaly"].sum()
contamination = n_anom / len(df)
print(f"anomaly ratio: {contamination:.3f}  ({n_anom}/{len(df)})")

# scale and fit - contamination set from ground truth
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

iforest = IsolationForest(n_estimators=200, contamination=contamination, random_state=42)
iforest.fit(X_scaled)

df["if_score"] = iforest.decision_function(X_scaled)
df["if_pred"]  = (iforest.predict(X_scaled) == -1).astype(int)

# evaluation
tp = ((df["if_pred"]==1) & (df["true_anomaly"]==1)).sum()
fp = ((df["if_pred"]==1) & (df["true_anomaly"]==0)).sum()
fn = ((df["if_pred"]==0) & (df["true_anomaly"]==1)).sum()
tn = ((df["if_pred"]==0) & (df["true_anomaly"]==0)).sum()

prec = tp/(tp+fp) if tp+fp else 0
rec  = tp/(tp+fn) if tp+fn else 0
f1   = 2*prec*rec/(prec+rec) if prec+rec else 0

print(f"precision={prec:.3f}  recall={rec:.3f}  f1={f1:.3f}")
print(f"tp={tp}  fp={fp}  fn={fn}  tn={tn}")

# ---- plots ----
fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
fig.suptitle("prmon Time-Series Anomaly Detection — ATLAS SPOT GSoC 2026",
             fontsize=13, fontweight="bold")

def shade(ax, color="orange"):
    for lo, hi, _ in anomaly_windows:
        ax.axvspan(lo, hi, alpha=0.15, color=color)

ax = axes[0]
ax.plot(df["elapsed"], df["pss"]/1024, color="steelblue", lw=0.8, label="PSS (MB)")
ax.scatter(df.loc[df["if_pred"]==1, "elapsed"],
           df.loc[df["if_pred"]==1, "pss"]/1024,
           color="red", s=8, zorder=5, label="detected anomaly")
shade(ax)
ax.set_ylabel("PSS (MB)")
ax.legend(fontsize=8, loc="upper right")
ax.grid(alpha=0.3)

ax = axes[1]
ax.plot(df["elapsed"], df["nprocs"],   color="green",  lw=0.8, label="nprocs")
ax.plot(df["elapsed"], df["nthreads"], color="purple", lw=0.8, label="nthreads", alpha=0.7)
ax.scatter(df.loc[df["if_pred"]==1, "elapsed"],
           df.loc[df["if_pred"]==1, "nprocs"],
           color="red", s=8, zorder=5)
shade(ax)
ax.set_ylabel("count")
ax.legend(fontsize=8, loc="upper right")
ax.grid(alpha=0.3)

ax = axes[2]
ax.plot(df["elapsed"], df["if_score"], color="dimgray", lw=0.8, label="IF score")
thr = np.percentile(df["if_score"], contamination*100)
ax.axhline(thr, color="red", ls="--", lw=1, label=f"threshold ({thr:.3f})")
shade(ax)
ax.set_ylabel("score (lower = anomalous)")
ax.set_xlabel("elapsed time (s)")
ax.legend(fontsize=7, loc="upper right")
ax.grid(alpha=0.3)

fig.legend(
    handles=[mpatches.Patch(color="orange", alpha=0.3, label="injected anomaly window")],
    loc="lower center", fontsize=9
)
plt.tight_layout(rect=[0, 0.03, 1, 1])
plt.savefig("anomaly_detection.png", dpi=150, bbox_inches="tight")
plt.show()
print("saved anomaly_detection.png")
