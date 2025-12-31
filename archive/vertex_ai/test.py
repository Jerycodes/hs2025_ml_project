import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# 1. KONFIGURATION
# ---------------------------------------------------------
FILE_PATH = 'data/processed/datasets/eurusd_news_training.csv' # Pfad anpassen!
TEST_SIZE_PERCENT = 0.2  # Die neuesten 20% der Daten zum Testen

# ---------------------------------------------------------
# 2. DATEN LADEN
# ---------------------------------------------------------
print("Lade Daten...")
df = pd.read_csv(FILE_PATH)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# ---------------------------------------------------------
# 3. FEATURES & TARGET DEFINIEREN
# ---------------------------------------------------------
# Mapping: Wenn dein Label 'up', 'down', 'neutral' ist
label_map = {'neutral': 0, 'up': 1, 'down': 2}

# Falls deine CSV bereits 0,1,2 im 'label' hat, diesen Schritt anpassen
if df['label'].dtype == 'O': # O steht für Object (String)
    df['target'] = df['label'].map(label_map)
else:
    df['target'] = df['label'] # Falls schon numerisch

# Features auswählen (Alles außer Metadaten und Zukunftsdaten)
drop_cols = ['date', 'label', 'signal', 'direction', 'lookahead_return', 'target']
feature_cols = [c for c in df.columns if c not in drop_cols]

print(f"Anzahl Features: {len(feature_cols)}")

# NaN handling (XGBoost kann das eigentlich, aber besser sauber machen)
X = df[feature_cols].fillna(0) 
y = df['target']

# ---------------------------------------------------------
# 4. SPLIT (CHRONOLOGISCH)
# ---------------------------------------------------------
# WICHTIG: Nicht shuffeln bei Zeitreihen!
split_idx = int(len(df) * (1 - TEST_SIZE_PERCENT))

X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

# Class Weights berechnen (falls "neutral" viel öfter vorkommt)
from sklearn.utils.class_weight import compute_sample_weight
sample_weights = compute_sample_weight(class_weight='balanced', y=y_train)

# ---------------------------------------------------------
# 5. TRAINING (XGBoost)
# ---------------------------------------------------------
print("Starte Training...")
model = xgb.XGBClassifier(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=4,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1 # Nutzt alle CPU Kerne
)

model.fit(X_train, y_train, sample_weight=sample_weights)

# ---------------------------------------------------------
# 6. EVALUATION
# ---------------------------------------------------------
preds = model.predict(X_test)

print("\n--- CLASSIFICATION REPORT ---")
print(classification_report(y_test, preds, target_names=['Neutral', 'Up', 'Down']))

# Feature Importance Plot
xgb.plot_importance(model, max_num_features=15, importance_type='weight', title='Top 15 Features')
plt.show()