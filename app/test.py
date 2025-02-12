import requests

def get_calories(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={product_name}&search_simple=1&json=1"
    response = requests.get(url)
    data = response.json()

    # Проверка на наличие продуктов в ответе
    if 'products' in data and data['products']:
        product = data['products'][0]  # Берём первый продукт из списка
        calories = product.get('nutriments', {}).get('energy-kcal', 'Неизвестно')
        return calories
    return "Продукт не найден"

product_name = "слива"  # Пример названия продукта
print(get_calories(product_name))