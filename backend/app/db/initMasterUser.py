"""
Database initialization functions.

This module contains functions for initializing default data in the database,
such as master users for development and testing.
"""

import os
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from app.db.session import SessionLocal
from app.db.models.userModel import UserModel


def init_master_user():
    """
    Initialize a default master user for development/testing if one doesn't exist.
    Uses environment variables for credentials with sensible defaults.
    
    Environment variables:
        MASTER_USER_EMAIL: Email for the master user (default: admin@example.com)
        MASTER_USER_PASSWORD: Password for the master user (default: admin123)
        MASTER_USER_NAME: Full name for the master user (default: Master Admin)
    """

    master_email =  "admin@example.com"
    master_password =  "admin123"
    master_name ="Master Admin"
    
    db: Session = SessionLocal()
    try:
        # Check if master user already exists
        existing_user = db.query(UserModel).filter(
            UserModel.user_email == master_email
        ).first()
        
        if existing_user:
            print(f"✅ Master user already exists: {master_email}")
            return
        
        # Create master user
        hashed_password = generate_password_hash(master_password)
        master_user = UserModel(
            user_full_name=master_name,
            user_email=master_email,
            user_status="ACTIVE",
            hashed_password=hashed_password,
            is_manager=True,  # Master user has manager privileges
        )
        
        db.add(master_user)
        db.commit()
        db.refresh(master_user)
        
        print(f"✅ Master user created successfully!")
        print(f"   Email: {master_email}")
        print(f"   Password: {master_password}")
        print(f"   Name: {master_name}")
        print(f"   ⚠️  Remember to change the password in production!")
        
    except Exception as e:
        db.rollback()
        print(f"⚠️  Warning: Could not create master user: {str(e)}")
    finally:
        db.close()

