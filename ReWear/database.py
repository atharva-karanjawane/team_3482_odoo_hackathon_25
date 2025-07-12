from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, CheckConstraint, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import pytz


load_dotenv()

IST = pytz.timezone('Asia/Kolkata')

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")


DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"

    uid = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    loc_lat = Column(Float)
    loc_long = Column(Float)
    points = Column(Integer, default=100)
    forgot_pass_code = Column(String(64))
    profile_img_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    products = relationship("Product", back_populates="user")
    transactions_as_requester = relationship("Transaction", foreign_keys="Transaction.requester_uid", back_populates="requester")
    transactions_as_receiver = relationship("Transaction", foreign_keys="Transaction.receiver_uid", back_populates="receiver")
    point_transactions = relationship("PointTransaction", back_populates="user")
    feedback_given = relationship("Feedback", foreign_keys="Feedback.reviewer_uid", back_populates="reviewer")
    feedback_received = relationship("Feedback", foreign_keys="Feedback.reviewee_uid", back_populates="reviewee")
    notifications = relationship("Notification", back_populates="user")

class Product(Base):
    __tablename__ = "products"

    pid = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(50), nullable=False)
    size = Column(String(20), nullable=False)
    condition = Column(String(50), nullable=False)
    point_value = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    is_featured = Column(Boolean, default=False)
    featured_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    transactions_as_requester = relationship("Transaction", foreign_keys="Transaction.requester_pid", back_populates="requester_product")
    transactions_as_receiver = relationship("Transaction", foreign_keys="Transaction.receiver_pid", back_populates="receiver_product")

    # Check constraints
    __table_args__ = (
        CheckConstraint("category IN ('Tops', 'Bottoms', 'Dresses', 'Outerwear')"),
        CheckConstraint("status IN ('pending', 'available', 'reserved', 'swapped', 'redeemed')"),
    )

class ProductImage(Base):
    __tablename__ = "product_images"

    image_id = Column(Integer, primary_key=True, index=True)
    pid = Column(Integer, ForeignKey("products.pid", ondelete="CASCADE"), nullable=False)
    image_url = Column(Text, nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    product = relationship("Product", back_populates="images")

class Transaction(Base):
    __tablename__ = "transactions"

    tid = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String(20), nullable=False)
    requester_uid = Column(Integer, ForeignKey("users.uid", ondelete="SET NULL"))
    receiver_uid = Column(Integer, ForeignKey("users.uid", ondelete="SET NULL"))
    requester_pid = Column(Integer, ForeignKey("products.pid", ondelete="SET NULL"))
    receiver_pid = Column(Integer, ForeignKey("products.pid", ondelete="SET NULL"))
    points_exchanged = Column(Integer, default=0)
    status = Column(String(20), default="requested")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    requester = relationship("User", foreign_keys=[requester_uid], back_populates="transactions_as_requester")
    receiver = relationship("User", foreign_keys=[receiver_uid], back_populates="transactions_as_receiver")
    requester_product = relationship("Product", foreign_keys=[requester_pid], back_populates="transactions_as_requester")
    receiver_product = relationship("Product", foreign_keys=[receiver_pid], back_populates="transactions_as_receiver")
    feedback = relationship("Feedback", back_populates="transaction", cascade="all, delete-orphan")

    # Check constraints
    __table_args__ = (
        CheckConstraint("transaction_type IN ('swap', 'redemption')"),
        CheckConstraint("status IN ('requested', 'accepted', 'rejected', 'completed', 'cancelled')"),
    )

class PointTransaction(Base):
    __tablename__ = "point_transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False)
    amount = Column(Integer, nullable=False)
    transaction_type = Column(String(50), nullable=False)
    reference_id = Column(Integer)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="point_transactions")

class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.tid", ondelete="CASCADE"), nullable=False)
    reviewer_uid = Column(Integer, ForeignKey("users.uid", ondelete="SET NULL"))
    reviewee_uid = Column(Integer, ForeignKey("users.uid", ondelete="SET NULL"))
    rating = Column(Integer, CheckConstraint("rating BETWEEN 1 AND 5"), nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    transaction = relationship("Transaction", back_populates="feedback")
    reviewer = relationship("User", foreign_keys=[reviewer_uid], back_populates="feedback_given")
    reviewee = relationship("User", foreign_keys=[reviewee_uid], back_populates="feedback_received")

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    notification_type = Column(String(50), nullable=False)
    reference_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="notifications")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)

