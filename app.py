from flask import Flask, render_template, request, redirect, url_for,flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, UserMixin, login_required, current_user
from datetime import datetime
import sqlalchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales.db'  # Using SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"]="welcome"
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app) 
login_manager.login_view='login'



@app.route("/")
def home():
    return render_template("h2.html")

class User(db.Model, UserMixin):
    tablename="users"
    id = db.Column(db.Integer, primary_key=True)
    companyName = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(100), default="user")

    def save_hash_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_hash_password(self,password):
        return check_password_hash(self.password_hash, password)

    


@app.route("/register", methods = ["GET","POST"])
def register():
    if request.method=="POST":
        companyName = request.form.get("companyName")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        if User.query.filter_by(email=email).first():
            flash("User Already Exists")
            return redirect(url_for("home"))

        user_data = User( companyName=companyName, email = email,role=role)
        user_data.save_hash_password(password)

        db.session.add(user_data)
        db.session.commit()
        flash("User Registered Successfully")
        return redirect(url_for("login"))
    
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user_data = User.query.filter_by(email=email).first()

        if user_data and user_data.check_hash_password(password):
            login_user(user_data)
           
            # Set the companyName in the session
            session['companyName'] = user_data.companyName  # Store the company name in the session
            return redirect(url_for("home"))
        
       
         
    return render_template("login.html")
# @app.route("/login", methods = ["GET", "POST"])
# def login():
#     if request.method=="POST":
#         email = request.form.get("email")
#         password = request.form.get("password")
#         role = request.form.get("role")

#         user_data = User.query.filter_by(email = email).first()

#         if user_data and user_data.check_hash_password(password):
#             login_user(user_data) 
#             flash("User Logged In Successfully")
#             return redirect(url_for("home"))
#         else:
#             flash("please check your credentials(email/password)")
#     return render_template("login.html")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User,int(user_id))  
@app.route("/logout")
def logout():
    logout_user()
    flash("User logged out successfully")
    return redirect(url_for("home"))



def role_required(role):  
    def decorator(func):  
        def wrap(*args, **kwargs):  
            if current_user.role!=role: 
                flash("Unauthorized Access")
                return redirect(url_for("login"))
            return func(*args, **kwargs)
        wrap.__name__ = func.__name__ 
        return wrap
    return decorator



@app.route("/aboutus")
def aboutus():
    return render_template("aboutus.html")

@app.route("/contactus")
def contact():
    return render_template("contactus.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/termscondition")
def termsAndCondition():
    return render_template("t&c.html")


# Customers Table
class Student(db.Model):
    __tablename__ = "usersTable"
    roll_no = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    company_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    work_phone = db.Column(db.Integer)
    receivables = db.Column(db.Integer)
    unused_credits = db.Column(db.Integer)

    def __init__(self, name, company_name, email, work_phone, receivables, unused_credits):
        self.name = name
        self.company_name = company_name
        self.email = email
        self.work_phone = work_phone
        self.receivables = receivables
        self.unused_credits = unused_credits

# Sales Orders Table
class SalesOrder(db.Model):
    __tablename__ = "sales_orders"
    id = db.Column(db.Integer, primary_key=True)
    sales_order_no = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('usersTable.roll_no'), nullable=False)
    reference_no = db.Column(db.String(50), nullable=True)
    order_status = db.Column(db.String(20), default='Draft')
    shipment_status = db.Column(db.String(20), default='Not Shipped')
    total_amount = db.Column(db.Float, nullable=False)
    amount_received = db.Column(db.Float, default=0.0)

    customer = db.relationship("Student", backref="sales_orders")

    @property
    def amount_due(self):
        return self.total_amount - self.amount_received

# Packages Table
class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(100), nullable=False)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    sales_order = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    carrier = db.Column(db.String(100), nullable=True)
    shipping_date = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default="Not Shipped")

def get_next_sales_order_no():
    last_order = SalesOrder.query.order_by(SalesOrder.id.desc()).first()
    if last_order:
        last_number = int(last_order.sales_order_no.split('-')[-1])
        return f"SO-{last_number + 1:02d}"
    return "SO-01"

