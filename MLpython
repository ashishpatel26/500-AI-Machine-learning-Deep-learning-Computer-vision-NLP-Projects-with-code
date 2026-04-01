import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# Load dataset
data = pd.read_csv("dataset.csv")

X = data[['hours_study','sleep_hours','attendance']]
y = data['marks']

# Train model
model = LinearRegression()
model.fit(X, y)

print("=== AI Study Companion ===")
hours = float(input("Enter study hours: "))
sleep = float(input("Enter sleep hours: "))
attendance = float(input("Enter attendance %: "))

# Prediction
prediction = model.predict([[hours, sleep, attendance]])[0]

print(f"\n Predicted Marks: {prediction:.2f}")

# Smart Suggestions
if prediction < 50:
    print("You need serious improvement. Increase study hours!")
elif prediction < 75:
    print("You're doing okay. Stay consistent!")
else:
    print("Excellent! Keep it up!")

# Graph
plt.scatter(data['hours_study'], data['marks'])
plt.xlabel("Study Hours")
plt.ylabel("Marks")
plt.title("Study Hours vs Marks")
plt.show()