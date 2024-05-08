import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


# Create SQLAlchemy instance
db = SQLAlchemy()

class Products(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(1000), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    
    transactions = db.relationship('Transaction', backref='product', lazy=True)
    vendor = db.relationship('Vendor', back_populates='products', lazy=True)
    
    def __repr__(self):
        return f"Product('{self.id}', '{self.name}', '{self.price}', '{self.stock}', '{self.image}')"

    def add_stock(self, amount):
        self.stock += amount
        
    def subtract_stock(self, amount):
        self.stock -= amount
        
class Vendor(db.Model):
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0)
    
    products = db.relationship('Products', back_populates='vendor', lazy=True)
    
    def __repr__(self):
        return f"Vendor('{self.id}', '{self.name}')"
    
    def add_product(self, name, price, description, stock, image):
        product = Products(name=name, price=price, description=description, stock=stock, image=image, vendor_id=self.id)
        db.session.add(product)
        db.session.commit()
        
    def remove_product(self, product_id):
        product = Products.query.get(product_id)
        if product is None:
            raise ValueError("Product does not exist")
        
        db.session.delete(product)
        db.session.commit()
        
    def update_product(self, product_id, name, price, description, stock, image):
        product = Products.query.get(product_id)
        if product is None:
            raise ValueError("Product does not exist")
        
        product.name = name
        product.price = price
        product.description = description
        product.stock = stock
        product.image = image
        db.session.commit()
        
    def get_products(self):
        return Products.query.filter_by(vendor_id=self.id).all()
    
    def get_product(self, product_id):
        return Products.query.get(product_id)
    
    def get_transactions(self):
        return Transaction.query.filter_by(vendor_id=self.id).all()
    
    def get_transaction(self, transaction_id):
        return Transaction.query.get(transaction_id)
    
    def get_balance(self):
        return sum([transaction.amount for transaction in Transaction.query.filter_by(vendor_id=self.id).all()])
    
    def refund(self, amount, user_id):
        self.balance -= amount
        user = User.query.get(user_id)
        user.refund(amount)
        db.session.commit()
        
    def add_balance(self, amount):
        self.balance += amount
        db.session.commit()
        
    def subtract_balance(self, amount):
        self.balance -= amount
        db.session.commit()
    

# Create a transaction table
class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    '''
    id: The unique identifier of the transaction.
    product_id: The ID of the product involved in the transaction.
    amount: The amount of the transaction.
    user_id: The ID of the user involved in the transaction.
    vendor_id: The ID of the vendor involved in the transaction.
    date: The date and time of the transaction.
    '''
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vendor_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f"Transaction('{self.id}', '{self.amount}', '{self.user_id}', '{self.date}')"


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    '''
    id: The unique identifier of the user.
    username: The username of the user.
    email: The email address of the user.
    password_hash: The hashed password of the user.
    is_active: A boolean flag indicating if the user is active.
    balance: The balance of the user.
    is_admin: A boolean flag indicating if the user is an admin.
    '''
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    balance = db.Column(db.Float, default=180)
    is_admin = db.Column(db.Boolean, default=False)
    
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    reviews = db.relationship('Reviews', backref='user', lazy=True)
    
    # if username is admin, then is_admin is True
    def __init__(self, username, email):
        self.username = username
        self.email = email
        if username == 'admin':
            self.is_admin = True
    
    def make_transaction(self, product_id, transaction_amount):
        product = Products.query.get(product_id)
        if product is None:
            raise ValueError("Product does not exist")

        if self.balance < transaction_amount:
            raise ValueError("Insufficient funds")

        try:
            transaction = Transaction(
                user_id=self.id,
                product_id=product_id,
                amount=transaction_amount,
                date=datetime.now()
            )
            self.balance -= transaction_amount  # Subtract amount from user's balance
            db.session.add(transaction)
            db.session.commit()
        except Exception as e:
            db.session.rollback()  # Rollback the transaction in case of any error
            raise e
    
    def make_admin(self, password):
        if password == 'admin':
            self.is_admin = True
            db.session.commit()
    
    def make_review(self, review, hoe_id):
        review = Reviews(user_name=self.username, review=review, hoe_id=hoe_id)
        db.session.add(review)
        db.session.commit()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def subtract_balance(self, amount):
        self.balance -= amount
        
    def refund(self, amount):
        self.balance += amount
        
    def add_balance(self, amount):
        self.balance += amount
        
    def __repr__(self):
        return '<User {}>'.format(self.username)

    @classmethod    
    def get(cls, user_id):
        return cls.query.get(user_id)

    # Implementation of properties and methods required by Flask-Login
    @property
    def is_authenticated(self):
        return True  # Assume all users are authenticated

    @property
    def is_active(self):
        return self.is_active  # Adjust based on your application's logic

    @property
    def is_anonymous(self):
        return False  # Real users are not anonymous

    def get_id(self):
        return str(self.id)  # Convert user ID to str for Flask-Login
    
class Admin(User):
        def __init__(self, username, email):
            super().__init__(username, email)
            self.is_admin = True
        
        def add_product(self, name, price, description, stock, image, vendor_id):
            product = Products(name=name, price=price, description=description, stock=stock, image=image, vendor_id=vendor_id)
            db.session.add(product)
            db.session.commit()
            
        def remove_product(self, product_id):
            product = Products.query.get(product_id)
            if product is None:
                raise ValueError("Product does not exist")
            
            db.session.delete(product)
            db.session.commit()
            
        def update_product(self, product_id, name, price, description, stock, image):
            product = Products.query.get(product_id)
            if product is None:
                raise ValueError("Product does not exist")
            
            product.name = name
            product.price = price
            product.description = description
            product.stock = stock
            product.image = image
            db.session.commit()
            
        def get_products(self):
            return Products.query.all()
        
        def get_product(self, product_id):
            return Products.query.get(product_id)
        
        def get_transactions(self):
            return Transaction.query.all()
        
        def get_transaction(self, transaction_id):
            return Transaction.query.get(transaction_id)
        
        def get_balance(self):
            return sum([transaction.amount for transaction in Transaction.query.all()])
        
        def refund(self, amount, user_id):
            user = User.query.get(user_id)
            user.refund(amount)
            db.session.commit()
            
        def add_balance(self, amount):
            db.session.commit()
            
        def subtract_balance(self, amount):
            db.session.commit()
    
class Reviews(db.Model):
    __tablename__ = 'reviews'
    
    '''
    id: The unique identifier of the review.
    user_id: The ID of the user who made the review.
    hoe_id: The ID of the hoe being reviewed.
    review: The review text.
    '''
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hoe_id = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(1000), nullable=False)
    
    def __repr__(self):
        return f"Review('{self.id}', '{self.user_id}', '{self.review}')"
    