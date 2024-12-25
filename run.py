from app import app
from app.routes import  admin_routes, user_routes, auth_routes, car_routes, payment_routes, default_routes

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5001, debug=True)