def create_user(name: str, email: str, password: str):
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return None
        new_user = User(name=name, email=email, password=password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        add_points(new_user.uid, 50, "first_login", description="First-time login bonus")
        
        return new_user.uid
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        return None
    finally:
        db.close()

def get_user_by_email(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return {
                'uid': user.uid,
                'name': user.name,
                'email': user.email,
                'password': user.password,
                'role': user.role,
                'points': user.points
            }
        return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None
    finally:
        db.close()

def get_user_by_id(uid: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.uid == uid).first()
        if user:
            return {
                'uid': user.uid,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'points': user.points,
                'profile_img_url': user.profile_img_url
            }
        return None
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None
    finally:
        db.close()

def update_user_login(uid: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.uid == uid).first()
        if user:
            user.last_login = datetime.utcnow()
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error updating user login: {e}")
        return False
    finally:
        db.close()

# Product operations
def create_product(uid: int, product_data: dict):
    db = SessionLocal()
    try:
        # Calculate point value based on category, subcategory, and condition
        point_value = calculate_points(
            product_data['category'], 
            product_data['subcategory'], 
            product_data['condition']
        )
        
        # Create new product
        new_product = Product(
            uid=uid,
            title=product_data['title'],
            description=product_data['description'],
            category=product_data['category'],
            subcategory=product_data['subcategory'],
            size=product_data['size'],
            condition=product_data['condition'],
            point_value=point_value,
            status="pending"  # Admin needs to approve
        )
        
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        # Add points for listing an item
        add_points(uid, 10, "item_listing", new_product.pid, "Points for listing an item")
        
        return new_product.pid
    except Exception as e:
        db.rollback()
        print(f"Error creating product: {e}")
        return None
    finally:
        db.close()

def add_product_image(pid: int, image_url: str, is_primary: bool = False):
    db = SessionLocal()
    try:
        new_image = ProductImage(
            pid=pid,
            image_url=image_url,
            is_primary=is_primary
        )
        
        db.add(new_image)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error adding product image: {e}")
        return False
    finally:
        db.close()

def approve_product(pid: int, admin_uid: int):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.pid == pid).first()
        if not product:
            return False
            
        # Update product status
        product.status = "available"
        db.commit()
        
        # Add points for approved item
        add_points(
            product.uid, 
            product.point_value, 
            "item_approved", 
            product.pid, 
            f"Points for approved item: {product.title}"
        )
        
        # Create notification
        create_notification(
            product.uid,
            f"Your item '{product.title}' has been approved!",
            "product_approved",
            product.pid
        )
        
        return True
    except Exception as e:
        db.rollback()
        print(f"Error approving product: {e}")
        return False
    finally:
        db.close()

def get_product(pid: int):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.pid == pid).first()
        if not product:
            return None
            
        # Get product images
        images = db.query(ProductImage).filter(ProductImage.pid == pid).all()
        image_urls = [{"image_id": img.image_id, "url": img.image_url, "is_primary": img.is_primary} for img in images]
        
        return {
            "pid": product.pid,
            "uid": product.uid,
            "title": product.title,
            "description": product.description,
            "category": product.category,
            "subcategory": product.subcategory,
            "size": product.size,
            "condition": product.condition,
            "point_value": product.point_value,
            "status": product.status,
            "is_featured": product.is_featured,
            "created_at": product.created_at,
            "images": image_urls
        }
    except Exception as e:
        print(f"Error getting product: {e}")
        return None
    finally:
        db.close()

