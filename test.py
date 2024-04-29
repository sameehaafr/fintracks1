# export FLASK_APP=app
# flask shell
# db.drop_all()
# db.create_all()
from datetime import datetime
from app import db, Category, Expense

category_food = Category(name='Food')
category_clothing = Category(name='Clothing')
category_entertainment = Category(name='Entertainment')

db.session.add_all([category_food, category_clothing, category_entertainment])
db.session.commit()

expense_1 = Expense(amount=20.50, name='Dominos Pizza', purchase_date=datetime.strptime('2024-04-20', '%Y-%m-%d').date(), category_id=category_food.id)
expense_2 = Expense(amount=15.75, name='Jeans', purchase_date=datetime.strptime('2024-04-21', '%Y-%m-%d').date(), category_id=category_clothing.id)
expense_3 = Expense(amount=100.00, name='Broadway Show', purchase_date=datetime.strptime('2024-04-22', '%Y-%m-%d').date(), category_id=category_entertainment.id)

db.session.add_all([expense_1, expense_2, expense_3])
db.session.commit()
