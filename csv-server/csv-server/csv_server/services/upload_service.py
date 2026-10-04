import os
import threading

from flask import jsonify
from werkzeug.utils import secure_filename

from ..config import ALLOWED_EXTENSIONS, DUPLICATE_FOLDER, FILE_DESTINATIONS, UPLOAD_FOLDER
from ..repositories import reserve_job_id
from ..utils import clean_error_message


active_uploads = set()
active_uploads_lock = threading.Lock()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def resolve_upload_directory(filename):
    return FILE_DESTINATIONS.get(filename.lower(), UPLOAD_FOLDER)


def try_reserve_upload(filename):
    normalized_name = filename.lower()

    with active_uploads_lock:
        if normalized_name in active_uploads:
            return False

        active_uploads.add(normalized_name)
        return True


def release_upload(filename):
    normalized_name = filename.lower()

    with active_uploads_lock:
        active_uploads.discard(normalized_name)


def build_duplicate_filepath(filename):
    base_name, extension = os.path.splitext(filename)
    candidate_path = os.path.join(DUPLICATE_FOLDER, filename)

    if not os.path.exists(candidate_path):
        return candidate_path

    counter = 1
    while True:
        candidate_name = f"{base_name}_{counter}{extension}"
        candidate_path = os.path.join(DUPLICATE_FOLDER, candidate_name)
        if not os.path.exists(candidate_path):
            return candidate_path
        counter += 1


def save_duplicate_file(file_storage, filename, message):
    duplicate_filepath = build_duplicate_filepath(filename)
    file_storage.save(duplicate_filepath)
    return jsonify({
        "status": "duplicate",
        "job_id": None,
        "message": message,
        "filename": filename,
        "path": duplicate_filepath,
    }), 202


def handle_upload(file_storage):
    if file_storage.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file_storage.filename):
        return jsonify({"error": "Only CSV or TXT files allowed"}), 400

    filename = secure_filename(file_storage.filename)
    is_primary_upload = try_reserve_upload(filename)

    if not is_primary_upload:
        return save_duplicate_file(
            file_storage,
            filename,
            "Same file is already being processed. Saved to duplicate folder.",
        )

    try:
        target_directory = resolve_upload_directory(filename)
        os.makedirs(target_directory, exist_ok=True)
        filepath = os.path.join(target_directory, filename)

        if os.path.exists(filepath):
            return save_duplicate_file(
                file_storage,
                filename,
                "Same filename already exists in the target folder. Saved to duplicate folder.",
            )

        file_storage.save(filepath)

        try:
            job_id = reserve_job_id()
        except Exception as error:
            return jsonify({
                "status": "failed",
                "error_message": clean_error_message(str(error)),
            }), 500

        return jsonify({
            "status": "success",
            "job_id": job_id,
            "filename": filename,
            "path": filepath,
        })
    finally:
        release_upload(filename)
