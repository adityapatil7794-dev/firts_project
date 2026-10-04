import requests

url = "https://dummyjson.com/products?limit=194"

response = requests.get(url)

print(response.status_code)
data = response.json()
print(type(data))
print(data.keys())

print(type(data))
print(data.keys())

print("Total:", data["total"])
print("Skip:", data["skip"])
print("Limit:", data["limit"])

products = data["products"]

clean_products = []

for product in products:
    clean_product = {
        "id": product["id"],
        "title": product["title"],
        "category": product["category"],
        "price": product["price"],
        "discountPercentage": product["discountPercentage"],
        "rating": product["rating"],
        "stock": product["stock"],
        "brand": product.get("brand", "Unknown"),
        "availabilityStatus": product["availabilityStatus"]
    }

    clean_products.append(clean_product)

print(len(clean_products))
print(clean_products[0])


ids = [product["id"] for product in clean_products]

print("Total IDs:", len(ids))
print("Unique IDs:", len(set(ids)))

invalid_prices = [
    product for product in clean_products
    if product["price"] < 0
]

print("Invalid prices:", len(invalid_prices))

missing_values = []

for product in clean_products:
    if not product["title"] or not product["category"]:
        missing_values.append(product)

print("Products with missing title or category:", len(missing_values))

invalid_ratings = [
    product for product in clean_products
    if product["rating"] < 0 or product["rating"] > 5
]

print("Invalid ratings:", len(invalid_ratings))

invalid_stock = [
    product for product in clean_products
    if product["stock"] < 0
]

print("Invalid stock quantities:", len(invalid_stock))

if len(clean_products) == data["total"]:
    print("Product count validation: PASSED")
else:
    print("Product count validation: FAILED")