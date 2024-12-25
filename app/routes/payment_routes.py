from flask import render_template, request, redirect, url_for, session, flash
from app import app
from app.models.user import User 
from .decorators import login_required
import logging
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from app.models.car import Car
from app.models.permit import Permit
from app.models.payment import Payment
from app.models.booking import Booking
from flask import jsonify
import qrcode
from io import BytesIO
from flask import send_file
import barcode
import os
from datetime import datetime
from barcode.writer import ImageWriter

from barcode import Code128


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    user_id = session.get('user_id')
    user = User.find_one({"_id": ObjectId(user_id)})
    selected_vehicle_id = session.get('selected_vehicle')
    selected_permit_id = session.get('selected_permit')

    # Fetch selected vehicle details
    selected_vehicle = Car.find_one({"_id": ObjectId(selected_vehicle_id)}) if selected_vehicle_id else None

    # Fetch selected permit details
    permit = Permit.find_one({"_id": ObjectId(selected_permit_id)}) if selected_permit_id else None

    if not permit or not selected_vehicle:
        flash("Permit or Vehicle details are missing.", "error")
        return redirect(url_for('select_vehicle'))

    # Generate dynamic permit code
    permit_type_code = 'R' if permit.get('permit_name') == 'Reserved Permit' else 'C'
    expiry_year = permit.get('end_date', '')[:4]  # Extract year from end_date
    t_number_suffix = user.get('t_number', '')[1:]  # Remove 'T' from t_number
    vehicle_number = selected_vehicle.get('number_plate', '').replace(" ", "")  # Remove spaces from number plate
    permit_code = f"{permit_type_code}{expiry_year}{t_number_suffix}"

    # Prepare cart items
    cart_items = [
        {
            "type": permit.get('permit_name', 'Permit'),
            "description": f"{permit.get('permit_name')} [{permit_code}] ({permit.get('start_date')} - {permit.get('end_date')})",
            "amount": float(permit.get('fee', 0)),
            "qty": 1,
            "valid_dates": f"{permit.get('start_date')} - {permit.get('end_date')}",
            "address": f"{user.get('address_1', '')}, {user.get('address_2', '')}, {user.get('city', '')}, {user.get('zipcode', '')}",
            "vehicle_details": f"{selected_vehicle.get('number_plate')}, {selected_vehicle.get('year')}, {selected_vehicle.get('make')}"
        }
    ]

    temp_tag_note = "A temporary tag will be provided after the payment which you can use until the permanent tag arrives."

    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        if not payment_method:
            flash("Please select a payment method.", "error")
            return redirect(url_for('cart'))
        
        # Save payment details to session
        session['payment_method'] = payment_method
        session['cart_items'] = cart_items

        # Save booking to the database
        booking_data = {
            "user_id": user_id,
            "t_number": user.get("t_number"),
            "car_id": selected_vehicle_id,
            "permit_id": selected_permit_id,
            "start_date": permit.get("start_date"),
            "end_date": permit.get("end_date"),
            "paid_amount": float(permit.get("fee", 0)),
            "role": user.get("role"),
            "payment_method": payment_method,
            "address": f"{user.get('address_1', '')}, {user.get('address_2', '')}, {user.get('city', '')}, {user.get('zipcode', '')}",
            "vehicle_details": {
                "number_plate": selected_vehicle.get("number_plate"),
                "year": selected_vehicle.get("year"),
                "make": selected_vehicle.get("make"),
                "model": selected_vehicle.get("model"),
                "color": selected_vehicle.get("color"),
            },
            "permit_details": {
                "type": permit.get("permit_name"),
                "code": permit_code,
                "valid_dates": f"{permit.get('start_date')} - {permit.get('end_date')}"
            },
            "created_at": datetime.now()
        }

        # Insert the booking into the Booking collection
        Booking.insert_one(booking_data)

        flash("Checkout successful! Your booking has been confirmed.", "success")
        return redirect(url_for('confirmation'))

    return render_template('student/cart.html', cart_items=cart_items, temp_tag_note=temp_tag_note)



