"""Train and serialize the delay model during Docker build."""
import pandas as pd
from challenge.model import DelayModel

model = DelayModel()
data = pd.read_csv("data/data.csv", low_memory=False)
features, target = model.preprocess(data, target_column="delay")
model.fit(features, target)
model.save("data/delay_model.pkl")
print("Model trained and saved successfully")
