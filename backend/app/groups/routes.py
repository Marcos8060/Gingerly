from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Group, Contact, GroupEmail, GroupEmailRecipient, User
from app.mail_service import deliver_email

groups_bp = Blueprint("groups", __name__)


def current_user():
    return db.session.get(User, int(get_jwt_identity()))


def require_gold(user):
    if user.plan != "gold":
        return jsonify({"error": "Gold plan required"}), 403
    return None


@groups_bp.route("", methods=["GET"])
@jwt_required()
def list_groups():
    user = current_user()
    err = require_gold(user)
    if err:
        return err
    groups = Group.query.filter_by(user_id=user.id).order_by(Group.created_at.desc()).all()
    return jsonify({"groups": [g.to_dict(include_contacts=True) for g in groups]}), 200


@groups_bp.route("", methods=["POST"])
@jwt_required()
def create_group():
    user = current_user()
    err = require_gold(user)
    if err:
        return err
    data = request.get_json()
    if not data.get("name"):
        return jsonify({"error": "Group name is required"}), 400

    group = Group(user_id=user.id, name=data["name"].strip())
    db.session.add(group)
    db.session.commit()
    return jsonify({"message": "Group created", "group": group.to_dict()}), 201


@groups_bp.route("/<int:group_id>", methods=["GET"])
@jwt_required()
def get_group(group_id):
    user = current_user()
    err = require_gold(user)
    if err:
        return err
    group = Group.query.filter_by(id=group_id, user_id=user.id).first_or_404()
    return jsonify({"group": group.to_dict(include_contacts=True)}), 200


@groups_bp.route("/<int:group_id>", methods=["DELETE"])
@jwt_required()
def delete_group(group_id):
    user = current_user()
    err = require_gold(user)
    if err:
        return err
    group = Group.query.filter_by(id=group_id, user_id=user.id).first_or_404()
    db.session.delete(group)
    db.session.commit()
    return jsonify({"message": "Group deleted"}), 200


@groups_bp.route("/<int:group_id>/contacts", methods=["POST"])
@jwt_required()
def add_contact_to_group(group_id):
    user = current_user()
    err = require_gold(user)
    if err:
        return err

    group = Group.query.filter_by(id=group_id, user_id=user.id).first_or_404()
    data = request.get_json()
    if not data.get("contact_id"):
        return jsonify({"error": "contact_id is required"}), 400

    contact = Contact.query.filter_by(id=data["contact_id"], user_id=user.id).first()
    if not contact:
        return jsonify({"error": "Contact not found"}), 404

    if contact in group.contacts:
        return jsonify({"error": "Contact already in group"}), 409

    group.contacts.append(contact)
    db.session.commit()
    return jsonify({"message": "Contact added to group"}), 200


@groups_bp.route("/<int:group_id>/contacts/<int:contact_id>", methods=["DELETE"])
@jwt_required()
def remove_contact_from_group(group_id, contact_id):
    user = current_user()
    err = require_gold(user)
    if err:
        return err

    group = Group.query.filter_by(id=group_id, user_id=user.id).first_or_404()
    contact = Contact.query.filter_by(id=contact_id, user_id=user.id).first_or_404()

    if contact not in group.contacts:
        return jsonify({"error": "Contact not in group"}), 404

    group.contacts.remove(contact)
    db.session.commit()
    return jsonify({"message": "Contact removed from group"}), 200


@groups_bp.route("/<int:group_id>/emails", methods=["POST"])
@jwt_required()
def send_group_email(group_id):
    user = current_user()
    err = require_gold(user)
    if err:
        return err

    group = Group.query.filter_by(id=group_id, user_id=user.id).first_or_404()
    data = request.get_json()

    if not data.get("subject") or not data.get("body"):
        return jsonify({"error": "subject and body are required"}), 400

    if not group.contacts:
        return jsonify({"error": "Group has no contacts"}), 400

    group_email = GroupEmail(
        user_id=user.id,
        group_id=group.id,
        subject=data["subject"].strip(),
        body=data["body"].strip(),
    )
    db.session.add(group_email)
    db.session.flush()

    for contact in group.contacts:
        status = deliver_email(contact.name, contact.email, data["subject"].strip(), data["body"].strip())
        recipient = GroupEmailRecipient(
            group_email_id=group_email.id,
            contact_id=contact.id,
            status=status,
        )
        db.session.add(recipient)

    db.session.commit()
    return jsonify({"message": "Group email sent", "group_email": group_email.to_dict(include_status=True)}), 201


@groups_bp.route("/<int:group_id>/emails", methods=["GET"])
@jwt_required()
def list_group_emails(group_id):
    user = current_user()
    err = require_gold(user)
    if err:
        return err

    group = Group.query.filter_by(id=group_id, user_id=user.id).first_or_404()
    return jsonify({"group_emails": [ge.to_dict(include_status=True) for ge in group.group_emails]}), 200


@groups_bp.route("/<int:group_id>/emails/<int:email_id>/status", methods=["GET"])
@jwt_required()
def group_email_status(group_id, email_id):
    user = current_user()
    err = require_gold(user)
    if err:
        return err

    group_email = GroupEmail.query.filter_by(id=email_id, group_id=group_id, user_id=user.id).first_or_404()
    return jsonify({"status": group_email.to_dict(include_status=True)["status"]}), 200
