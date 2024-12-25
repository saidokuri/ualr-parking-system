
from flask import render_template, request, redirect, url_for, session, flash
from app import app
from app.models.user import User 
from .decorators import login_required
import logging
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from app.models.car import Car
from app.models.permit import Permit
from app.models.parking_lot import ParkingLot
from app.models.payment import Payment
from flask import jsonify
import os
from datetime import datetime



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@app.route('/user_dashboard')
def user_dashboard():
    if "user_id" in session:
        user_role = session.get("role")
        if user_role in ["student", "faculty"]:
            # Fetch active permits
            permits = Permit.find({"status": "active"})  # Replace with actual database query
            
            # Fetch parking lots based on role and open lots
            reserved_lots = ParkingLot.find({"status": "active", "roles": user_role})  # Reserved lots
            open_lots = ParkingLot.find({"status": "active", "roles": {"$in": ["open"]}})  # Open lots


            return render_template(
                'student/dashboard.html',
                email=session['email'],
                permits=list(permits),
                reserved_lots=list(reserved_lots),  # Pass reserved lots to the template
                open_lots=list(open_lots),  # Pass open lots to the template
                user_role=user_role
            )

    flash("Unauthorized access!", "error")
    return redirect(url_for('sso_login'))


from flask import jsonify

@app.route('/set_selected_permit', methods=['POST'])
def set_selected_permit():
    data = request.get_json()
    permit_id = data.get('permit_id')

    if not permit_id:
        return jsonify({"success": False, "message": "Permit ID is missing."}), 400

    # Store the selected permit ID in the session
    session['selected_permit'] = permit_id

    return jsonify({"success": True, "message": "Selected permit set in session."})

# Faculty Dashboard
@app.route('/faculty_dashboard')
def faculty_dashboard():
    if "user_id" in session and session.get("role") == "faculty":
        permits = Permit.find({"status": "active"})  
        return render_template('student/dashboard.html', email=session['email'], permits=list(permits))
    flash("Unauthorized access!", "error")
    return redirect(url_for('sso_login'))


@app.route('/police_dashboard')
@login_required
def police_dashboard():
    print(session)
    # Fetch all active parking lots from the database
    lots = ParkingLot.get_all_filtered({"status": "active"})
    
    # Convert the cursor to a list of dictionaries for easy rendering in the template
    lots = list(lots)

    # Render the dashboard template
    return render_template('police/dashboard.html', lots=lots)





















@app.route('/select_other_info', methods=['GET', 'POST'])
@login_required
def select_other_info():
    user_id = session.get('user_id')
    user = User.find_one({"_id": ObjectId(user_id)})

    # Retrieve vehicle and permit details from the session
    selected_vehicle_id = session.get('selected_vehicle')
    selected_permit_id = session.get('selected_permit')

    vehicle = Car.find_one({"_id": ObjectId(selected_vehicle_id)}) if selected_vehicle_id else None
    permit = Permit.find_one({"_id": ObjectId(selected_permit_id)}) if selected_permit_id else None

    if request.method == 'POST':
        # Validate the delivery option and email selection
        delivery_option = request.form.get('delivery_option')
        selected_email = request.form.get('email')

        if not delivery_option or not selected_email:
            flash("All fields are required.", "error")
            return redirect(url_for('select_other_info'))

        # Handle dynamically added addresses
        new_address = request.form.get('new_address')
        if new_address:
            User.update_one({"_id": ObjectId(user_id)}, {"$push": {"addresses": new_address}})

        # Handle dynamically added emails
        new_email = request.form.get('new_email')
        if new_email:
            User.update_one({"_id": ObjectId(user_id)}, {"$push": {"emails": new_email}})

        # Save delivery option and email selection in session
        session['delivery_option'] = delivery_option
        session['selected_email'] = selected_email

        return redirect(url_for('cart'))

    # Fetch pre-existing addresses
    addresses = [
        f"{user.get('address_1', '')}, {user.get('address_2', '')}, {user.get('city', '')}, {user.get('zipcode', '')}".strip(", ")
    ]
    emails = [user.get("email", ""), user.get("alternative_email", "")]

    return render_template(
        'student/select_other_info.html',
        vehicle=vehicle,
        permit=permit,
        addresses=addresses,
        emails=emails
    )