def get_available_products(limit: int = 20, offset: int = 0, category: str = None):
    db = SessionLocal()
    try:
        query = db.query(Product).filter(Product.status == "available")
        
        # Apply category filter if provided
        if category:
            query = query.filter(Product.category == category)
        
        # Order by featured first, then creation date
        query = query.order_by(Product.is_featured.desc(), Product.created_at.desc())
        
        # Apply pagination
        products = query.limit(limit).offset(offset).all()
        
        result = []
        for product in products:
            # Get primary image
            primary_image = db.query(ProductImage).filter(
                ProductImage.pid == product.pid,
                ProductImage.is_primary == True
            ).first()
            
            image_url = primary_image.image_url if primary_image else None
            
            result.append({
                "pid": product.pid,
                "title": product.title,
                "category": product.category,
                "subcategory": product.subcategory,
                "point_value": product.point_value,
                "condition": product.condition,
                "is_featured": product.is_featured,
                "image_url": image_url
            })
        
        return result
    except Exception as e:
        print(f"Error getting available products: {e}")
        return []
    finally:
        db.close()

def get_user_products(uid: int):
    db = SessionLocal()
    try:
        products = db.query(Product).filter(Product.uid == uid).all()
        
        result = []
        for product in products:
            # Get primary image
            primary_image = db.query(ProductImage).filter(
                ProductImage.pid == product.pid,
                ProductImage.is_primary == True
            ).first()
            
            image_url = primary_image.image_url if primary_image else None
            
            result.append({
                "pid": product.pid,
                "title": product.title,
                "category": product.category,
                "subcategory": product.subcategory,
                "point_value": product.point_value,
                "status": product.status,
                "condition": product.condition,
                "image_url": image_url
            })
        
        return result
    except Exception as e:
        print(f"Error getting user products: {e}")
        return []
    finally:
        db.close()

# Transaction operations
def create_swap_request(requester_uid: int, receiver_pid: int, requester_pid: int):
    db = SessionLocal()
    try:
        # Get the products
        requester_product = db.query(Product).filter(Product.pid == requester_pid).first()
        receiver_product = db.query(Product).filter(Product.pid == receiver_pid).first()
        
        if not requester_product or not receiver_product:
            return None
            
        # Check if products are available
        if requester_product.status != "available" or receiver_product.status != "available":
            return None
            
        # Check if requester has enough points for swap fee
        requester = db.query(User).filter(User.uid == requester_uid).first()
        if requester.points < 5:  # Swap fee is 5 points
            return None
            
        # Create transaction
        new_transaction = Transaction(
            transaction_type="swap",
            requester_uid=requester_uid,
            receiver_uid=receiver_product.uid,
            requester_pid=requester_pid,
            receiver_pid=receiver_pid,
            points_exchanged=5,  # Swap fee
            status="requested"
        )
        
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
        
        # Deduct points for swap fee
        add_points(
            requester_uid, 
            -5, 
            "swap_fee", 
            new_transaction.tid, 
            "Swap request fee"
        )
        
        # Update product status
        requester_product.status = "reserved"
        db.commit()
        
        # Create notification for receiver
        create_notification(
            receiver_product.uid,
            f"You have a new swap request for your item '{receiver_product.title}'",
            "swap_request",
            new_transaction.tid
        )
        
        return new_transaction.tid
    except Exception as e:
        db.rollback()
        print(f"Error creating swap request: {e}")
        return None
    finally:
        db.close()

def create_redemption_request(requester_uid: int, product_pid: int):
    db = SessionLocal()
    try:
        # Get the product
        product = db.query(Product).filter(Product.pid == product_pid).first()
        
        if not product or product.status != "available":
            return None
            
        # Calculate redemption cost (1.5x product value)
        redemption_cost = int(product.point_value * 1.5)
        
        # Check if requester has enough points
        requester = db.query(User).filter(User.uid == requester_uid).first()
        if requester.points < redemption_cost:
            return None
            
        # Create transaction
        new_transaction = Transaction(
            transaction_type="redemption",
            requester_uid=requester_uid,
            receiver_uid=product.uid,
            requester_pid=None,
            receiver_pid=product_pid,
            points_exchanged=redemption_cost,
            status="requested"
        )
        
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
        
        # Deduct points for redemption
        add_points(
            requester_uid, 
            -redemption_cost, 
            "redeem_item", 
            new_transaction.tid, 
            f"Redemption of item: {product.title}"
        )
        
        # Update product status
        product.status = "reserved"
        db.commit()
        
        # Create notification for receiver
        create_notification(
            product.uid,
            f"Someone wants to redeem your item '{product.title}' with points",
            "redemption_request",
            new_transaction.tid
        )
        
        return new_transaction.tid
    except Exception as e:
        db.rollback()
        print(f"Error creating redemption request: {e}")
        return None
    finally:
        db.close()

