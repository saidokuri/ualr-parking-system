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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@app.route('/add_permit', methods=['POST'])
@login_required
def add_permit():
    permit_name = request.form.get("permit_name")
    fee = request.form.get("fee")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    new_permit = {
        "permit_name": permit_name,
        "fee": fee,
        "start_date": start_date,
        "end_date": end_date,
        "created_at": datetime.now(),
        "status": "active"
    }
    Permit.insert_one(new_permit)  # Insert into the database
    flash("Permit added successfully!", "success")
    return redirect(url_for('manage_permits'))

@app.route('/toggle_status/<permit_id>', methods=['POST'])
@login_required
def toggle_status(permit_id):
    permit = Permit.find_one({"_id": ObjectId(permit_id)})
    if permit:
        new_status = "inactive" if permit["status"] == "active" else "active"
        Permit.update_one({"_id": ObjectId(permit_id)}, {"$set": {"status": new_status}})
        flash(f"Permit status updated to {new_status}!", "success")
    else:
        flash("Permit not found!", "error")
    return redirect(url_for('manage_permits'))



@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    
    return render_template('admin/dashboard.html')



@app.route('/manage_permits')
@login_required
def manage_permits():
    permits = Permit.get_all()
    permits = list(permits)
    return render_template('admin/manage_permits.html', permits=permits)


@app.route('/manage_parking_lots', methods=['GET'])
@login_required
def manage_parking_lots():
    # Fetch query parameters for pagination and search
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    search_query = request.args.get('query', '').strip()

    # Search and filter logic
    parking_lots_query = {}
    if search_query:
        parking_lots_query = {"lot_name": {"$regex": search_query, "$options": "i"}}

    # Fetch filtered and paginated parking lots
    total_records = ParkingLot.count(parking_lots_query)  # Replace with actual count logic
    parking_lots = ParkingLot.get_all_filtered(
        parking_lots_query, skip=(page - 1) * limit, limit=limit
    )  # Replace with actual filtered query logic

    # Fetch all permits
    permits = Permit.get_all()  # Replace with actual database query

    # Calculate pagination details
    total_pages = (total_records + limit - 1) // limit
    pagination = {
        "current_page": page,
        "total_pages": total_pages,
        "total_records": total_records,
    }

    return render_template(
        'admin/manage_parking_lots.html',
        parking_lots=list(parking_lots),
        permits=list(permits),
        pagination=pagination,
        search_query=search_query,
    )

@app.route('/add_parking_lot', methods=['POST'])
@login_required
def add_parking_lot():
    try:
        lot_name = request.form.get("lot_name")
        total_capacity = int(request.form.get("total_capacity"))
        handicapped_slots = int(request.form.get("handicapped_slots"))
        normal_slots = int(request.form.get("normal_slots"))
        permit_id = request.form.get("permit_id")  # Fetch the selected permit ID
        roles = request.form.getlist("roles")  # Fetch the selected roles as a list

        # Validate slot counts
        if handicapped_slots + normal_slots != total_capacity:
            flash("Total capacity must match the sum of handicapped and normal slots.", "error")
            return redirect(url_for('manage_parking_lots'))

        # Insert new parking lot into the database
        new_lot = {
            "lot_name": lot_name,
            "total_capacity": total_capacity,
            "handicapped_slots": handicapped_slots,
            "normal_slots": normal_slots,
            "permit_id": ObjectId(permit_id),
            "roles": roles,  # Save roles as an array
            "created_at": datetime.now(),
            "status": "active"
        }
        ParkingLot.insert_one(new_lot)  # Replace with actual database insertion method
        flash("Parking lot added successfully!", "success")
    except Exception as e:
        flash(f"Error adding parking lot: {str(e)}", "error")
    return redirect(url_for('manage_parking_lots'))




@app.route('/toggle_lot_status/<lot_id>', methods=['POST'])
@login_required
def toggle_lot_status(lot_id):
    try:
        # Fetch the parking lot by its ID
        lot = ParkingLot.find_one({"_id": ObjectId(lot_id)})  # Replace with actual query
        if not lot:
            flash("Parking lot not found.", "error")
            return redirect(url_for('manage_parking_lots'))

        # Toggle the status
        new_status = "inactive" if lot.get("status") == "active" else "active"
        ParkingLot.update_one({"_id": ObjectId(lot_id)}, {"$set": {"status": new_status}})  # Replace with actual update method

        flash(f"Parking lot status updated to {new_status}.", "success")
    except Exception as e:
        flash(f"Error updating parking lot status: {str(e)}", "error")
    return redirect(url_for('manage_parking_lots'))

