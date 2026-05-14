from tensorflow.keras.models import load_model
import numpy as np
import cv2
import os

# ---------------- LOAD MODEL ----------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "best_model_6cls with_default_spliting.keras"
)

model = load_model(MODEL_PATH)


# ---------------- PREPROCESS ----------------

def preprocess_image(image_path):

    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Invalid image path")

    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (224, 224))
    img = img.astype("float32") / 255.0

    img = np.expand_dims(img, axis=-1)
    img = np.expand_dims(img, axis=0)

    return img


# ---------------- PREDICTION ----------------

def predict_oct(image_path):

    img = preprocess_image(image_path)

    prediction = model.predict(img)

    class_index = int(np.argmax(prediction))
    confidence = float(np.max(prediction))

    classes = [
        "CNV",
        "DME",
        "DR",
        "NORMAL",
        "MH",
        "AMD",
        "CSR",
        "DRUSEN"
    ]

    disease = classes[class_index]

    return disease, confidence
