from flask import render_template, request, redirect, url_for, session, flash
from app import app
from app.models.user import User 
from .decorators import login_required
import logging
from datetime import datetime, timedelta
from app.models.car import Car as Vehicle
from bson.objectid import ObjectId
from app.models.car import Car
from app.models.permit import Permit
from app.models.payment import Payment
from flask import jsonify
import os
from datetime import datetime



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 

from app.models.booking import Booking

@app.route('/select_vehicle', methods=['GET', 'POST'])
@login_required
def select_vehicle():
    print("Select Vehicle")
    print(session)
    user_id = session.get("user_id")
    if not user_id:
        flash("You must be logged in to select a vehicle.", "error")
        return redirect(url_for("login"))

    if request.method == 'POST':
        # Handle POST request
        permit_id = request.form.get('permit_id')
        vehicle_id = request.form.get('vehicle_id')

        # Validate inputs
        if not permit_id or not vehicle_id:
            flash("Please select both a permit and a vehicle.", "error")
            return redirect(url_for('select_vehicle'))

        # Check if the selected vehicle already has a permit of the same type
        permit = Permit.find_one({"_id": ObjectId(permit_id)})
        if not permit:
            flash("Selected permit not found.", "error")
            return redirect(url_for('select_vehicle'))

        booking = Booking.find_one({
            "car_id": ObjectId(vehicle_id),
            "permit_details.type": permit.get("permit_name")
        })

        if booking:
            flash(
                f"This vehicle already has a {permit.get('permit_name')} parking permit. "
                "Please contact the administrative police department for more information.",
                "error"
            )
            return redirect(url_for('select_vehicle'))

        # Store selections in session
        session['selected_permit'] = permit_id
        session['selected_vehicle'] = vehicle_id

        # Redirect to finalize permit
        return redirect(url_for('finalize_permit'))

    # Handle GET request
    vehicles = list(Vehicle.find({"user_id": ObjectId(user_id)}))
    selected_permit_id = session.get("selected_permit")
    permit = Permit.find_one({"_id": ObjectId(selected_permit_id)}) if selected_permit_id else None

    # Render template
    return render_template(
        'student/select_vehicle.html',
        vehicles=vehicles,
        permit=permit
    )





@app.route('/validate_vehicle', methods=['POST'])
@login_required
def validate_vehicle():
    user_id = session.get("user_id")
    print(user_id)
    data = request.get_json()
    print(data)
    # Extract permit_id and vehicle_id from the request
    permit_id = data.get("permit_id")
    vehicle_id = data.get("vehicle_id")

    if not permit_id or not vehicle_id:
        return jsonify({"success": False, "message": "Permit or vehicle ID is missing."}), 400

    # Fetch permit details
    permit = Permit.find_one({"_id": ObjectId(permit_id)})
    print(permit)
    if not permit:
        return jsonify({"success": False, "message": "Invalid permit ID."}), 404

    # Check if the vehicle already has a permit of the same type
    booking = Booking.find_one({"car_id": vehicle_id, "permit_details.type": permit.get("permit_name")})
    print("Booking", booking)
    if booking:
        return jsonify({
            "success": False,
            "message": f"This vehicle already has a {permit.get('permit_name')} parking permit. "
                       "Please contact the administrative police department for more information."
        }), 400

    return jsonify({"success": True, "message": "Vehicle and permit selection is valid."}), 200