def accept_transaction(tid: int):
    db = SessionLocal()
    try:
        transaction = db.query(Transaction).filter(Transaction.tid == tid).first()
        
        if not transaction or transaction.status != "requested":
            return False
            
        # Update transaction status
        transaction.status = "accepted"
        transaction.updated_at = datetime.utcnow()
        db.commit()
        
        # Create notification for requester
        create_notification(
            transaction.requester_uid,
            f"Your transaction request has been accepted!",
            "transaction_accepted",
            transaction.tid
        )
        
        return True
    except Exception as e:
        db.rollback()
        print(f"Error accepting transaction: {e}")
        return False
    finally:
        db.close()

def complete_transaction(tid: int):
    db = SessionLocal()
    try:
        transaction = db.query(Transaction).filter(Transaction.tid == tid).first()
        
        if not transaction or transaction.status != "accepted":
            return False
            
        # Update transaction status
        transaction.status = "completed"
        transaction.completed_at = datetime.utcnow()
        db.commit()
        
        # Handle based on transaction type
        if transaction.transaction_type == "swap":
            # Get the products
            requester_product = db.query(Product).filter(Product.pid == transaction.requester_pid).first()
            receiver_product = db.query(Product).filter(Product.pid == transaction.receiver_pid).first()
            
            # Update product status and ownership
            requester_product.status = "swapped"
            requester_product.uid = transaction.receiver_uid
            
            receiver_product.status = "swapped"
            receiver_product.uid = transaction.requester_uid
            
            db.commit()
            
            # Award points for successful swap to seller
            add_points(
                transaction.receiver_uid, 
                20, 
                "successful_swap", 
                transaction.tid, 
                "Bonus for completing a swap"
            )
            
        elif transaction.transaction_type == "redemption":
            # Get the product
            product = db.query(Product).filter(Product.pid == transaction.receiver_pid).first()
            
            # Update product status and ownership
            product.status = "redeemed"
            product.uid = transaction.requester_uid
            
            db.commit()
            
            # Award points to seller (original product value)
            add_points(
                transaction.receiver_uid, 
                product.point_value, 
                "item_redeemed", 
                transaction.tid, 
                f"Points for redeemed item: {product.title}"
            )
        
        # Create notifications
        create_notification(
            transaction.requester_uid,
            "Your transaction has been completed successfully!",
            "transaction_completed",
            transaction.tid
        )
        
        create_notification(
            transaction.receiver_uid,
            "Your transaction has been completed successfully!",
            "transaction_completed",
            transaction.tid
        )
        
        return True
    except Exception as e:
        db.rollback()
        print(f"Error completing transaction: {e}")
        return False
    finally:
        db.close()

def reject_transaction(tid: int):
    db = SessionLocal()
    try:
        transaction = db.query(Transaction).filter(Transaction.tid == tid).first()
        
        if not transaction or transaction.status != "requested":
            return False
            
        # Update transaction status
        transaction.status = "rejected"
        transaction.updated_at = datetime.utcnow()
        db.commit()
        
        # Refund points if it's a redemption
        if transaction.transaction_type == "redemption":
            # Refund the redemption cost
            product = db.query(Product).filter(Product.pid == transaction.receiver_pid).first()
            redemption_cost = int(product.point_value * 1.5)
            
            add_points(
                transaction.requester_uid, 
                redemption_cost, 
                "redemption_refund", 
                transaction.tid, 
                "Refund for rejected redemption"
            )
        else:
            # Refund the swap fee
            add_points(
                transaction.requester_uid, 
                5, 
                "swap_fee_refund", 
                transaction.tid, 
                "Refund for rejected swap request"
            )
        
        # Update product status back to available
        if transaction.transaction_type == "swap":
            requester_product = db.query(Product).filter(Product.pid == transaction.requester_pid).first()
            requester_product.status = "available"
        
        receiver_product = db.query(Product).filter(Product.pid == transaction.receiver_pid).first()
        receiver_product.status = "available"
        
        db.commit()
        
        # Create notification
        create_notification(
            transaction.requester_uid,
            "Your transaction request has been rejected.",
            "transaction_rejected",
            transaction.tid
        )
        
        return True
    except Exception as e:
        db.rollback()
        print(f"Error rejecting transaction: {e}")
        return False
    finally:
        db.close()

