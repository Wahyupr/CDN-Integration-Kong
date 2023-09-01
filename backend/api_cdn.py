from flask import Flask, request, send_from_directory, jsonify, abort, render_template_string
import os
import uuid
import requests
import logging

app = Flask(__name__)

# For the CDN 
CDN_DIRECTORY = "cdn_assets"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

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

# For Kong integration
KONG_ADMIN_URL = "http://localhost:8001"
def create_service(name, url):
    logging.info("-=====Start Service Creation=====-")
    
    # Check if the service already exists
    response = requests.get(f"{KONG_ADMIN_URL}/services/{name}")
    if response.status_code == 200:
        logging.info("Service %s already exists. Skipping creation.", name)
        return response.json()['id']

    service_data = {
        "name": name,
        "url": url
    }
    response = requests.post(f"{KONG_ADMIN_URL}/services", data=service_data)
    service = response.json()
    
    if 'id' in service:
        logging.info("Service created with ID: %s", service['id'])
        return service['id']
    else:
        logging.error("Failed to create service. Response: %s", response.text)
        return None

def create_route(service_id, path_routes):
    logging.info("-=====Start Route Creation=====-")
    
    # Retrieve all routes associated with the service to check if our paths already exist
    response = requests.get(f"{KONG_ADMIN_URL}/services/{service_id}/routes")
    if response.status_code != 200:
        logging.error("Failed to retrieve routes for service_id: %s. Response: %s", service_id, response.text)
        return
    
    existing_routes = response.json().get('data', [])
    existing_paths = [path for route in existing_routes for path in route.get('paths', [])]
    
    # Check which paths from path_routes are not in existing_paths
    paths_to_create = [path for path in path_routes if path not in existing_paths]
    
    if not paths_to_create:
        logging.info("All route paths already exist for service_id: %s. Skipping creation.", service_id)
        return

    route_data = {
        "protocols": ["http"],
        "strip_path": True,
        "preserve_host": True,
        "service": {"id": service_id},
        "paths": paths_to_create
    }

    response = requests.post(f"{KONG_ADMIN_URL}/routes", json=route_data)
    if response.status_code == 201:
        logging.info("Route created successfully for service_id: %s", service_id)
    else:
        logging.error("Failed to create route. Status code: %s, Response: %s", response.status_code, response.text)




def migrate(name, url, service_name, path_routes):
    logging.info("--%s--", service_name)
    
    service_id = create_service(name, url)
    if service_id:
        create_route(service_id, path_routes)
    else:
        logging.error("Migration failed for service: %s", service_name)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate("cdn_api", "http://host.docker.internal:9000", "cdn_api", ["/cdn"])
    app.run(debug=True, port=9000)