# Home Page
@app.route('/sales_orders')
def index():
    sales_orders = SalesOrder.query.all()
    return render_template('sales_orders.html', sales_orders=sales_orders)

# Create New Order Page
# Delete Sales Order
@app.route('/delete_order/<int:order_id>', methods=['POST'])
@role_required("admin")
def delete_order(order_id):
    order = SalesOrder.query.get(order_id)
    if order:
        db.session.delete(order)
        db.session.commit()
    return redirect(url_for('index'))

# Create New Order Page (unchanged)
@app.route('/new_order', methods=['GET', 'POST'])
def new_order():
    customers = Student.query.all()
    order = None  # Initialize order variable

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        reference_no = request.form['reference_no']
        order_status = request.form['order_status']
        shipment_status = request.form['shipment_status']
        total_amount = float(request.form['total_amount'])
        amount_received = float(request.form['amount_received'])

        # Check if we are editing an existing order
        if 'order_id' in request.form and request.form['order_id']:
            order_id = request.form['order_id']
            order = SalesOrder.query.get(order_id)
            if order:
                order.customer_id = customer_id
                order.reference_no = reference_no
                order.order_status = order_status
                order.shipment_status = shipment_status
                order.total_amount = total_amount
                order.amount_received = amount_received
                db.session.commit()
        else:
            # Create a new order
            sales_order_no = get_next_sales_order_no()
            new_order = SalesOrder(
                sales_order_no=sales_order_no,
                customer_id=customer_id,
                reference_no=reference_no,
                order_status=order_status,
                shipment_status=shipment_status,
                total_amount=total_amount,
                amount_received=amount_received
            )
            db.session.add(new_order)
            db.session.commit()

        return redirect(url_for('index'))

    # If an order_id is provided, fetch the order details
    order_id = request.args.get('order_id')
    if order_id:
        order = SalesOrder.query.get(order_id)

    return render_template('new_order.html', customers=customers, sales_order_no=get_next_sales_order_no(), order=order)

@app.route("/customers")
def customers():
    return render_template("Customers.html", users=Student.query.all())

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/delete", methods=["POST"])
@role_required("admin")
def delete_users():
    if 'user_id' in request.form:
        user_id = int(request.form['user_id'])
        user = Student.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
    elif 'user_ids' in request.form:
        user_ids = request.form.getlist("user_ids")
        if user_ids:
            user_ids = [int(user_id) for user_id in user_ids]
            Student.query.filter(Student.roll_no.in_(user_ids)).delete(synchronize_session=False)
            db.session.commit()
    return redirect(url_for("customers"))

@app.route("/edit/<int:roll_no>")
@role_required("admin")
def edit_user(roll_no):
    user = Student.query.get(roll_no)
    if user:
        return render_template("form.html", user=user)
    return redirect(url_for("customers"))
@app.route('/dashboard')
def dashboard():
    data = {
        "sales_activity": {"to_be_packed": 51, "to_be_shipped": 40, "to_be_delivered": 52, "to_be_invoiced": 97},
        "inventory_summary": {"quantity_in_hand": 12746, "quantity_to_receive": 62},
        "product_details": {"low_stock": 22, "item_groups": 34, "all_items": 129, "active_items_percentage": 78},
       
        "purchase_order": {"quantity_ordered": 2, "total_cost": "Rs. 14500.00"},
        "sales_order": {"draft": 23, "confirmed": 51, "packed": 10, "shipped": 10, "invoiced": 40}
    }
    return render_template('dashboard.html', data=data)

@app.route("/formSubmit", methods=["POST"])
def submitFunction():
    roll_no = request.form.get("roll_no")
    name = request.form.get("customer-name")
    company_name = request.form.get("customer-company_name")
    email = request.form.get("customer-email")
    work_phone = request.form.get("customer-work_phone")
    receivables = request.form.get("customer-receivables")
    unused_credits = request.form.get("customer-unused-credits")

    if roll_no:
        user = Student.query.get(roll_no)
        if user:
            user.name = name
            user.company_name = company_name
            user.email = email
            user.work_phone = work_phone
            user.receivables = receivables
            user.unused_credits = unused_credits
    else:
        user = Student(name, company_name, email, work_phone, receivables, unused_credits)
        db.session.add(user)

    db.session.commit()
    return redirect(url_for("customers"))


