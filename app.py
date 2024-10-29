# transestion task work

from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean, CheckConstraint, Float
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import SQLAlchemyError


engine = create_engine('mysql://root:root@localhost/transactions_db', echo=True)

Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    contact = Column(String(100))
    address = Column(String(100))
    orders = relationship("Order", back_populates="customer")

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    order_details = relationship("OrderDetail", back_populates="product")

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    customer = relationship("Customer", back_populates="orders")
    order_details = relationship("OrderDetail", back_populates="order")

class OrderDetail(Base):
    __tablename__ = 'orderdetails'
    id = Column(Integer, primary_key=True)
    quantity = Column(Integer, nullable=False)  
    unit_price = Column(Integer, nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)

    order = relationship("Order", back_populates="order_details")
    product = relationship("Product", back_populates="order_details")


Base.metadata.create_all(engine)


# transection logic

def add_customer(name, contact, address):
    try:
        with session.begin():
            customer = Customer(name=name, contact=contact, address=address)
            session.add(customer)
            print(f"Customer {name} added successfully.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Failed to add customer: {e}")

def update_customer(customer_id, name=None, contact=None, address=None):
    try:
        with session.begin():
            customer = session.query(Customer).filter_by(id=customer_id).one()
            if name: customer.name = name
            if contact: customer.contact = contact
            if address: customer.address = address
            print(f"Customer {customer_id} updated successfully.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Failed to update customer: {e}")


def delete_customer(customer_id):
    try:
        with session.begin():
            # Find the customer
            customer = session.query(Customer).filter_by(id=customer_id).one_or_none()
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} does not exist.")
            
            # Delete related orders and order details
            for order in customer.orders:
                session.query(OrderDetail).filter_by(order_id=order.id).delete()
                session.delete(order)
            
            # Delete the customer
            session.delete(customer)
            session.commit()
            print(f"Customer with ID {customer_id} and related records deleted successfully.")

    except (SQLAlchemyError, ValueError) as e:
        session.rollback()
        print(f"Deletion failed: {e}")
        


def add_product(name, price, stock):
    try:
        with session.begin():
            product = Product(name=name, price=price, stock=stock)
            session.add(product)
            print(f"Product {name} added successfully.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Failed to add product: {e}")

def update_product_stock(product_id, quantity):
    try:
        with session.begin():
            product = session.query(Product).filter_by(id=product_id).one()
            product.stock += quantity
            print(f"Product {product_id} stock updated successfully.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Failed to update product stock: {e}")

def delete_product(product_id):
    try:
        with session.begin():
            product = session.query(Product).filter_by(id=product_id).one_or_none()
            if not product:
                raise ValueError(f"Product with ID {product_id} does not exist.")
            
            session.query(OrderDetail).filter_by(product_id=product_id).delete()
            
            session.delete(product)
            session.commit()
            print(f"Product with ID {product_id} and related records deleted successfully.")

    except (SQLAlchemyError, ValueError) as e:
        session.rollback()
        print(f"Deletion failed: {e}")

def create_order(customer_id, product_orders):
    try:
        with session.begin():
            order = Order(date=DateTime.now(), customer_id=customer_id)
            session.add(order)
            session.flush()  # Get order.id for use in order details

            for item in product_orders:
                product = session.query(Product).filter_by(id=item['product_id']).one()
                
                if product.stock < item['quantity']:
                    raise ValueError(f"Insufficient stock for product ID {item['product_id']}")
                
                order_detail = OrderDetail(
                    quantity=item['quantity'],
                    unit_price=product.price,
                    order_id=order.id,
                    product_id=product.id
                )
                session.add(order_detail)
                product.stock -= item['quantity']
            
            print("Order created successfully with all items processed.")
    except (SQLAlchemyError, ValueError) as e:
        session.rollback()
        print(f"Failed to create order: {e}")


def update_order_details(order_id, updated_items):
    try:
        with session.begin():
            order = session.query(Order).filter_by(id=order_id).one()
            for item in updated_items:
                order_detail = session.query(OrderDetail).filter_by(order_id=order.id, product_id=item['product_id']).one()
                
                product = session.query(Product).filter_by(id=item['product_id']).one()
                stock_change = item['quantity'] - order_detail.quantity
                
                if product.stock < stock_change:
                    raise ValueError(f"Insufficient stock for product ID {item['product_id']}")

                product.stock -= stock_change
                order_detail.quantity = item['quantity']
                order_detail.unit_price = product.price

            print(f"Order {order_id} updated successfully.")
    except (SQLAlchemyError, ValueError) as e:
        session.rollback()
        print(f"Failed update order: {e}")

def delete_order(order_id):
    try:
        with session.begin():
            order = session.query(Order).filter_by(id=order_id).one_or_none()
            if not order:
                raise ValueError(f"Order ID {order_id} does not exist.")
            
            session.query(OrderDetail).filter_by(order_id=order_id).delete()
            
            session.delete(order)
            session.commit()
            print(f"Order ID {order_id} deleted successfully.")

    except (SQLAlchemyError, ValueError) as e:
        session.rollback()
        print(f"Deletion failed: {e}")
        
        '''
        open terminal:
        cd "C:\Program Files\MySQL\MySQL Server 8.0\bin"
        mysql -u root -p
        Enter password: root
        USE transactions_db;
        SELECT * FROM products;
        UPDATE products SET stock = 50 WHERE id = 101; 
        SELECT * FROM products WHERE id = 101;
        SELECT * FROM products;

        UPDATE customers SET name = 'ihsan', address = 'street 49' WHERE id = 1; 
        SELECT * FROM customers WHERE id = 1;

        # deletion
        SELECT * FROM products;
        DELETE FROM products WHERE id = 104;
        SELECT * FROM products;
        # insertion
        INSERT INTO products (name, price, stock) VALUES ('qmobile', 300.99, 25);

        mysql> exit
        Bye

        '''