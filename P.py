from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# In-memory database (for demo purposes)
users = {}
customers = {}
campaigns = {}

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if username in users and check_password_hash(users[username]['password'], password):
            session['user'] = username
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    
    if username in users:
        return jsonify({'success': False, 'message': 'User already exists'}), 400
    
    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
    
    users[username] = {
        'password': generate_password_hash(password),
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify({'success': True, 'message': 'Account created successfully'})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ==================== DASHBOARD ROUTE ====================

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', username=session['user'])

# ==================== CUSTOMER MANAGEMENT ROUTES ====================

@app.route('/api/customers', methods=['GET', 'POST'])
def manage_customers():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user = session['user']
    
    if user not in customers:
        customers[user] = {}
    
    if request.method == 'POST':
        data = request.get_json()
        customer_id = data.get('id', str(len(customers[user]) + 1))
        
        customers[user][customer_id] = {
            'id': customer_id,
            'name': data.get('name'),
            'ways_price': float(data.get('ways_price', 0)),
            'ways_use': float(data.get('ways_use', 0)),
            'customer_modem': data.get('customer_modem'),
            'customer_package': data.get('customer_package'),
            'decades': data.get('decades', []),
            'total': float(data.get('ways_price', 0)) * float(data.get('ways_use', 0)) + 
                    (float(data.get('customer_modem', 0)) if data.get('customer_modem') else 0) + 
                    (float(data.get('customer_package', 0)) if data.get('customer_package') else 0),
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'message': 'Customer added successfully', 'customer': customers[user][customer_id]})
    
    else:
        return jsonify({'success': True, 'customers': list(customers[user].values())})

@app.route('/api/customers/<customer_id>', methods=['GET', 'PUT', 'DELETE'])
def customer_detail(customer_id):
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user = session['user']
    
    if user not in customers or customer_id not in customers[user]:
        return jsonify({'success': False, 'message': 'Customer not found'}), 404
    
    if request.method == 'GET':
        return jsonify({'success': True, 'customer': customers[user][customer_id]})
    
    elif request.method == 'PUT':
        data = request.get_json()
        customer = customers[user][customer_id]
        
        customer['name'] = data.get('name', customer['name'])
        customer['ways_price'] = float(data.get('ways_price', customer['ways_price']))
        customer['ways_use'] = float(data.get('ways_use', customer['ways_use']))
        customer['customer_modem'] = data.get('customer_modem', customer['customer_modem'])
        customer['customer_package'] = data.get('customer_package', customer['customer_package'])
        customer['decades'] = data.get('decades', customer['decades'])
        
        # Recalculate total
        customer['total'] = (customer['ways_price'] * customer['ways_use'] + 
                           (float(customer['customer_modem']) if customer['customer_modem'] else 0) + 
                           (float(customer['customer_package']) if customer['customer_package'] else 0))
        
        return jsonify({'success': True, 'message': 'Customer updated successfully', 'customer': customer})
    
    elif request.method == 'DELETE':
        del customers[user][customer_id]
        return jsonify({'success': True, 'message': 'Customer deleted successfully'})

# ==================== DECADE MANAGEMENT ROUTES ====================

@app.route('/api/customers/<customer_id>/decades', methods=['POST', 'PUT', 'DELETE'])
def manage_decades(customer_id):
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user = session['user']
    
    if user not in customers or customer_id not in customers[user]:
        return jsonify({'success': False, 'message': 'Customer not found'}), 404
    
    customer = customers[user][customer_id]
    data = request.get_json()
    
    if request.method == 'POST':
        decade = {
            'id': str(len(customer['decades']) + 1),
            'name': data.get('name'),
            'created_at': datetime.now().isoformat()
        }
        customer['decades'].append(decade)
        return jsonify({'success': True, 'message': 'Decade added', 'decade': decade})
    
    elif request.method == 'PUT':
        decade_id = data.get('decade_id')
        for decade in customer['decades']:
            if decade['id'] == decade_id:
                decade['name'] = data.get('name', decade['name'])
                return jsonify({'success': True, 'message': 'Decade updated', 'decade': decade})
        return jsonify({'success': False, 'message': 'Decade not found'}), 404
    
    elif request.method == 'DELETE':
        decade_id = data.get('decade_id')
        customer['decades'] = [d for d in customer['decades'] if d['id'] != decade_id]
        return jsonify({'success': True, 'message': 'Decade deleted'})

# ==================== CAMPAIGN MANAGEMENT ROUTES ====================

@app.route('/api/campaigns', methods=['GET', 'POST'])
def manage_campaigns():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user = session['user']
    
    if user not in campaigns:
        campaigns[user] = {}
    
    if request.method == 'POST':
        data = request.get_json()
        campaign_id = data.get('id', str(len(campaigns[user]) + 1))
        
        tool1_total = float(data.get('tool1_use', 0)) * float(data.get('tool1_price', 0))
        tool2_total = float(data.get('tool2_use', 0)) * float(data.get('tool2_price', 0))
        total_price = tool1_total + tool2_total
        
        campaigns[user][campaign_id] = {
            'id': campaign_id,
            'name': data.get('name'),
            'tool1_use': float(data.get('tool1_use', 0)),
            'tool1_price': float(data.get('tool1_price', 0)),
            'tool2_use': float(data.get('tool2_use', 0)),
            'tool2_price': float(data.get('tool2_price', 0)),
            'tool1_total': tool1_total,
            'tool2_total': tool2_total,
            'total_price': total_price,
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'message': 'Campaign added successfully', 'campaign': campaigns[user][campaign_id]})
    
    else:
        return jsonify({'success': True, 'campaigns': list(campaigns[user].values())})

@app.route('/api/campaigns/<campaign_id>', methods=['GET', 'PUT', 'DELETE'])
def campaign_detail(campaign_id):
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user = session['user']
    
    if user not in campaigns or campaign_id not in campaigns[user]:
        return jsonify({'success': False, 'message': 'Campaign not found'}), 404
    
    if request.method == 'GET':
        return jsonify({'success': True, 'campaign': campaigns[user][campaign_id]})
    
    elif request.method == 'PUT':
        data = request.get_json()
        campaign = campaigns[user][campaign_id]
        
        campaign['name'] = data.get('name', campaign['name'])
        campaign['tool1_use'] = float(data.get('tool1_use', campaign['tool1_use']))
        campaign['tool1_price'] = float(data.get('tool1_price', campaign['tool1_price']))
        campaign['tool2_use'] = float(data.get('tool2_use', campaign['tool2_use']))
        campaign['tool2_price'] = float(data.get('tool2_price', campaign['tool2_price']))
        
        campaign['tool1_total'] = campaign['tool1_use'] * campaign['tool1_price']
        campaign['tool2_total'] = campaign['tool2_use'] * campaign['tool2_price']
        campaign['total_price'] = campaign['tool1_total'] + campaign['tool2_total']
        
        return jsonify({'success': True, 'message': 'Campaign updated successfully', 'campaign': campaign})
    
    elif request.method == 'DELETE':
        del campaigns[user][campaign_id]
        return jsonify({'success': True, 'message': 'Campaign deleted successfully'})

# ==================== ERROR HANDLING ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'message': 'Server error'}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("Phone Controller Application")
    print("=" * 50)
    print("Starting application on http://localhost:5000")
    print("Press CTRL+C to stop the server")
    print("=" * 50)
    app.run(debug=True, host='localhost', port=5000)
  
