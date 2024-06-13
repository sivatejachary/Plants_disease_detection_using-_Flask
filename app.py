from flask import Flask, request, render_template, redirect, url_for, session, send_from_directory
import os
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
from werkzeug.utils import secure_filename
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Ensure the UPLOAD_FOLDER exists and is used to store uploaded images
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = tf.keras.models.load_model('PlantDNet.h5', compile=False)
disease_descriptions_df = pd.read_csv('disease_info.csv', encoding='ISO-8859-1')

def model_predict(img_path, model):
    img = image.load_img(img_path, target_size=(64, 64))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x /= 255
    preds = model.predict(x)
    return preds

@app.route('/', methods=['GET'])
def index():
    # Main page
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def upload():
    if 'image' in request.files:
        file = request.files['image']
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        preds = model_predict(file_path, model)
        disease_class = ['Pepper__bell___Bacterial_spot', 'Pepper__bell___healthy', 'Potato___Early_blight',
                         'Potato___Late_blight', 'Potato___healthy', 'Tomato_Bacterial_spot', 'Tomato_Early_blight',
                         'Tomato_Late_blight', 'Tomato_Leaf_Mold', 'Tomato_Septoria_leaf_spot',
                         'Tomato_Spider_mites_Two_spotted_spider_mite', 'Tomato__Target_Spot',
                         'Tomato__Tomato_YellowLeaf__Curl_Virus', 'Tomato__Tomato_mosaic_virus', 'Tomato_healthy']  # Update your classes here
        index = np.argmax(preds[0])
        result = disease_class[index]

        disease_info = disease_descriptions_df[disease_descriptions_df['disease_name'] == result].iloc[0]
        session['image_path'] = filename
        session['result'] = result
        session['description'] = disease_info['description']
        session['pesticide'] = disease_info['pesticide']
        session['product_link'] = disease_info['product_link']
        
        return redirect(url_for('submit'))

@app.route('/submit')
def submit():
    # Fetch details from the session
    details = {
        'image_path': session.get('image_path', None),
        'result': session.get('result', None),
        'description': session.get('description', None),
        'pesticide': session.get('pesticide', None),
        'product_link': session.get('product_link', None)
    }
    return render_template('submit.html', details=details)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