from PIL import Image, ImageDraw, ImageFont
from barcode import Code128
from barcode.writer import ImageWriter
import os
import uuid
def generate_parking_permit_barcode(data, permit_type, expiration_date, user_id, card_id):
    print("Generating parking permit barcode...")
    print(f"Data: {data}")
    print(f"Permit Type: {permit_type}")
    print(f"Expiration Date: {expiration_date}")
    print(f"User ID: {user_id}")
    print(f"Card ID: {card_id}")

    """
    Generate a parking permit with a barcode, university name banner, permit type, and expiration date.
    
    Args:
    - data (str): Barcode data to encode.
    - permit_type (str): Type of permit (e.g., "Commuter").
    - expiration_date (str): Expiration date for the permit.
    - user_id (str): The user ID for generating the filename.
    - card_id (str): The vehicle/card ID for generating the filename.
    
    Returns:    
    - str: Path to the generated image.
    """
    try:
        # Generate the filename
        filename = f"permit_card_{user_id}_{card_id}.png"

        # Generate the barcode
        abs_path = os.path.join(os.getcwd(), 'static', 'permits')
        os.makedirs(abs_path, exist_ok=True)  # Ensure the directory exists
        barcode_path = os.path.join(abs_path, filename)

        # Generate the barcode and save it
        barcode_instance = Code128(data, writer=ImageWriter())
        barcode_instance.save(barcode_path)

        # Open the barcode image
        barcode_image = Image.open(f"{barcode_path}.png")
        barcode_width, barcode_height = barcode_image.size

        # Create a new image with space for the banner, permit details, and expiration date
        canvas_height = barcode_height + 250  # Add space for text and banner
        canvas_width = barcode_width + 150  # Add padding for width
        canvas = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))  # White background
        draw = ImageDraw.Draw(canvas)

        # Colors
        maroon = (110, 38, 57)
        white = (255, 255, 255)
        black = (0, 0, 0)

        # Fonts
        try:
            banner_font = ImageFont.truetype("arial.ttf", 40)
            text_font = ImageFont.truetype("arial.ttf", 30)
            small_text_font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            banner_font = text_font = small_text_font = ImageFont.load_default()

        # Add the maroon banner at the top
        banner_height = 60
        draw.rectangle([(0, 0), (canvas_width, banner_height)], fill=maroon)

        # Add university name in the banner
        university_name = "UA LITTLE ROCK"
        text_bbox = draw.textbbox((0, 0), university_name, font=banner_font)
        text_width = text_bbox[2] - text_bbox[0]
        draw.text(((canvas_width - text_width) / 2, (banner_height - text_bbox[3]) / 2), university_name, fill=white, font=banner_font)

        # Add permit type below the banner
        permit_text = f"{permit_type} Parking Permit"
        text_bbox = draw.textbbox((0, 0), permit_text, font=text_font)
        text_width = text_bbox[2] - text_bbox[0]
        draw.text(((canvas_width - text_width) / 2, banner_height + 20), permit_text, fill=maroon, font=text_font)

        # Paste the barcode below the permit type
        canvas.paste(barcode_image, ((canvas_width - barcode_width) // 2, banner_height + 80))

        # Add expiration date below the barcode
        expiration_text = f"Expires {expiration_date}"
        text_bbox = draw.textbbox((0, 0), expiration_text, font=small_text_font)
        text_width = text_bbox[2] - text_bbox[0]
        draw.text(((canvas_width - text_width) / 2, banner_height + 80 + barcode_height + 20), expiration_text, fill=black, font=small_text_font)

        # Save the final image with the generated filename
        canvas.save(barcode_path)
        print(f"Permit card saved to: {barcode_path}")
        return barcode_path
    except Exception as e:
        raise ValueError(f"Error generating parking permit: {e}")






@app.route('/download_permit')
@login_required
def download_permit():
    user_id = session.get('user_id')
    selected_vehicle_id = session.get('selected_vehicle')

    # Fetch additional details
    selected_vehicle = Car.find_one({"_id": ObjectId(selected_vehicle_id)}) if selected_vehicle_id else None
    if not user_id or not selected_vehicle:
        flash("Permit card cannot be downloaded. Missing required information.", "error")
        return redirect(url_for('confirmation'))

    # Generate filename with updated pattern
    car_id = selected_vehicle.get('_id', 'unknown')
    permit_card_filename = f"permit_card_{user_id}_{car_id}.png"
    print(f"Permit card filename: {permit_card_filename}")

    # Use absolute path for the permit file
    permit_path = os.path.join(os.getcwd(), "static", "permits", permit_card_filename)
    print(f"Permit path: {permit_path}")

    # Check if the file exists
    if not os.path.exists(permit_path):
        flash("No permit card available for download.", "error")
        return redirect(url_for('confirmation'))

    return send_file(permit_path, as_attachment=True, download_name=permit_card_filename)


@app.route('/confirmation', methods=['GET'])
@login_required
def confirmation():
    # Retrieve session details
    user_id = session.get('user_id')
    selected_vehicle_id = session.get('selected_vehicle')
    selected_permit_id = session.get('selected_permit')
    payment_method = session.get('payment_method', 'Unknown')
    delivery_option = session.get('delivery_option', 'Standard')
    selected_email = session.get('selected_email', 'Not Provided')

    # Validate session data
    if not (user_id and selected_vehicle_id and selected_permit_id):
        flash("Some details are missing. Please start over.", "error")
        return redirect(url_for('confirmation'))

    # Fetch additional details
    user = User.find_one({"_id": ObjectId(user_id)})
    selected_vehicle = Car.find_one({"_id": ObjectId(selected_vehicle_id)})
    permit = Permit.find_one({"_id": ObjectId(selected_permit_id)})

    if not (user and selected_vehicle and permit):
        flash("Invalid data. Please try again.", "error")
        return redirect(url_for('confirmation'))

    # Generate filename for the permit card
    car_id = selected_vehicle.get('_id', 'unknown')
    permit_card_filename = f"permit_card_{user_id}_{car_id}.png"
    permit_card_path = os.path.join(os.getcwd(), "static", "permits", permit_card_filename)
    
    # Generate permit code
    permit_type_code = 'R' if permit.get('permit_name', 'unknown') == 'Reserved Permit' else 'C'
    expiry_year = permit.get('end_date', 'unknown')[:4]  # Extract the year from end_date
    t_number_suffix = user.get('t_number', 'unknown')[1:]  # Remove the 'T' prefix from the t_number
    permit_code = f"{permit_type_code}{expiry_year}{t_number_suffix}"




    # Check if permit card already exists
    if os.path.exists(permit_card_path):
        print(f"Permit card already exists at {permit_card_path}. Overwriting...")
    
    generate_parking_permit_barcode(
            data=permit_code,
            permit_type=permit.get('permit_name', 'Unknown'),
            expiration_date=permit.get('end_date', 'N/A'),
            user_id=user_id,
            card_id=car_id
        )
    print("Permit card generated successfully.")
    print(permit_card_path)

    # Prepare cart items
    cart_items = [
        {
            "qty": 1,
            "type": permit.get('permit_name', 'Permit'),
            "description": f"{permit.get('permit_name')} [{permit.get('permit_code')}] ({permit.get('start_date')} - {permit.get('end_date')})",
            "amount": float(permit.get('fee', 0)),
            "valid_dates": f"{permit.get('start_date')} - {permit.get('end_date')}",
            "address": f"{user.get('address_1', '')}, {user.get('address_2', '')}, {user.get('city', '')}, {user.get('zipcode', '')}",
            "vehicle_details": f"{selected_vehicle.get('number_plate', 'N/A')}, {selected_vehicle.get('year', 'N/A')}, {selected_vehicle.get('make', 'N/A')}"
        }
    ]

    # Render confirmation template
    return render_template(
        'student/confirmation.html',
        cart_items=cart_items,
        payment_method=payment_method,
        delivery_option=delivery_option,
        selected_email=selected_email,
        permit_card_filename=permit_card_filename
    )