def get_user_transactions(uid: int):
    db = SessionLocal()
    try:
        # Get transactions where user is either requester or receiver
        transactions = db.query(Transaction).filter(
            (Transaction.requester_uid == uid) | (Transaction.receiver_uid == uid)
        ).order_by(Transaction.created_at.desc()).all()
        
        result = []
        for transaction in transactions:
            # Get product details
            requester_product = None
            receiver_product = None
            
            if transaction.requester_pid:
                requester_product = db.query(Product).filter(Product.pid == transaction.requester_pid).first()
            
            if transaction.receiver_pid:
                receiver_product = db.query(Product).filter(Product.pid == transaction.receiver_pid).first()
            
            # Determine if user is requester or receiver
            is_requester = (transaction.requester_uid == uid)
            
            result.append({
                "tid": transaction.tid,
                "transaction_type": transaction.transaction_type,
                "status": transaction.status,
                "created_at": transaction.created_at,
                "completed_at": transaction.completed_at,
                "points_exchanged": transaction.points_exchanged,
                "is_requester": is_requester,
                "other_user_id": transaction.receiver_uid if is_requester else transaction.requester_uid,
                "requester_product": {
                    "pid": requester_product.pid,
                    "title": requester_product.title,
                    "image_url": get_product_primary_image(requester_product.pid)
                } if requester_product else None,
                "receiver_product": {
                    "pid": receiver_product.pid,
                    "title": receiver_product.title,
                    "image_url": get_product_primary_image(receiver_product.pid)
                } if receiver_product else None
            })
        
        return result
    except Exception as e:
        print(f"Error getting user transactions: {e}")
        return []
    finally:
        db.close()

# Points system operations
def add_points(uid: int, amount: int, transaction_type: str, reference_id: int = None, description: str = None):
    db = SessionLocal()
    try:
        # Get current points
        user = db.query(User).filter(User.uid == uid).first()
        
        if not user:
            return False
            
        # Update user points
        user.points += amount
        
        # Record point transaction
        new_transaction = PointTransaction(
            uid=uid,
            amount=amount,
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description
        )
        
        db.add(new_transaction)
        db.commit()
        
        return True
    except Exception as e:
        db.rollback()
        print(f"Error adding points: {e}")
        return False
    finally:
        db.close()

def get_point_transactions(uid: int, limit: int = 20, offset: int = 0):
    db = SessionLocal()
    try:
        transactions = db.query(PointTransaction).filter(
            PointTransaction.uid == uid
        ).order_by(PointTransaction.created_at.desc()).limit(limit).offset(offset).all()
        
        result = []
        for transaction in transactions:
            result.append({
                "transaction_id": transaction.transaction_id,
                "amount": transaction.amount,
                "transaction_type": transaction.transaction_type,
                "description": transaction.description,
                "created_at": transaction.created_at
            })
        
        return result
    except Exception as e:
        print(f"Error getting point transactions: {e}")
        return []
    finally:
        db.close()

# Feedback operations
def create_feedback(transaction_id: int, reviewer_uid: int, reviewee_uid: int, rating: int, comment: str = None):
    db = SessionLocal()
    try:
        # Check if feedback already exists
        existing_feedback = db.query(Feedback).filter(
            Feedback.transaction_id == transaction_id,
            Feedback.reviewer_uid == reviewer_uid
        ).first()
        
        if existing_feedback:
            return False
            
        # Create new feedback
        new_feedback = Feedback(
            transaction_id=transaction_id,
            reviewer_uid=reviewer_uid,
            reviewee_uid=reviewee_uid,
            rating=rating,
            comment=comment
        )
        
        db.add(new_feedback)
        db.commit()
        
        # Award points for positive feedback
        if rating >= 4:
            add_points(
                reviewee_uid, 
                5, 
                "positive_feedback", 
                transaction_id, 
                "Points for positive feedback"
            )
        
        return True
    except Exception as e:
        db.rollback()
        print(f"Error creating feedback: {e}")
        return False
    finally:
        db.close()

