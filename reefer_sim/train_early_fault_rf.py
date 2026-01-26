import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score
)

import joblib

# ==============================
# CONFIGURATION
# ==============================

DATASET_PATH = "logs/reefer_dataset.csv"

WINDOW_SIZE = 10          # minutes of past data used as input
PREDICTION_HORIZON = 5    # minutes ahead to predict fault

RANDOM_STATE = 42

# ==============================
# LOAD DATA
# ==============================

df = pd.read_csv(DATASET_PATH)

# Ensure proper ordering
df = df.sort_values(["run_id", "time_min"]).reset_index(drop=True)

# ==============================
# CREATE EARLY FAULT LABEL
# ==============================

# Any fault flag
df["any_fault"] = (
    df["fault_power"] |
    df["fault_door"] |
    df["fault_cooling"]
)

df["early_fault"] = 0

for run_id, run_df in df.groupby("run_id"):
    indices = run_df.index.tolist()

    for i, idx in enumerate(indices):
        future_indices = indices[i + 1 : i + 1 + PREDICTION_HORIZON]

        if len(future_indices) == 0:
            continue

        if run_df.loc[future_indices, "any_fault"].any():
            df.loc[idx, "early_fault"] = 1

# ==============================
# FEATURE EXTRACTION
# ==============================

features = []
labels = []

def extract_features(window):
    temp = window["temperature_C"]
    hum = window["humidity_pct"]
    risk = window["risk_index"]

    return [
        temp.mean(),                     # mean temperature
        temp.iloc[-1] - temp.iloc[0],    # temperature slope
        hum.mean(),                      # mean humidity
        hum.iloc[-1] - hum.iloc[0],      # humidity slope
        risk.iloc[-1] - risk.iloc[0],    # risk growth
        temp.std(),                      # temperature variability
        hum.std()                        # humidity variability
    ]

for run_id, run_df in df.groupby("run_id"):
    run_df = run_df.reset_index(drop=True)

    for i in range(WINDOW_SIZE, len(run_df) - PREDICTION_HORIZON):
        window = run_df.iloc[i - WINDOW_SIZE:i]

        features.append(extract_features(window))
        labels.append(run_df.loc[i, "early_fault"])

X = np.array(features)
y = np.array(labels)

print("Total samples:", len(y))
print("Positive (early fault) samples:", y.sum())

# ==============================
# TRAIN / TEST SPLIT
# ==============================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.30,
    random_state=RANDOM_STATE,
    stratify=y
)

# ==============================
# TRAIN RANDOM FOREST
# ==============================

rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=RANDOM_STATE,
    class_weight="balanced"
)

rf.fit(X_train, y_train)

# ==============================
# EVALUATION
# ==============================

y_pred = rf.predict(X_test)
proba = rf.predict_proba(X_test)

if proba.shape[1] == 2:
    y_prob = proba[:, 1]
else:
    # Only one class present
    y_prob = np.ones(len(X_test))

print("\n=== Classification Report ===")
print(classification_report(y_test, y_pred))

print("=== Confusion Matrix ===")
print(confusion_matrix(y_test, y_pred))

print("=== ROC AUC ===")
print(roc_auc_score(y_test, y_prob))

# ==============================
# FEATURE IMPORTANCE
# ==============================

feature_names = [
    "temp_mean",
    "temp_slope",
    "hum_mean",
    "hum_slope",
    "risk_growth",
    "temp_std",
    "hum_std"
]

print("\n=== Feature Importance ===")
for name, importance in zip(feature_names, rf.feature_importances_):
    print(f"{name:15s}: {importance:.4f}")

# ==============================
# SAVE MODEL
# ==============================

joblib.dump(rf, "early_fault_random_forest.pkl")

print("\nModel saved as early_fault_random_forest.pkl")