@app.route('/update_package_status/<int:package_id>', methods=['POST'])
def update_package_status(package_id):
    package = Package.query.get(package_id)
    if package:
        new_status = request.form.get('status')  # Get the new status from the form
        package.status = new_status  # Update the status
        db.session.commit()
        
    
    return redirect(url_for('packages'))  # Redirect to the packages page
@app.route('/packages')
def packages():
    # Fetch packages based on their status
    not_shipped_packages = Package.query.filter_by(status="Not Shipped").all()
    delivered_packages = Package.query.filter_by(status="Delivered").all()
    shipped_sales_orders = SalesOrder.query.filter_by(shipment_status="Shipped").all()
    
    return render_template('packages.html', 
                           not_shipped_packages=not_shipped_packages,
                           shipped_sales_orders=shipped_sales_orders,
                           delivered_packages=delivered_packages)
# Models
class InventoryAdjustment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    item_name = db.Column(db.String(100), nullable=False)
    quantity_available = db.Column(db.Integer, nullable=False)
    new_quantity_on_hand = db.Column(db.Integer, nullable=False)
    quantity_adjusted = db.Column(db.Integer, nullable=False)
    account = db.Column(db.String(50), nullable=False)
    
class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    salutation = db.Column(db.String(10))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    vendor_display_name = db.Column(db.String(100))
    vendor_email = db.Column(db.String(100), nullable=False, unique=True)
    work_phone = db.Column(db.String(20), nullable=False)
    mobile = db.Column(db.String(20))

    def __repr__(self):
        return f'<Vendor {self.id} - {self.first_name} {self.last_name}>'

class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_no = db.Column(db.String(50), unique=True, nullable=False)  # Add this line
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    vendor = db.relationship('Vendor', backref=db.backref('purchase_orders', lazy=True))
    order_date = db.Column(db.Date, default=db.func.current_date())
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50))
    reference_no = db.Column(db.String(50), nullable=True)  

def get_next_purchase_order_no():
    last_order = PurchaseOrder.query.order_by(PurchaseOrder.id.desc()).first()
    if last_order:
        last_number = int(last_order.purchase_order_no.split('-')[-1])
        return f"PO-{last_number + 1:02d}"
    return "01"

