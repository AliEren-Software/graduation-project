import hmac

from flask import Blueprint, jsonify, request

from ..config import UPLOAD_TOKEN
from ..repositories import (
    fetch_customer_quality_counts,
    fetch_file_status_by_session_id,
    fetch_file_status_rows,
    fetch_raw_customer_duplicate_count,
    fetch_raw_customers_with_invalid_id,
    get_session_status,
)
from ..services import handle_upload
from ..utils import clean_error_message


api_bp = Blueprint("api", __name__)


@api_bp.before_request
def require_authorization():
    authorization = request.headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if (
        not separator
        or scheme.lower() != "bearer"
        or not hmac.compare_digest(token, UPLOAD_TOKEN)
    ):
        return jsonify({"error": "Unauthorized"}), 401


@api_bp.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    return handle_upload(request.files["file"])


@api_bp.route("/odi/sessions/<int:sess_no>/status", methods=["GET"])
@api_bp.route("/odi-status/<int:sess_no>", methods=["GET"])
def odi_status(sess_no):
    result = get_session_status(sess_no)

    if not result:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(result)


@api_bp.route("/customers/invalid-ids", methods=["GET"])
def raw_customers_invalid_id():
    try:
        rows = fetch_raw_customers_with_invalid_id()
        return jsonify({
            "status": "success",
            "count": len(rows),
            "data": rows,
        })
    except Exception as error:
        return jsonify({
            "status": "failed",
            "error_message": clean_error_message(str(error)),
        }), 500


@api_bp.route("/customers/quality/null-counts", methods=["GET"])
@api_bp.route("/customer-quality-counts", methods=["GET"])
def customer_quality_counts():
    try:
        result = fetch_customer_quality_counts()

        if not result:
            return jsonify({"error": "No data found"}), 404

        return jsonify({
            "status": "success",
            "data": result,
        })
    except Exception as error:
        return jsonify({
            "status": "failed",
            "error_message": clean_error_message(str(error)),
        }), 500


@api_bp.route("/raw/customers/duplicate-count", methods=["GET"])
@api_bp.route("/customers/duplicate-count", methods=["GET"])
def raw_customer_duplicate_count():
    try:
        result = fetch_raw_customer_duplicate_count()

        if not result:
            return jsonify({"error": "No data found"}), 404

        return jsonify({
            "status": "success",
            "data": result,
        })
    except Exception as error:
        return jsonify({
            "status": "failed",
            "error_message": clean_error_message(str(error)),
        }), 500


@api_bp.route("/file-status", methods=["GET"])
def file_status():
    try:
        rows = fetch_file_status_rows()
        return jsonify({
            "count": len(rows),
            "data": rows,
        })
    except Exception as error:
        return jsonify({
            "status": "failed",
            "error_message": clean_error_message(str(error)),
        }), 500


@api_bp.route("/file-status/<int:session_id>", methods=["GET"])
def file_status_by_session_id(session_id):
    try:
        row = fetch_file_status_by_session_id(session_id)

        if not row:
            return jsonify({"error": "Session not found"}), 404

        return jsonify({
            "data": row,
        })
    except Exception as error:
        return jsonify({
            "status": "failed",
            "error_message": clean_error_message(str(error)),
        }), 500
