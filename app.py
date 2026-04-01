import os
import uuid
import tempfile
from flask import Flask, render_template, request, jsonify, session, send_file
from werkzeug.utils import secure_filename
from generator import classify_object, generate_summary, generate_glb_from_type

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change for production
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    description = ""
    if request.form.get('description'):
        description = request.form['description'].strip()
    elif 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            description = f"Image: {filename}"
        else:
            return jsonify({'error': 'Invalid image file'}), 400
    else:
        return jsonify({'error': 'No input provided'}), 400

    obj_type = classify_object(description)
    summary = generate_summary(description, obj_type)

    glb_bytes = generate_glb_from_type(obj_type)

    model_id = str(uuid.uuid4())
    model_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{model_id}.glb")
    with open(model_path, 'wb') as f:
        f.write(glb_bytes)

    session['model_path'] = model_path

    return jsonify({
        'summary': summary,
        'model_url': f'/model/{model_id}'
    })

@app.route('/model/<model_id>')
def get_model(model_id):
    model_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{model_id}.glb")
    if os.path.exists(model_path):
        return send_file(model_path, mimetype='model/gltf-binary')
    else:
        return "Model not found", 404

if __name__ == '__main__':
    app.run(debug=True)