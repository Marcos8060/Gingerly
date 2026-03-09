from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    required = ["first_name", "last_name", "email_address", "phone_number", "password"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": "All fields are required"}), 400

    if User.query.filter_by(email_address=data["email_address"].lower()).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        email_address=data["email_address"].lower().strip(),
        phone_number=data["phone_number"].strip(),
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"message": "Account created successfully", "token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data.get("email_address") or not data.get("password"):
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email_address=data["email_address"].lower()).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    return jsonify({"message": "Logged out successfully"}), 200
