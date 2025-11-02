from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    ADMIN = "admin"
    INVESTIGATOR = "investigator"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.INVESTIGATOR)
    badge_number = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    credits = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    disclaimer_accepted = Column(Boolean, default=False)
    disclaimer_accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    cases = relationship("Case", back_populates="created_by_user", foreign_keys="Case.created_by")
    audit_logs = relationship("AuditLog", back_populates="user")
    reports = relationship("Report", back_populates="generated_by_user")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="open")  # open, in_progress, closed
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    created_by = Column(Integer, ForeignKey("users.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="cases")
    assigned_to_user = relationship("User", foreign_keys=[assigned_to])
    reports = relationship("Report", back_populates="case")
    whatsapp_profiles = relationship("WhatsAppProfile", back_populates="case")
    face_searches = relationship("FaceSearch", back_populates="case")
    social_profiles = relationship("SocialProfile", back_populates="case")
    monitored_keywords = relationship("MonitoredKeyword", back_populates="case")
    username_searches = relationship("UsernameSearch", back_populates="case")
    number_email_searches = relationship("NumberEmailSearch", back_populates="case")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    module = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    report_type = Column(String(50), nullable=False)  # whatsapp, facial, social, etc.
    title = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id"))
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="reports")
    generated_by_user = relationship("User", back_populates="reports")


class WhatsAppProfile(Base):
    __tablename__ = "whatsapp_profiles"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    phone_number = Column(String(20), nullable=False, index=True)
    display_name = Column(String(100), nullable=True)
    about = Column(Text, nullable=True)
    profile_picture_path = Column(String(500), nullable=True)
    last_seen = Column(String(50), nullable=True)
    is_available = Column(Boolean, default=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="whatsapp_profiles")


class FaceSearch(Base):
    __tablename__ = "face_searches"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    source_image_path = Column(String(500), nullable=False)
    search_type = Column(String(20), nullable=False)  # local, reverse
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="face_searches")
    matches = relationship("FaceMatch", back_populates="search")


class FaceMatch(Base):
    __tablename__ = "face_matches"

    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("face_searches.id"))
    matched_image_path = Column(String(500), nullable=True)
    source_url = Column(String(1000), nullable=True)
    confidence_score = Column(Float, nullable=False)
    name = Column(String(100), nullable=True)
    alias = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    search = relationship("FaceSearch", back_populates="matches")


class SocialProfile(Base):
    __tablename__ = "social_profiles"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    platform = Column(String(50), nullable=False)  # twitter, facebook, instagram
    username = Column(String(100), nullable=False, index=True)
    display_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    profile_picture_path = Column(String(500), nullable=True)
    profile_url = Column(String(500), nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(Text, nullable=True)  # JSON data

    # Relationships
    case = relationship("Case", back_populates="social_profiles")


class MonitoredKeyword(Base):
    __tablename__ = "monitored_keywords"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    keyword = Column(String(200), nullable=False, index=True)
    location = Column(String(200), nullable=True)
    platforms = Column(String(500), nullable=True)  # Comma-separated
    created_at = Column(DateTime, default=datetime.utcnow)
    last_monitored = Column(DateTime, nullable=True)

    # Relationships
    case = relationship("Case", back_populates="monitored_keywords")
    results = relationship("MonitoredPost", back_populates="keyword")


class MonitoredPost(Base):
    __tablename__ = "monitored_posts"

    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("monitored_keywords.id"))
    platform = Column(String(50), nullable=False)
    post_url = Column(String(1000), nullable=True)
    post_text = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    sentiment = Column(String(20), nullable=True)  # positive, neutral, negative
    sentiment_score = Column(Float, nullable=True)
    location = Column(String(200), nullable=True)
    posted_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    keyword = relationship("MonitoredKeyword", back_populates="results")


class UsernameSearch(Base):
    __tablename__ = "username_searches"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    username = Column(String(100), nullable=False, index=True)
    officer_name = Column(String(100), nullable=True)
    cache_key = Column(String(200), nullable=True, index=True)
    status = Column(String(20), default="pending")  # pending, in_progress, completed, failed
    platforms_checked = Column(Integer, default=0)
    platforms_found = Column(Integer, default=0)
    searched_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    case = relationship("Case", back_populates="username_searches")
    results = relationship("UsernameResult", back_populates="search")


class UsernameResult(Base):
    __tablename__ = "username_results"

    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("username_searches.id"))
    platform_name = Column(String(100), nullable=False)
    platform_url = Column(String(1000), nullable=True)
    username_found = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.0)
    discovered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    search = relationship("UsernameSearch", back_populates="results")


class NumberEmailSearch(Base):
    __tablename__ = "number_email_searches"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    search_type = Column(String(20), nullable=False)  # phone, email
    search_value = Column(String(200), nullable=False, index=True)
    searched_at = Column(DateTime, default=datetime.utcnow)
    credits_used = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, completed, failed
    modules_requested = Column(String(500), nullable=True)  # Comma-separated module names
    
    # Relationships
    case = relationship("Case", back_populates="number_email_searches")
    results = relationship("NumberEmailResult", back_populates="search")
    user = relationship("User")


class NumberEmailResult(Base):
    __tablename__ = "number_email_results"

    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("number_email_searches.id"))
    module_name = Column(String(100), nullable=False)  # truename, social_media, upi, vehicle, aadhaar, deep_search, linked_emails, alternate_numbers, bank_details
    result_type = Column(String(50), nullable=False)  # name, upi, aadhaar, vehicle, etc.
    result_data = Column(Text, nullable=True)  # JSON data
    source = Column(String(100), nullable=True)  # Bot name (e.g., @YouLeakOsint_bot)
    confidence = Column(String(20), default="medium")  # low, medium, high
    retrieved_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    search = relationship("NumberEmailSearch", back_populates="results")


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    transaction_type = Column(String(20), nullable=False)  # debit, credit
    amount = Column(Integer, nullable=False)
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    module = Column(String(50), nullable=True)  # tracker, etc.
    reference_id = Column(Integer, nullable=True)  # Search ID
    description = Column(String(500), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who credited
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    admin_user = relationship("User", foreign_keys=[created_by])
