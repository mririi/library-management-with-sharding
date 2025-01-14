# Library Management System - Backend Code (Flask Example)

from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://127.0.0.1:27117,127.0.0.1:27118/book_management"
mongo = PyMongo(app)

# Collections
subscribers = mongo.db.subscribers
documents = mongo.db.documents
loans = mongo.db.loans

# Initialize database connection
def initialize_database():
    try:
        mongo.cx.server_info()
        print("Connected to MongoDB successfully!")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        exit(1)

initialize_database()

# API Routes for Subscribers
@app.route('/api/subscribers', methods=['POST'])
def add_subscriber():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    subscribers.insert_one({"name": name, "email": email, "phone": phone})
    return redirect(url_for('subscribers_page'))

@app.route('/api/subscribers/<id>/update', methods=['POST'])
def update_subscriber(id):
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    subscribers.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"name": name, "email": email, "phone": phone}}
    )
    return redirect(url_for('subscribers_page'))

# API Routes for Documents
@app.route('/api/documents', methods=['POST'])
def add_document():
    title = request.form.get('title')
    author = request.form.get('author')
    genre = request.form.get('genre')
    type = request.form.get('type')
    disponibility = request.form.get('disponibility', 'available')
    documents.insert_one({"title": title, "author": author, "genre": genre, "type": type, "disponibility": disponibility})
    return redirect(url_for('documents_page'))

@app.route('/api/documents/<id>/delete', methods=['POST'])
def delete_document(id):
    documents.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('documents_page'))

@app.route('/api/documents/<id>/update', methods=['POST'])
def update_document(id):
    title = request.form.get('title')
    author = request.form.get('author')
    genre = request.form.get('genre')
    type = request.form.get('type')
    disponibility = request.form.get('disponibility')
    documents.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"title": title, "author": author, "genre": genre, "type": type, "disponibility": disponibility}}
    )
    return redirect(url_for('documents_page'))

@app.route('/api/documents/search', methods=['GET'])
def search_documents():
    query = request.args.get('query', '')
    results = list(documents.find({
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"author": {"$regex": query, "$options": "i"}},
            {"genre": {"$regex": query, "$options": "i"}},
            {"type": {"$regex": query, "$options": "i"}}
        ]
    }))
    for res in results:
        res["_id"] = str(res["_id"])
    return jsonify(results)

# API Routes for Loans
@app.route('/api/loans', methods=['POST'])
def add_loan():
    document_id = request.form.get('document_id')
    borrower = request.form.get('borrower')
    date_start = request.form.get('date_start')
    date_return = request.form.get('date_return')
    loans.insert_one({
        "document_id": document_id,
        "borrower": borrower,
        "date_start": date_start,
        "date_return": date_return,
        "returned": False
    })
    return redirect(url_for('loans_page'))

@app.route('/api/loans/<id>/update', methods=['POST'])
def update_loan(id):
    document_id = request.form.get('document_id')
    borrower = request.form.get('borrower')
    date_start = request.form.get('date_start')
    date_return = request.form.get('date_return')
    loans.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "document_id": document_id,
            "borrower": borrower,
            "date_start": date_start,
            "date_return": date_return
        }}
    )
    return redirect(url_for('loans_page'))

@app.route('/api/loans/<id>/delete', methods=['POST'])
def delete_loan(id):
    loans.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('loans_page'))

@app.route('/api/loans/search', methods=['GET'])
def search_loans():
    query = request.args.get('query', '')
    results = list(loans.find({
        "$or": [
            {"borrower": {"$regex": query, "$options": "i"}},
            {"document_id": {"$regex": query, "$options": "i"}}
        ]
    }))
    for res in results:
        res["_id"] = str(res["_id"])
    return jsonify(results)

# Frontend Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subscribers')
def subscribers_page():
    all_subscribers = list(subscribers.find())
    for sub in all_subscribers:
        sub["_id"] = str(sub["_id"])
    return render_template('subscribers.html', subscribers=all_subscribers)

@app.route('/documents')
def documents_page():
    all_documents = list(documents.find())
    for doc in all_documents:
        doc["_id"] = str(doc["_id"])
    return render_template('documents.html', documents=all_documents)

@app.route('/loans')
def loans_page():
    all_loans = list(loans.find())
    all_subscribers = list(subscribers.find())
    all_documents = list(documents.find())
    now = datetime.now().strftime('%Y-%m-%d')

    # Process loans for overdue highlighting
    for loan in all_loans:
        loan["_id"] = str(loan["_id"])
        loan["date_return"] = loan.get("date_return", "N/A")
        loan["overdue"] = not loan.get("returned", True) and loan["date_return"] != "N/A" and loan["date_return"] < now

    # Prepare subscribers and documents for dropdowns
    for sub in all_subscribers:
        sub["_id"] = str(sub["_id"])

    for doc in all_documents:
        doc["_id"] = str(doc["_id"])

    return render_template(
        'loans.html',
        loans=all_loans,
        subscribers=all_subscribers,
        documents=all_documents,
        now=now
    )
if __name__ == '__main__':
    app.run(debug=True)
