from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Contact, User

contacts_bp = Blueprint("contacts", __name__)


def current_user():
    return db.session.get(User, int(get_jwt_identity()))


@contacts_bp.route("", methods=["GET"])
@jwt_required()
def list_contacts():
    user = current_user()
    contacts = Contact.query.filter_by(user_id=user.id).order_by(Contact.created_at.desc()).all()
    return jsonify({"contacts": [c.to_dict() for c in contacts]}), 200


@contacts_bp.route("", methods=["POST"])
@jwt_required()
def add_contact():
    user = current_user()
    data = request.get_json()
    if not data.get("name") or not data.get("email"):
        return jsonify({"error": "Name and email are required"}), 400

    contact = Contact(
        user_id=user.id,
        name=data["name"].strip(),
        email=data["email"].lower().strip(),
        phone=data.get("phone", "").strip() or None,
    )
    db.session.add(contact)
    db.session.commit()
    return jsonify({"message": "Contact added", "contact": contact.to_dict()}), 201


@contacts_bp.route("/<int:contact_id>", methods=["PUT"])
@jwt_required()
def update_contact(contact_id):
    user = current_user()
    contact = Contact.query.filter_by(id=contact_id, user_id=user.id).first_or_404()
    data = request.get_json()

    if data.get("name"):
        contact.name = data["name"].strip()
    if data.get("email"):
        contact.email = data["email"].lower().strip()
    if "phone" in data:
        contact.phone = data["phone"].strip() or None

    db.session.commit()
    return jsonify({"message": "Contact updated", "contact": contact.to_dict()}), 200


@contacts_bp.route("/<int:contact_id>", methods=["DELETE"])
@jwt_required()
def delete_contact(contact_id):
    user = current_user()
    contact = Contact.query.filter_by(id=contact_id, user_id=user.id).first_or_404()
    db.session.delete(contact)
    db.session.commit()
    return jsonify({"message": "Contact deleted"}), 200
