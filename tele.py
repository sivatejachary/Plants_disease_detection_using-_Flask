from flask import Flask, request, render_template, redirect, url_for, session, send_from_directory
import os
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
from werkzeug.utils import secure_filename
import pandas as pd
import telebot
import csv

# Flask app setup
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Telegram Bot setup
telegram_bot_token = '6901622275:AAHFJGKZTMb6yMa6uwdE7CozJ29dd3l8hpI'
bot = telebot.TeleBot(telegram_bot_token)

# Ensure the UPLOAD_FOLDER exists and is used to store uploaded images
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load model and CSV data
model = tf.keras.models.load_model('PlantDNet.h5', compile=False)
disease_descriptions_df = pd.read_csv('disease_info.csv', encoding='ISO-8859-1')

# Common functionalities
def model_predict(img_path, model):
    img = image.load_img(img_path, target_size=(64, 64))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x /= 255
    preds = model.predict(x)
    return preds

def get_disease_info(disease_name, dataframe):
    disease_info = dataframe[dataframe['disease_name'] == disease_name].iloc[0]
    return disease_info

# Flask routes for web interface
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def upload():
    if 'image' in request.files:
        file = request.files['image']
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        preds = model_predict(file_path, model)
        # Assume classes are the same as in the Telegram bot section
        disease_class = ['Pepper__bell___Bacterial_spot', 'Pepper__bell___healthy', 'Potato___Early_blight',
                           'Potato___Late_blight', 'Potato___healthy', 'Tomato_Bacterial_spot', 'Tomato_Early_blight',
                           'Tomato_Late_blight', 'Tomato_Leaf_Mold', 'Tomato_Septoria_leaf_spot',
                           'Tomato_Spider_mites_Two_spotted_spider_mite', 'Tomato__Target_Spot',
                           'Tomato__Tomato_YellowLeaf__Curl_Virus', 'Tomato__Tomato_mosaic_virus', 'Tomato_healthy']  # Define your classes here
        index = np.argmax(preds[0])
        result = disease_class[index]

        disease_info = get_disease_info(result, disease_descriptions_df)
        # Store results in session or directly pass to template
        return redirect(url_for('submit'))

@app.route('/submit')
def submit():
    # Example details retrieval from session (adjust according to your application logic)
    details = {
        'image_path': session.get('image_path', 'default_image.jpg'),
        'result': session.get('result', 'No result'),
        'description': session.get('description', 'No description'),
        'pesticide': session.get('pesticide', 'No pesticide recommendation'),
        'product_link': session.get('product_link', '#')
    }
    return render_template('submit.html', details=details)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Telegram bot handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Send me an image of a plant, and I'll detect any diseases in it.")

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    # Similar to the Flask upload route, but adapted for Telegram
    pass  # Implement Telegram image handling and response

# Flask command to run the app
def run_flask():
    app.run(debug=True, use_reloader=False)

# Main execution
if __name__ == '__main__':
    from threading import Thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    bot.polling(none_stop=True)
