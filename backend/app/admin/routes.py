from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User

admin_bp = Blueprint("admin", __name__)


def current_user():
    return db.session.get(User, int(get_jwt_identity()))


def require_admin(user):
    if user.role != "admin":
        return jsonify({"error": "Admin access required"}), 403
    return None


def require_superuser(user):
    if user.role != "admin" or not user.is_superuser:
        return jsonify({"error": "Superuser access required"}), 403
    return None


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    user = current_user()
    err = require_admin(user)
    if err:
        return err
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    user = current_user()
    err = require_admin(user)
    if err:
        return err
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": target.to_dict(include_emails=True)}), 200


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    user = current_user()
    err = require_admin(user)
    if err:
        return err
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404
    if target.id == user.id:
        return jsonify({"error": "Cannot delete your own account"}), 400

    db.session.delete(target)
    db.session.commit()
    return jsonify({"message": "User and all associated data deleted"}), 200


@admin_bp.route("/users/<int:user_id>/upgrade", methods=["POST"])
@jwt_required()
def upgrade_user(user_id):
    user = current_user()
    err = require_superuser(user)
    if err:
        return err
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404
    target.plan = "gold"
    db.session.commit()
    return jsonify({"message": f"{target.first_name} upgraded to gold plan", "user": target.to_dict()}), 200


@admin_bp.route("/users/<int:user_id>/downgrade", methods=["POST"])
@jwt_required()
def downgrade_user(user_id):
    user = current_user()
    err = require_superuser(user)
    if err:
        return err
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404
    target.plan = "free"
    db.session.commit()
    return jsonify({"message": f"{target.first_name} downgraded to free plan", "user": target.to_dict()}), 200


@admin_bp.route("/users/<int:user_id>/grant-admin", methods=["POST"])
@jwt_required()
def grant_admin(user_id):
    user = current_user()
    err = require_superuser(user)
    if err:
        return err
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404
    target.role = "admin"
    db.session.commit()
    return jsonify({"message": f"{target.first_name} granted admin access", "user": target.to_dict()}), 200


@admin_bp.route("/users/<int:user_id>/revoke-admin", methods=["POST"])
@jwt_required()
def revoke_admin(user_id):
    user = current_user()
    err = require_superuser(user)
    if err:
        return err
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404
    if target.id == user.id:
        return jsonify({"error": "Cannot revoke your own admin access"}), 400
    target.role = "normal"
    target.is_superuser = False
    db.session.commit()
    return jsonify({"message": f"{target.first_name}'s admin access revoked", "user": target.to_dict()}), 200


@admin_bp.route("/users/<int:user_id>/grant-superuser", methods=["POST"])
@jwt_required()
def grant_superuser(user_id):
    user = current_user()
    err = require_superuser(user)
    if err:
        return err
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404
    if target.role != "admin":
        return jsonify({"error": "User must be an admin first"}), 400
    target.is_superuser = True
    db.session.commit()
    return jsonify({"message": f"{target.first_name} granted superuser rights", "user": target.to_dict()}), 200


@admin_bp.route("/users/<int:user_id>/revoke-superuser", methods=["POST"])
@jwt_required()
def revoke_superuser(user_id):
    user = current_user()
    err = require_superuser(user)
    if err:
        return err
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404
    if target.id == user.id:
        return jsonify({"error": "Cannot revoke your own superuser rights"}), 400
    target.is_superuser = False
    db.session.commit()
    return jsonify({"message": f"{target.first_name}'s superuser rights revoked", "user": target.to_dict()}), 200