class ItemCategory(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     category_name = db.Column(db.String(30))
     category_remarks=db.Column(db.String(80))
     unit=db.Column(db.String(10))     
class Items(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(30))
    item_remarks = db.Column(db.String(80))
    item_category = db.Column(db.Integer)  
    item_colour = db.Column(db.String(20))
    item_size = db.Column(db.String(10))
    purchase_rate = db.Column(db.Float)  
    sales_rate = db.Column(db.Float)     
    quantity = db.Column(db.Integer)     
    reference_number = db.Column(db.String(30)) 

# route for dashboard page

# routing for  Vendors page
@app.route('/vendors', methods=['GET', 'POST'])
def vendors():
    if request.method == 'POST':
        selected_vendors = request.form.getlist('selected_vendors[]')
        for vendor_id in selected_vendors:
            vendor = Vendor.query.get(vendor_id)
            if vendor:
                db.session.delete(vendor)
        db.session.commit()

        return redirect(url_for('vendors'))

    search_query = request.args.get('q')
    vendors = Vendor.query

    if search_query:
        vendors = vendors.filter(
            db.or_(
                Vendor.first_name.ilike(f"%{search_query}%"),
                Vendor.last_name.ilike(f"%{search_query}%"),
                Vendor.company_name.ilike(f"%{search_query}%"),
                Vendor.vendor_display_name.ilike(f"%{search_query}%"),
                Vendor.vendor_email.ilike(f"%{search_query}%")
            )
        )
    vendors = vendors.all()
    return render_template('vendors.html', vendors=vendors)
@app.route('/add_vendor', methods=['GET', 'POST'])
def add_vendor():
    if request.method == 'POST':
        try:
            # Check if the email already exists
            existing_vendor = Vendor.query.filter_by(vendor_email=request.form['vendor_email']).first()
            if existing_vendor:
             
                return render_template('add_vendor.html', error='Email address already exists.')

            new_vendor = Vendor(
                salutation=request.form['salutation'],
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                company_name=request.form['company_name'],
                vendor_display_name=request.form['vendor_display_name'],
                vendor_email=request.form['vendor_email'],
                work_phone=request.form['work_phone'],
                mobile=request.form['mobile']
            )
            db.session.add(new_vendor)
            db.session.commit()
           
            return redirect(url_for('vendors'))
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()  # Rollback the session on error
     
            return render_template('add_vendor.html', error='An error occurred while adding the vendor.')
    return render_template('add_vendor.html')

@app.route('/edit_vendor/<int:vendor_id>', methods=['GET', 'POST'])
@role_required("admin")
def edit_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    if request.method == 'POST':
        try:
            vendor.salutation = request.form['salutation']
            vendor.first_name = request.form['first_name']
            vendor.last_name = request.form['last_name']
            vendor.company_name = request.form['company_name']
            vendor.vendor_display_name = request.form['vendor_display_name']
            vendor.vendor_email = request.form['vendor_email']
            vendor.work_phone = request.form['work_phone']
            vendor.mobile = request.form['mobile']
            db.session.commit()
           
            return redirect(url_for('vendors'))
        except sqlalchemy.exc.IntegrityError:
         
            return render_template('edit_vendor.html', vendor=vendor, error='Email address already exists.')
    return render_template('edit_vendor.html', vendor=vendor)


@app.route('/delete_vendor/<int:vendor_id>', methods=['POST'])
@role_required("admin")
def delete_vendor(vendor_id):
    try:
        vendor = Vendor.query.get_or_404(vendor_id)
        db.session.delete(vendor)
        db.session.commit()
        flash('Vendor deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting vendor: {str(e)}', 'danger')
    
    return redirect(url_for('vendors'))
@app.route('/purchase_orders', methods=['GET', 'POST'])
def purchase_orders():
    purchase_orders = PurchaseOrder.query.join(Vendor).all()
    return render_template('purchase_orders.html', purchase_orders=purchase_orders, vendors=Vendor.query.all())

@app.route('/add_purchase_order', methods=['POST'])
def add_purchase_order():
    
        new_order = PurchaseOrder(
            purchase_order_no=get_next_purchase_order_no(),  # Generate the purchase order number
            vendor_id=request.form['vendor_id'],
            reference_no=request.form['reference_no'],  # Capture the reference number from the form
            amount=request.form['amount'],
            status=request.form['status']
        )
        db.session.add(new_order)
        db.session.commit()
     
        return redirect(url_for('purchase_orders'))

@app.route('/edit_purchase_order/<int:order_id>', methods=['GET', 'POST'])
@role_required("admin")
def edit_purchase_order(order_id):

    order = PurchaseOrder.query.get_or_404(order_id)
    vendor = Vendor.query.get(order.vendor_id)  # Fetch the vendor associated with this order

    if request.method == 'POST':
        try:
            # Update the order details
            order.amount = request.form['amount']
            order.status = request.form['status']
            # Update vendor details
            vendor.salutation = request.form['salutation']
            vendor.first_name = request.form['first_name']
            vendor.last_name = request.form['last_name']
            vendor.company_name = request.form['company_name']
            vendor.vendor_display_name = request.form['vendor_display_name']
            vendor.vendor_email = request.form['vendor_email']
            vendor.work_phone = request.form['work_phone']
            vendor.mobile = request.form['mobile']
            
            db.session.commit()
           
            return redirect(url_for('purchase_orders'))  # Redirect to the purchase orders page
        except Exception as e:
            db.session.rollback()
       
            return redirect(url_for('purchase_orders'))
    return render_template('edit_purchase_order.html', order=order, vendor=vendor)

@app.route('/delete_purchase_order/<int:order_id>', methods=['POST'])
@role_required("admin")
def delete_purchase_order(order_id):
    print(f"Attempting to delete purchase order with ID: {order_id}")  # Debugging line
    order = PurchaseOrder.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('Purchase order deleted successfully!', 'success')
    return redirect(url_for('purchase_orders'))
from sqlalchemy.exc import IntegrityError

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form.get('username')  # Use .get() to avoid KeyError
    email = request.form.get('email')

    if not username or not email:  # Validate input to prevent empty values
        flash('Error: Username and email are required!', 'danger')
        return redirect(url_for('users'))

    new_user = User(username=username, email=email)

    try:
        db.session.add(new_user)
        db.session.commit()
      
    except IntegrityError:
        db.session.rollback()
        

    return redirect(url_for('users'))

# Route for inventory adjustments page.
@app.route('/inventory_adjustments')
def inventory_adjustments():
    adjustments = InventoryAdjustment.query.all()
    return render_template('inventory_adjustments.html', adjustments=adjustments)

# Route for items page.
@app.route('/items', methods=['GET'])
def items():
    all_items = Items.query.all()  # Fetch all items from the database
    return render_template('items.html', items=all_items)  # Pass items to the template

@app.route('/items_add', methods=['GET', 'POST'])
def items_add():
    # Fetch all categories to populate the dropdown
    categories = ItemCategory.query.all()

    if request.method == 'POST':
        try:
            new_item = Items(
                item_name=request.form['item_name'],
                item_remarks=request.form['item_remarks'],
                item_category=int(request.form['item_category']),
                item_colour=request.form['item_colour'],
                item_size=request.form['item_size'],
                purchase_rate=float(request.form['purchase_rate']),  # New field for purchase rate
                sales_rate=float(request.form['sales_rate']),        # New field for sales rate
                quantity=int(request.form['quantity']),              # New field for quantity
                reference_number=request.form['reference_number']    # New field for reference number
            )
            db.session.add(new_item)
            db.session.commit()
            flash('Item added successfully!', 'success')
            return redirect(url_for('items'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding item: {str(e)}', 'danger')

    # Always return the template with categories
    return render_template('items_add.html', categories=categories)  # Add this line

    
    # Always return the template with categories
   
@app.route('/items_edit/<int:id>', methods=['GET', 'POST'])

@role_required("admin")
def items_edit(id):
    item = Items.query.get_or_404(id)
    if request.method == 'POST':
        try:
            item.item_name = request.form['item_name']
            item.item_remarks = request.form['item_remarks']
            item.item_category = int(request.form['item_category'])
            item.item_colour = request.form['item_colour']
            item.item_size = request.form['item_size']
            
            db.session.commit()
      
            return redirect(url_for('items'))
        except Exception as e:
            db.session.rollback()
           

    return render_template('items_edit.html', item=item)

# 🔹 Route to delete an item
@app.route('/items_delete/<int:id>', methods=['POST'])
@role_required("admin")
def items_delete(id):
    item = Items.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
       

    return redirect(url_for('items'))

# Route for new item group form.
@app.route('/group_items', methods=['GET'])
def group_items():
    group_items = ItemCategory.query.all()  # Fetch all categories from DB
    return render_template('group_items.html', group_items=group_items)

# category add
@app.route('/group_items_add', methods=['GET', 'POST'])
@role_required("admin") 
def group_item_add():
    if request.method == 'POST':
        try:
            new_group_item = ItemCategory(
                category_name=request.form['category_name'],
                category_remarks=request.form['category_remarks'],
                unit=request.form['category_units']
            )
            db.session.add(new_group_item)
            db.session.commit()
         
            return redirect(url_for('group_items'))  # Redirect to list page after adding
        except Exception as e:
            db.session.rollback()
           

    return render_template('group_items_add.html')  # Render the add form on GET request

# edit category
@app.route('/group_items_edit/<int:id>', methods=['GET', 'POST'])
@role_required("admin") 
def category_item_edit(id):
    print(f"Editing category with ID: {id}")  # Debugging step
    category = ItemCategory.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            category.category_name = request.form['category_name']
            category.category_remarks = request.form['category_remarks']
            category.unit = request.form['category_units']
            db.session.commit()
           
            return redirect(url_for('group_items'))  # Redirect after update
        except Exception as e:
            db.session.rollback()
    

    return render_template('group_items_edit.html', category=category)


@app.route('/category_item_delete/<int:category_id>', methods=['POST'])
@role_required("admin") 
def category_item_delete(category_id):
    try:
        category = ItemCategory.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
     
    except Exception as e:
        db.session.rollback()
   

    return redirect(url_for('group_items'))



# Route for the new adjustment page
@app.route('/new_adjustment', methods=['GET', 'POST'])


def new_adjustment():
    if request.method == 'POST':
        date = request.form['date']
        account = request.form['account']
        reason = request.form['reason']
        description = request.form['description']
        item_name = request.form['item_name']
        quantity_available = request.form['quantity_available']
        new_quantity_on_hand = request.form['new_quantity_on_hand']
        quantity_adjusted = request.form['quantity_adjusted']
        
        new_adjustment = InventoryAdjustment(
            date=date,
            account=account,
            reason=reason,
            description=description,
            item_name=item_name,
            quantity_available=quantity_available,
            new_quantity_on_hand=new_quantity_on_hand,
            quantity_adjusted=quantity_adjusted
        )
        
        db.session.add(new_adjustment)
        db.session.commit()
       
        return redirect(url_for('inventory_adjustments'))

    return render_template('new_adjustment.html')

class PurchaseReceive(db.Model):
    __tablename__ = "purchase_receives"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    purchase_order = db.relationship('PurchaseOrder', backref='receives')
    vendor = db.relationship('Vendor', backref='receives')


@app.route('/purchase_receives', methods=['GET'])
def purchase_receives():
    receives = PurchaseReceive.query.join(PurchaseOrder).join(Vendor).all()
    return render_template('purchase_receives.html', receives=receives)

@app.route('/add_purchase_receive', methods=['GET', 'POST'])
def add_purchase_receive():
    if request.method == 'POST':
        # Convert the date string to a date object
        date_str = request.form['date']
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()  # Convert to date object

        new_receive = PurchaseReceive(
            date=date_obj,  # Use the date object here
            purchase_order_id=request.form['purchase_order_id'],
            vendor_id=request.form['vendor_id'],
            status=request.form['status'],
            quantity=request.form['quantity']
        )
        db.session.add(new_receive)
        db.session.commit()
      
        return redirect(url_for('purchase_receives'))

    vendors = Vendor.query.all()
    purchase_orders = PurchaseOrder.query.all()
    return render_template('add_purchase_receive.html', vendors=vendors, purchase_orders=purchase_orders)

@app.route('/edit_purchase_receive/<int:id>', methods=['GET', 'POST'])
@role_required("admin")
def edit_purchase_receive(id):
    receive = PurchaseReceive.query.get_or_404(id)
    
    if request.method == 'POST':
        # Convert the date string to a date object
        date_str = request.form['date']
        receive.date = datetime.strptime(date_str, '%Y-%m-%d').date()  # Convert to date object
        
        # Assign other fields
        receive.purchase_order_id = request.form['purchase_order_id']
        receive.vendor_id = request.form['vendor_id']
        receive.status = request.form['status']
        receive.quantity = request.form['quantity']
        
        # Commit the changes to the database
        db.session.commit()
 
        return redirect(url_for('purchase_receives'))

    vendors = Vendor.query.all()
    purchase_orders = PurchaseOrder.query.all()
    return render_template('edit_purchase_receive.html', receive=receive, vendors=vendors, purchase_orders=purchase_orders)

@app.route('/delete_purchase_receive/<int:id>', methods=['POST'])
@role_required("admin")
def delete_purchase_receive(id):
    receive = PurchaseReceive.query.get_or_404(id)
    db.session.delete(receive)
    db.session.commit()
  
    return redirect(url_for('purchase_receives'))

# Initialize Database
with app.app_context():
    db.create_all()
    

    if not User.query.filter_by(role="admin").first():
        admin = User(email="admin@gmail.com",role="admin")
        admin.save_hash_password("admin")

        db.session.add(admin)
        db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

