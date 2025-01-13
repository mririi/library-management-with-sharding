# Library Management System - Backend Code (Flask Example)

from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

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
    subscribers.insert_one({"name": name, "email": email})
    return redirect(url_for('subscribers_page'))

@app.route('/api/subscribers/<id>', methods=['POST'])
def delete_subscriber(id):
    subscribers.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('subscribers_page'))

# API Routes for Documents
@app.route('/api/documents', methods=['POST'])
def add_document():
    title = request.form.get('title')
    author = request.form.get('author')
    documents.insert_one({"title": title, "author": author})
    return redirect(url_for('documents_page'))

@app.route('/api/documents/<id>', methods=['POST'])
def delete_document(id):
    documents.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('documents_page'))

@app.route('/api/loans', methods=['POST'])
def add_loan():
    document_id = request.form.get('document_id')
    subscriber_id = request.form.get('subscriber_id')

    # Check if the document is available
    document = documents.find_one({"_id": ObjectId(document_id)})
    if not document or not document.get("available", True):
        return jsonify({"error": "Document is not available"}), 400

    # Insert the loan
    loan = {
        "document_id": ObjectId(document_id),
        "subscriber_id": ObjectId(subscriber_id),
        "borrower": subscriber_id,
        "returned": False
    }
    loans.insert_one(loan)

    # Mark the document as unavailable
    documents.update_one({"_id": ObjectId(document_id)}, {"$set": {"available": False}})

    return redirect(url_for('loans_page'))


@app.route('/api/loans/<id>/return', methods=['POST'])
def return_loan(id):
    loan = loans.find_one({"_id": ObjectId(id)})
    if loan:
        loans.update_one({"_id": ObjectId(id)}, {"$set": {"returned": True}})
        documents.update_one({"_id": ObjectId(loan["document_id"])}, {"$set": {"available": True}})
    return redirect(url_for('loans_page'))

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

    # Map IDs to names for display
    subscriber_map = {str(sub["_id"]): sub["name"] for sub in all_subscribers}
    document_map = {str(doc["_id"]): doc["title"] for doc in all_documents}

    for loan in all_loans:
        loan["_id"] = str(loan["_id"])
        loan["subscriber_name"] = subscriber_map.get(str(loan["subscriber_id"]), "Unknown Subscriber")
        loan["document_title"] = document_map.get(str(loan["document_id"]), "Unknown Document")

    return render_template('loans.html', loans=all_loans, subscribers=all_subscribers, documents=all_documents)


if __name__ == '__main__':
    app.run(debug=True)
