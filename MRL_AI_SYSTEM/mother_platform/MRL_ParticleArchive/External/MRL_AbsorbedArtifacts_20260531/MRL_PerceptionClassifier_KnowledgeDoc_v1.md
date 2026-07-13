# ML Models Documentation

This document describes the Machine Learning models used in the chat application for:

- Spam Detection
- Toxic Message Detection

---

## 1. Spam Detection Model

### Dataset
- File: `spam.csv`
- Columns used:
  - `v1` → label (ham/spam)
  - `v2` → message text

### Data Preprocessing
- Renamed columns to `label` and `message`
- Converted labels:
  - `ham` → 0
  - `spam` → 1
- Removed unnecessary columns

### Feature Extraction
- Technique: TF-IDF Vectorization
- Parameters:
  - `stop_words = 'english'`
  - `max_features = 5000`

### Model Used
- Algorithm: Multinomial Naive Bayes

### Training
- Train/Test Split:
  - 80% training
  - 20% testing
- Random State: 42

### Evaluation Metrics
- Accuracy Score
- Classification Report (Precision, Recall, F1-score)

### Prediction Function
```python
def predict_spam(text):
    text_vec = vectorizer.transform([text])
    prob = model.predict_proba(text_vec)[0][1]
    return prob
```

## Example Predictions

- **"Free money click now!!!"** → High spam probability  
- **"Let's meet tomorrow"** → Low spam probability  

## Model Export

- `spam_model.pkl`  
- `spam_vectorizer.pkl`

## 2. Toxic Message Detection Model

### Dataset
- File: `data.csv`  
- Columns used:
  - `comment_text`
  - `target`

### Data Preprocessing
- Created binary label:
  - `toxic = 1` if `target > 0.5`
  - else `0`
- Selected relevant columns:
  - `comment_text`, `toxic`

### Feature Extraction
- Technique: TF-IDF Vectorization  
- Parameters:
  - `stop_words = 'english'`
  - `max_features = 10000`

### Model Used
- Algorithm: Logistic Regression  
- Parameters:
  - `max_iter = 1000`

### Training
- Train/Test Split:
  - 80% training
  - 20% testing  
- Random State: 42

### Evaluation Metrics
- Accuracy Score  
- Classification Report  

### Prediction Function
```python
def predict_toxicity(text):
    text_vec = tfidf.transform([text])
    prob = model.predict_proba(text_vec)[0][1]
    return prob
```

## Example Predictions

- **"You are stupid"** → High toxicity
- **"Have a great day"** → Low toxicity  

## Model Export

- `toxic_model.pkl`  
- `toxic_vectorizer.pkl`

## Integration in Chat App

Both models are used for real-time message analysis.

### Workflow
1. User sends message  
2. Message is vectorized  
3. Passed to ML model  
4. Probability score generated  
5. If threshold exceeded:
   - Flag as spam/toxic  
   - Take action (warn, block, or filter)  

### Future Improvements
- Use deep learning models (LSTM or Transformers)  
- Improve dataset quality  
- Add multilingual support  
- Real-time model retraining  
- Context-aware toxicity detection

## Files

- `spam_model.pkl`  
- `spam_vectorizer.pkl`  
- `toxic_model.pkl`  
- `tfidf_vectorizer.pkl`

| Feature         | Model               | Technique |
| --------------- | ------------------- | --------- |
| Spam Detection  | Naive Bayes         | TF-IDF    |
| Toxic Detection | Logistic Regression | TF-IDF    |
