from faker import Faker
import random
import json

# Initialize Faker with locale for USA
fake = Faker('en_US')

# Custom Roles Distribution
role_distribution = {
    'student': 60,
    'faculty': 20,
    'staff': 10,
    'police': 5,
    'sodexo': 5
}

# Function to generate a single user
def generate_mock_user(index, role):
    first_name = fake.first_name()
    last_name = fake.last_name()
    date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=65)
    year_of_birth = date_of_birth.year

    return {
        "t_number": f"T{10000 + index}",  # Incrementing t_number
        "first_name": first_name,
        "last_name": last_name,
        "email": f"{first_name[0].lower()}{last_name.lower()}@abc.edu",  # Primary email
        "gender": random.choice(["Male", "Female", "Other"]),  # Restrict gender choices
        "role": role,
        "date_of_birth": date_of_birth.strftime('%m/%d/%Y'),
        "address_1": fake.street_address(),
        "address_2": fake.secondary_address(),
        "city": fake.city(),
        "zipcode": fake.zipcode(),  # US zip code
        "phone_number": fake.phone_number(),
        "alternative_email": f"{first_name.lower()}{last_name.lower()}{year_of_birth}@testmail.com",  # Alternative email
        "password": fake.password(length=8, upper_case=True, lower_case=True, digits=True, special_chars=True)
    }

# Function to generate data with role distribution
def generate_mock_data():
    users = []
    index = 0
    
    # Generate users based on role distribution
    for role, count in role_distribution.items():
        for _ in range(count):
            users.append(generate_mock_user(index, role))
            index += 1
    
    # Save to a JSON file
    with open("mock_users.json", "w") as file:
        json.dump(users, file, indent=4)
    
    print(f"100 mock records saved to 'mock_users.json' with specific role distribution.")

# Generate the records
if __name__ == "__main__":
    generate_mock_data()
