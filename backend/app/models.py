from datetime import datetime, timezone
from app import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email_address = db.Column(db.String(255), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="normal", nullable=False)
    is_superuser = db.Column(db.Boolean, default=False, nullable=False)
    plan = db.Column(db.String(20), default="free", nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    contacts = db.relationship("Contact", backref="owner", lazy=True, cascade="all, delete-orphan")
    emails = db.relationship("Email", backref="sender", lazy=True, cascade="all, delete-orphan")
    groups = db.relationship("Group", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self, include_emails=False):
        data = {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email_address": self.email_address,
            "phone_number": self.phone_number,
            "role": self.role,
            "is_superuser": self.is_superuser,
            "plan": self.plan,
            "created_at": self.created_at.isoformat(),
        }
        if include_emails:
            data["emails"] = [e.to_dict() for e in self.emails]
        return data


class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    emails = db.relationship("Email", backref="contact", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat(),
        }


class Email(db.Model):
    __tablename__ = "emails"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey("contacts.id"), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="sent", nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    sent_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "contact_id": self.contact_id,
            "contact": self.contact.to_dict() if self.contact else None,
            "subject": self.subject,
            "body": self.body,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }


group_contacts = db.Table(
    "group_contacts",
    db.Column("group_id", db.Integer, db.ForeignKey("groups.id"), primary_key=True),
    db.Column("contact_id", db.Integer, db.ForeignKey("contacts.id"), primary_key=True),
)


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    contacts = db.relationship("Contact", secondary=group_contacts, lazy=True)
    group_emails = db.relationship("GroupEmail", backref="group", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_contacts=False):
        data = {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "contact_count": len(self.contacts),
        }
        if include_contacts:
            data["contacts"] = [c.to_dict() for c in self.contacts]
        return data


class GroupEmail(db.Model):
    __tablename__ = "group_emails"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    recipients = db.relationship(
        "GroupEmailRecipient", backref="group_email", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self, include_status=False):
        data = {
            "id": self.id,
            "group_id": self.group_id,
            "subject": self.subject,
            "body": self.body,
            "created_at": self.created_at.isoformat(),
        }
        if include_status:
            sent = sum(1 for r in self.recipients if r.status == "sent")
            pending = sum(1 for r in self.recipients if r.status == "pending")
            failed = [
                {"contact_id": r.contact_id, "contact": r.contact.to_dict()}
                for r in self.recipients
                if r.status == "failed"
            ]
            data["status"] = {
                "total": len(self.recipients),
                "sent": sent,
                "pending": pending,
                "failed_count": len(failed),
                "failed_contacts": failed,
            }
        return data


class GroupEmailRecipient(db.Model):
    __tablename__ = "group_email_recipients"

    id = db.Column(db.Integer, primary_key=True)
    group_email_id = db.Column(db.Integer, db.ForeignKey("group_emails.id"), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey("contacts.id"), nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)

    contact = db.relationship("Contact", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "contact_id": self.contact_id,
            "contact": self.contact.to_dict() if self.contact else None,
            "status": self.status,
        }
