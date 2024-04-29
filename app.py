import os
from flask import Flask, render_template, request, url_for, redirect # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from sqlalchemy.sql import func # type: ignore
from datetime import datetime
from flask import jsonify # type: ignore
from sqlalchemy import create_engine # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from sqlalchemy import bindparam # type: ignore
from sqlalchemy import text # type: ignore

# set up main database

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

engine = create_engine('sqlite:///database.db', isolation_level='READ COMMITTED')
Session = sessionmaker(bind=engine)
session = Session()

db = SQLAlchemy(app)

# set up data tables

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    def __repr__(self):
        return f'<Category {self.name}>'

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    amount = db.Column(db.Integer, nullable=False)
    purchase_date = db.Column(db.Date)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), index=True)
    category = db.relationship('Category', backref=db.backref('expenses', lazy=True))

    def __repr__(self):
        return f'<Expense {self.id}>'
    
# home page

@app.route('/')
def index():
    categories = Category.query.all()
    expenses = Expense.query.all()
    return render_template('index.html', categories=categories, expenses=expenses)

# directs 'Add Expense' button to add.html and passes category values

@app.route('/add_expense')
def add_expense_page():
    categories = Category.query.all()
    return render_template('add.html', categories=categories)

# contains 'Add Expense' functionality: takes name, amount, category, and purchase date as input from the user

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if request.method == 'POST':
        name = request.form['name']
        amount = float(request.form['amount'])
        purchase_date = datetime.strptime(request.form['purchase_date'], '%Y-%m-%d')
        category_id = int(request.form['category'])

        expense = Expense(name=name, amount=amount, purchase_date=purchase_date, category_id=category_id)
        db.session.add(expense)
        db.session.commit()

        return redirect(url_for('index'))

@app.route('/expense/<int:expense_id>/edit/', methods=('GET', 'POST'))
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    categories = Category.query.all()

    if request.method == 'POST':
        name = request.form['name']
        amount = float(request.form['amount'])
        purchase_date = datetime.strptime(request.form['purchase_date'], '%Y-%m-%d')
        category_id = int(request.form['category']) 

        expense.name = name
        expense.amount = amount
        expense.purchase_date = purchase_date
        expense.category_id = category_id

        db.session.commit()

        return redirect(url_for('index'))

    return render_template('edit.html', expense=expense, categories=categories)

@app.route('/expense/<int:expense_id>/delete/', methods=['GET', 'POST'])
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/report', methods=['GET', 'POST'])
def generate_report():
    if request.method == 'GET':
        filter_category = request.args.get('category')
        filter_date_start = request.args.get('date_start')
        filter_date_end = request.args.get('date_end')
        
        query = Expense.query
        if filter_category:
            query = query.filter_by(category_id=filter_category)
        if filter_date_start:
            query = query.filter(Expense.purchase_date >= filter_date_start)
        if filter_date_end:
            query = query.filter(Expense.purchase_date <= filter_date_end)
        
        expenses = query.all()

        total_exp = len(expenses)
        total_amt = sum(expense.amount for expense in expenses)
        avg_amt = total_amt / total_exp if total_exp > 0 else 0
        min_amt = min((expense.amount for expense in expenses), default=0)
        max_amt = max((expense.amount for expense in expenses), default=0)
        expenses_by_category = {}

        # using the indexes instead of for loop

        expenses_by_category = db.session.query(Expense.category_id, func.sum(Expense.amount))\
                                          .filter(Expense.id.in_([e.id for e in expenses]))\
                                          .group_by(Expense.category_id)\
                                          .all()
        expenses_by_category = {Category.query.get(category_id).name: total_amount 
                                for category_id, total_amount in expenses_by_category}
        
        
        report = []
        for expense in expenses:
            report.append({
                'name': expense.name,
                'amount': expense.amount,
                'purchase_date': expense.purchase_date.strftime('%Y-%m-%d'),
                'category_name': expense.category.name,
                'total_exp': total_exp,
                'total_amt': total_amt,
                'avg_amt': avg_amt,
                'min_amt': min_amt,
                'max_amt': max_amt,
                'expenses_by_category': expenses_by_category
            })
        
        return render_template('report.html', report=report)

@app.route('/edit_category', methods=['GET', 'POST'])
def edit_category():
    if request.method == 'GET':
        categories = Category.query.all()
        return render_template('categories.html', categories=categories)
    elif request.method == 'POST':
        action = request.form['action']
        if action == 'add':
            category_name = request.form['new_category']
            category = Category(name=category_name)
            db.session.add(category)
            db.session.commit()
        elif action == 'edit':
            category_id = int(request.form['category_id'])
            new_name = request.form['new_name']
            category = Category.query.get(category_id)
            category.name = new_name
            db.session.add(category)
            db.session.commit()
        elif action == 'delete':
            category_id = int(request.form['category_id'])
            category = Category.query.get(category_id)
            db.session.delete(category)
            db.session.commit()
        return redirect(url_for('edit_category'))

if __name__ == '__main__':
    app.run(debug=True)