@app.route('/check_availability', methods=['GET'])
@login_required
def check_availability():
    user_role = session.get("role")
    if not user_role:
        return jsonify({"success": False, "message": "User role not found"}), 400

    # Calculate availability for the user's role
    lots = ParkingLot.find({"roles": user_role})
    total_capacity = sum(lot.get("total_capacity", 0) for lot in lots)
    print("line 172", total_capacity)
    booked_count = Booking.count_documents({"permit_details.type": "Reserved Permit", "user_role": user_role})
    print("line 174", booked_count)
    available_slots = total_capacity - booked_count
    print("line 176", available_slots)
    return jsonify({
        "success": True,
        "total_capacity": total_capacity,
        "booked_count": booked_count,
        "available_slots": available_slots
    })



@app.route('/additional_info', methods=['GET', 'POST'])
@login_required
def additional_info():
    user_id = session.get('user_id')
    user = User.find_one({"_id": ObjectId(user_id)})

    if request.method == 'POST':
        # Handle delivery option or email selection
        delivery_option = request.form.get('delivery_option')
        selected_email = request.form.get('email')
        
        # Handle address addition
        new_address = request.form.get('new_address')
        if new_address:
            User.update_one({"_id": ObjectId(user_id)}, {"$push": {"addresses": new_address}})
            flash("Address added successfully.", "success")
            return redirect(url_for('additional_info'))

        # Handle email addition
        new_email = request.form.get('new_email')
        if new_email:
            User.update_one({"_id": ObjectId(user_id)}, {"$push": {"emails": new_email}})
            flash("Email added successfully.", "success")
            return redirect(url_for('additional_info'))

        # If all inputs are valid, redirect to the next step
        if delivery_option and selected_email:
            session['delivery_option'] = delivery_option
            session['selected_email'] = selected_email
            return redirect(url_for('next_step'))  # Replace 'next_step' with the actual route

        flash("Please complete all required fields.", "error")

    addresses = user.get("addresses", [])
    emails = user.get("emails", [])
    return render_template('additional_info.html', addresses=addresses, emails=emails)



from app.models.booking import Booking
@app.route('/my_permits', methods=['GET'])
@login_required
def my_permits():
    user_id = session.get('user_id')
    if not user_id:
        flash("User not logged in.", "error")
        return redirect(url_for('login'))

    # Fetch permits from the booking collection
    permits_cursor = Booking.find({"user_id": user_id})
    permits = list(permits_cursor)  # Convert Cursor to List
    return render_template('student/my_permits.html', permits=permits)


@app.route('/my_citations', methods=['GET'])
@login_required
def my_citations():
    # Ensure the user is logged in and has the correct role
    user_id = session.get('user_id')
    role = session.get('role')

    if role not in ['student', 'faculty']:
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    # Fetch user's cars
    cars = list(Car.collection.find({"user_id": ObjectId(user_id)}))
    car_plates = [car['number_plate'] for car in cars]

    # Fetch citations for user's cars
    citations = list(Citation.collection.find({"vehicle_plate": {"$in": car_plates}}))

    return render_template('student/my_citations.html', citations=citations)






from app.models.booking import Booking
from app.models.parking_lot import ParkingLot
from app.models.citation import Citation
@app.route('/search_citations', methods=['GET'])
def search_citations():
    # Retrieve search parameters
    citation_number = request.args.get('citation_number', '').strip()
    plate_number = request.args.get('plate_number', '').strip()
    state = request.args.get('state', '').strip()
    print(citation_number, plate_number, state)
    # Build MongoDB query
    query = {}
    if citation_number:
        query["citation_number"] = citation_number  # Match citation_number directly
    if plate_number:
        query["vehicle_plate"] = {"$regex": plate_number, "$options": "i"}

    print(query)
    # Fetch matching citation records
    citations = list(Citation.collection.find(query))
    print(citations)
    # If citation exists, fetch car details using vehicle_plate
    results = []
    for citation in citations:
        vehicle_plate = citation.get("vehicle_plate")
        if vehicle_plate:
            car = Car.collection.find_one({"number_plate": vehicle_plate})
            print("car", car)
            if car:
                results.append({
                    "citation_number": citation.get("citation_number"),
                    "violation": citation.get("violation"),
                    "fine_amount": citation.get("fine_amount"),
                    "issued_at": citation.get("issued_at"),
                    "vehicle_plate": vehicle_plate,
                    "car_details": {
                        "make": car.get("make"),
                        "model": car.get("model"),
                        "color": car.get("color"),
                        "year": car.get("year"),
                        "state": car.get("state"),
                        "style": car.get("style"),
                    }
                })
            else:
                results.append({
                    "citation_number": citation.get("citation_number"),
                    "violation": citation.get("violation"),
                    "fine_amount": citation.get("fine_amount"),
                    "issued_at": citation.get("issued_at"),
                    "vehicle_plate": vehicle_plate,
                    "car_details": None
                })
            print("results", results)
    return jsonify(results)
