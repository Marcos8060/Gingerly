from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Email, Contact, User
from app.mail_service import deliver_email

emails_bp = Blueprint("emails", __name__)


def current_user():
    return db.session.get(User, int(get_jwt_identity()))


@emails_bp.route("", methods=["GET"])
@jwt_required()
def list_emails():
    user = current_user()
    emails = Email.query.filter_by(sender_id=user.id).order_by(Email.created_at.desc()).all()
    return jsonify({"emails": [e.to_dict() for e in emails]}), 200


@emails_bp.route("", methods=["POST"])
@jwt_required()
def send_email():
    user = current_user()
    data = request.get_json()

    if not data.get("contact_id") or not data.get("subject") or not data.get("body"):
        return jsonify({"error": "contact_id, subject, and body are required"}), 400

    contact = Contact.query.filter_by(id=data["contact_id"], user_id=user.id).first()
    if not contact:
        return jsonify({"error": "Contact not found"}), 404

    status = deliver_email(contact.name, contact.email, data["subject"].strip(), data["body"].strip())

    email = Email(
        sender_id=user.id,
        contact_id=contact.id,
        subject=data["subject"].strip(),
        body=data["body"].strip(),
        status=status,
        sent_at=datetime.now(timezone.utc) if status == "sent" else None,
    )
    db.session.add(email)
    db.session.commit()
    return jsonify({"message": f"Email {status}", "email": email.to_dict()}), 201


@emails_bp.route("/<int:email_id>", methods=["DELETE"])
@jwt_required()
def delete_email(email_id):
    user = current_user()
    email = Email.query.filter_by(id=email_id, sender_id=user.id).first_or_404()
    db.session.delete(email)
    db.session.commit()
    return jsonify({"message": "Email deleted"}), 200


@emails_bp.route("/<int:email_id>/retry", methods=["POST"])
@jwt_required()
def retry_email(email_id):
    user = current_user()
    if user.plan != "gold":
        return jsonify({"error": "Gold plan required to retry emails"}), 403

    email = Email.query.filter_by(id=email_id, sender_id=user.id).first_or_404()
    if email.status != "failed":
        return jsonify({"error": "Only failed emails can be retried"}), 400

    status = deliver_email(email.contact.name, email.contact.email, email.subject, email.body)
    email.status = status
    if status == "sent":
        email.sent_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"message": f"Retry {status}", "email": email.to_dict()}), 200
