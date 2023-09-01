from flask import Flask, request, send_from_directory, jsonify, abort
import os
import uuid

app = Flask(__name__)

# Directory to store uploaded files
CDN_DIRECTORY = "cdn_assets"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}  # you can modify this set based on your requirements

if not os.path.exists(CDN_DIRECTORY):
    os.makedirs(CDN_DIRECTORY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_asset():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in the request"}), 400

    uploaded_file = request.files['file']
    
    if uploaded_file.filename == '':
        return jsonify({"success": False, "error": "No files selected"}), 400
    
    if not allowed_file(uploaded_file.filename):
        return jsonify({"success": False, "error": "File type not allowed"}), 400

    unique_filename = str(uuid.uuid4()) + os.path.splitext(uploaded_file.filename)[1]
    file_path = os.path.join(CDN_DIRECTORY, unique_filename)
    uploaded_file.save(file_path)
    
    return jsonify({"success": True, "cdn_url": f"/assets/{unique_filename}"}), 201

@app.route('/assets/<filename>', methods=['GET'])
def retrieve_asset(filename):
    if not os.path.exists(os.path.join(CDN_DIRECTORY, filename)):
        abort(404)  # File not found
    return send_from_directory(CDN_DIRECTORY, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=8080)