@app.route('/view_faculties')
@login_required
def view_faculties():
    faculties = User.get_all_faculties_with_permits()
    faculties = list(faculties)
    return render_template('admin/view_teachers.html', faculties=faculties)


@app.route('/view_students')
@login_required
def view_students():
    students = User.get_all_students_with_permits()
    students = list(students)
    return render_template('admin/view_students.html', students=students)


@app.route('/view_police')
@login_required
def view_police():
    police = User.get_all_police()
    police = list(police)
    print(police)
    return render_template('admin/view_police.html', police=police)


@app.route('/view_sodexo')
@login_required
def view_sodexo():
    sodexo = User.get_all_sodexo_with_permits()
    sodexo = list(sodexo)
    return render_template('admin/view_sodexo.html', sodexo=sodexo)




@app.route('/view_guests')
@login_required
def view_guests():
    return "Guests Page"

@app.route('/view_payments')
@login_required
def view_payments():
    return "Payments Page"




@app.route('/lot_details/<string:lot_id>')
@login_required
def lot_details(lot_id):
    # Fetch the lot details
    lot = ParkingLot.find_one({"_id": ObjectId(lot_id)})

    if not lot:
        flash("Parking lot not found.", "error")
        return redirect(url_for('police_dashboard'))

    # Fetch the associated permit details
    permit = Permit.find_one({"_id": ObjectId(lot['permit_id'])}) if lot.get('permit_id') else None

    return render_template('police/lot_details.html', lot=lot, permit=permit)


from app.models.citation import Citation
@app.route('/submit_citation/<string:lot_id>', methods=['POST'])
@login_required
def submit_citation(lot_id):
    # Get form data
    # Get form data
    vehicle_plate = request.form.get('vehicle_plate')
    violation = request.form.get('violation')

    # Validate inputs
    if not vehicle_plate or not violation:
        flash("Both vehicle plate and violation are required.", "error")
        return redirect(url_for('lot_details', lot_id=lot_id))

    # Generate citation_number
    try:
        # Fetch the lot name for the lot_id
        lot = ParkingLot.find_one({"_id": ObjectId(lot_id)})
        if not lot:
            flash("Invalid lot ID.", "error")
            return redirect(url_for('lot_details', lot_id=lot_id))
        lot_name = lot.get('lot_name', 'UNKNOWN')

        # Extract parts for citation_number format
        vehicle_prefix = vehicle_plate[:2].upper()  # First 2 characters of the vehicle plate
        lot_prefix = lot_name.replace("LOT", "").zfill(2)  # Extract numeric part of the lot, e.g., LOT12 -> 12
        issued_at_prefix = datetime.utcnow().strftime('%d')  # Use the day of the month for the issued_at part

        # Count the existing citations for the lot and vehicle to determine the increment
        existing_citations_count = Citation.collection.count_documents({
            "lot_id": ObjectId(lot_id),
            "vehicle_plate": vehicle_plate
        })

        increment = existing_citations_count + 1  # Increment for this vehicle in this lot

        # Format citation_number
        citation_number = f"CIT{vehicle_prefix}{lot_prefix}{issued_at_prefix}{str(increment).zfill(2)}"

    except Exception as e:
        flash(f"Error generating citation number: {str(e)}", "error")
        return redirect(url_for('lot_details', lot_id=lot_id))

    # Create citation entry
    citation = {
        "lot_id": ObjectId(lot_id),
        "vehicle_plate": vehicle_plate,
        "violation": violation,
        "fine_amount": 50,  # Assuming a fixed fine amount
        "issued_at": datetime.utcnow(),
        "citation_number": citation_number
    }

    # Insert into Citation collection
    Citation.insert_one(citation)

    flash(f"Citation submitted successfully. Citation Number: {citation_number}", "success")
    return redirect(url_for('lot_details', lot_id=lot_id))






@app.route('/view_all_citations', methods=['GET'])
@login_required
def view_all_citations():
    if session.get('role') != 'police':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    search_query = request.args.get('search_query', '').strip()
    query = {}

    # If there's a search query, filter citations by vehicle_plate or violation
    if search_query:
        query = {
            "$or": [
                {"vehicle_plate": {"$regex": search_query, "$options": "i"}},
                {"violation": {"$regex": search_query, "$options": "i"}}
            ]
        }

    # Fetch citations from the database
    citations = list(Citation.collection.find(query))

    return render_template('police/view_all_citations.html', citations=citations)
