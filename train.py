import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import joblib

# Данные (имитация звонков)
data = [
    ("buy subscription", "sales"),
    ("price cost", "sales"),
    ("how much", "sales"),
    ("not working error", "support"),
    ("help me problem", "support"),
    ("login failed", "support"),
    ("angry manager", "escalation"),
    ("urgent fail", "escalation"),
    ("lawsuit legal", "escalation")
]
df = pd.DataFrame(data, columns=["text", "category"])

# Обучение
print("Training model...")
model = make_pipeline(TfidfVectorizer(), LogisticRegression())
model.fit(df["text"], df["category"])

# Сохранение
joblib.dump(model, "router_model.pkl")
print("Model saved as router_model.pkl")