@app.route('/add_vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    if request.method == 'POST':
        user_id = session.get('user_id')
        
        # Validate Plate Number confirmation
        plate_number = request.form.get("number_plate").strip()
        plate_number_confirm = request.form.get("plate_number_confirm").strip()
        if plate_number != plate_number_confirm:
            flash("Plate numbers do not match. Please try again.", "error")
            return redirect(url_for('add_vehicle'))
        
        # Gather the input data
        data = {
            "user_id": ObjectId(user_id),
            "number_plate": plate_number,
            "relationship": request.form.get("relationship").strip(),
            "state": request.form.get("state").strip(),
            "year": request.form.get("year").strip(),
            "make": request.form.get("make").strip(),
            "model": request.form.get("model").strip(),
            "color": request.form.get("color").strip(),
            "style": request.form.get("style").strip()
        }
        
        # Insert into the database
        Car.insert_one(data)
        flash("Vehicle added successfully.", "success")
        return redirect(url_for('select_vehicle'))  # Redirect back to the vehicle selection page

    # Pass car makes, models, and styles for dynamic dropdowns
    car_data = {
        "Toyota": {
            "Camry": ["Sedan", "Hybrid"],
            "Corolla": ["Sedan", "Hatchback"],
            "RAV4": ["SUV", "Hybrid"]
        },
        "Honda": {
            "Civic": ["Sedan", "Coupe"],
            "Accord": ["Sedan", "Hybrid"],
            "CR-V": ["SUV"]
        },
        "Ford": {
            "F-150": ["Truck"],
            "Explorer": ["SUV"],
            "Mustang": ["Coupe"]
        }
    }

    states = [
        "Arkansas", "Texas", "California", "New York", "Florida", 
        "Alabama", "Alaska", "Arizona", "Colorado", "Connecticut", 
        "Delaware", "Georgia"
    ]

    return render_template('student/add_vehicle.html', car_data=car_data, states=states)



@app.route('/finalize_permit', methods=['POST'])
@login_required
def finalize_permit():
    vehicle_id = request.form.get('vehicle_id')
    user_id = session.get('user_id')

    # Retrieve the selected vehicle details
    vehicle = Vehicle.find_one({"_id": ObjectId(vehicle_id), "user_id": ObjectId(user_id)})

    # Ensure a valid vehicle is selected
    if not vehicle:
        flash("Invalid vehicle selection. Please try again.", "error")
        return redirect(url_for('select_vehicle'))

    # Retrieve the permit details from the session
    permit_id = session.get("selected_permit")
    if not permit_id:
        flash("Permit details not found. Please select a permit again.", "error")
        return redirect(url_for('select_permit'))

    permit = Permit.find_one({"_id": ObjectId(permit_id)})

    # Ensure a valid permit is found
    if not permit:
        flash("Permit details not found. Please select a permit again.", "error")
        return redirect(url_for('select_permit'))

    # Store vehicle details in session
    session['selected_vehicle'] = str(vehicle_id)
    session['vehicle_details'] = {
        'state': vehicle.get('state'),
        'number_plate': vehicle.get('number_plate'),
        'year': vehicle.get('year'),
        'make': vehicle.get('make'),
        'model': vehicle.get('model'),
        'color': vehicle.get('color'),
    }

    # Render the final confirmation page
    return render_template('student/finalize_permit.html', vehicle=vehicle, permit=permit)




@app.route('/confirm_purchase', methods=['POST'])
@login_required
def confirm_purchase():
    user_id = session.get('user_id')
    permit_id = session.get('selected_permit')
    vehicle_id = session.get('selected_vehicle')

    # Ensure all necessary data is available
    if not all([user_id, permit_id, vehicle_id]):
        flash("Missing data. Please try again.", "error")
        return redirect(url_for('select_permit'))

    # Create a new permit purchase record (you might need to adjust this based on your data model)
    purchase = {
        'user_id': ObjectId(user_id),
        'permit_id': ObjectId(permit_id),
        'vehicle_id': ObjectId(vehicle_id),
        'purchase_date': datetime.utcnow(),
        'status': 'active',
    }

    # Insert the purchase record into the database
    result = Permit.insert_one(purchase)  # Replace with your collection

    # Clear the selection from the session
    session.pop('selected_permit', None)
    session.pop('selected_vehicle', None)
    session.pop('vehicle_details', None)

    flash("Your permit has been successfully purchased!", "success")
    return redirect(url_for('user_dashboard'))  # Redirect to a dashboard or confirmation page