def get_user_rating(uid: int):
    db = SessionLocal()
    try:
        # Get all feedback for this user
        feedback = db.query(Feedback).filter(Feedback.reviewee_uid == uid).all()
        
        if not feedback:
            return None
            
        # Calculate average rating
        total_rating = sum(f.rating for f in feedback)
        avg_rating = total_rating / len(feedback)
        
        return {
            "average_rating": round(avg_rating, 1),
            "total_reviews": len(feedback)
        }
    except Exception as e:
        print(f"Error getting user rating: {e}")
        return None
    finally:
        db.close()

# Notification operations
def create_notification(uid: int, message: str, notification_type: str, reference_id: int = None):
    db = SessionLocal()
    try:
        new_notification = Notification(
            uid=uid,
            message=message,
            notification_type=notification_type,
            reference_id=reference_id
        )
        
        db.add(new_notification)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error creating notification: {e}")
        return False
    finally:
        db.close()

def get_user_notifications(uid: int, limit: int = 20, offset: int = 0):
    db = SessionLocal()
    try:
        notifications = db.query(Notification).filter(
            Notification.uid == uid
        ).order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()
        
        result = []
        for notification in notifications:
            result.append({
                "notification_id": notification.notification_id,
                "message": notification.message,
                "is_read": notification.is_read,
                "notification_type": notification.notification_type,
                "reference_id": notification.reference_id,
                "created_at": notification.created_at
            })
        
        return result
    except Exception as e:
        print(f"Error getting user notifications: {e}")
        return []
    finally:
        db.close()

def mark_notification_read(notification_id: int):
    db = SessionLocal()
    try:
        notification = db.query(Notification).filter(Notification.notification_id == notification_id).first()
        
        if not notification:
            return False
            
        notification.is_read = True
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error marking notification as read: {e}")
        return False
    finally:
        db.close()

# Utility functions
def calculate_points(category: str, subcategory: str, condition: str):
    """Calculate point value for an item based on its category, subcategory, and condition"""
    # Base points by category
    base_points = {
        'Tops': 30,
        'Bottoms': 35,
        'Dresses': 45,
        'Outerwear': 50
    }
    
    # Subcategory modifiers
    subcategory_modifiers = {
        'Tops': {'Casual': -5, 'Formal': 10, 'Athletic': 0},
        'Bottoms': {'Casual': -5, 'Formal': 10, 'Athletic': 0},
        'Dresses': {'Casual': -10, 'Formal': 15, 'Evening': 25},
        'Outerwear': {'Light': -10, 'Heavy': 10, 'Formal': 5}
    }
    
    # Condition multipliers
    condition_multipliers = {
        'New with tags': 1.5,
        'Like New': 1.25,
        'Good': 1.0,
        'Fair': 0.75
    }
    
    # Calculate points
    category_points = base_points.get(category, 30)
    modifier = subcategory_modifiers.get(category, {}).get(subcategory, 0)
    multiplier = condition_multipliers.get(condition, 1.0)
    
    total_points = int((category_points + modifier) * multiplier)
    
    # Ensure minimum points
    return max(10, total_points)

def get_product_primary_image(pid: int):
    db = SessionLocal()
    try:
        # Try to get primary image first
        primary_image = db.query(ProductImage).filter(
            ProductImage.pid == pid,
            ProductImage.is_primary == True
        ).first()
        
        # If no primary image, get any image
        if not primary_image:
            primary_image = db.query(ProductImage).filter(
                ProductImage.pid == pid
            ).first()
        
        return primary_image.image_url if primary_image else None
    except Exception as e:
        print(f"Error getting product primary image: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")