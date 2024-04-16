import io
import tkinter as tk
from tkinter import messagebox
from math import radians, sin, cos, sqrt, atan2
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import time

API_KEY = open('API_KEY.txt', 'r').read()
default_image = mpimg.imread('noimage.jpg')
value = [] 
chosen_rest_lat = 0.0 
chosen_rest_lng = 0.0
nearby = []


food_types = [
    'restaurant',
    'cafe',
    'bar',
    'bakery',
    'meal_takeaway',
    'meal_delivery'
]

price_level_map = {'0': 'Безкоштовно', '1': 'Низький', '2': 'Середній', '3': 'Високий', '4': 'Дуже високий'}

def calculate_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    radius_earth_km = 6371.0

    distance = radius_earth_km * c

    return distance

def download_image(photo_reference, max_width=400):
    base_url = 'https://maps.googleapis.com/maps/api/place/photo'
    params = {
        'maxwidth': max_width,
        'photoreference': photo_reference,
        'key': API_KEY
    }
    response = requests.get(base_url, params=params)
    img = plt.imread(io.BytesIO(response.content), format='jpg')
    return img

def get_delivery_time(origin, destination, mode='driving'):
    directions_url = 'https://maps.googleapis.com/maps/api/directions/json'
    directions_params = {
        'origin': origin,
        'destination': destination,
        'mode': mode,
        'language': 'uk',
        'key': API_KEY
    }
    response = requests.get(directions_url, params=directions_params)
    data = response.json()

    if data['status'] == 'OK':
        route = data['routes'][0]
        leg = route['legs'][0]
        duration = leg['duration']['text']
        return duration
    else:
        print(f"Не вдалося отримати маршрут: {data['status']}")
        return None
    
def get_route_image(origin, destination, mode='walking'):
    directions_url = 'https://maps.googleapis.com/maps/api/directions/json'
    directions_params = {
        'origin': origin,
        'destination': destination,
        'mode': mode,
        'language': 'uk',
        'key': API_KEY
    }

    response = requests.get(directions_url, params=directions_params)
    data = response.json()

    if data['status'] == 'OK':
        route = data['routes'][0]
        leg = route['legs'][0]
        duration = leg['duration']['text']
    
        polyline = route['overview_polyline']['points']

        static_maps_url = 'https://maps.googleapis.com/maps/api/staticmap'

        static_maps_params = {
            'size': '640x640',  
            'maptype': 'roadmap', 
            'path': f'color:blue|enc:{polyline}',
            'key': API_KEY,
            'language': 'uk',
            'markers': f'color:red|{origin}|{destination}', 
        }

        map_response = requests.get(static_maps_url, params=static_maps_params)
        
        if map_response.status_code == 200:
            image = Image.open(io.BytesIO(map_response.content))
            return image, duration
            
        else:
            print(f"Не вдалося завантажити зображення карти: {map_response.status_code}")
            return None, None
    else:
        print(f"Не вдалося отримати маршрут: {data['status']}")
        return None, None

def display_places_info(places, details, delivery, routes):
    current_index = 0
    fig, axes = plt.subplots(2, 2, figsize=(12, 6))

    ax_image, ax_info = axes[0]  # Перший рядок з двома підграфіками
    ax_bottom, ax_info2 = axes[1]   # Другий рядок з двома підграфіками
    

    def update_places_info_display():
        ax_info.clear()
        ax_info2.clear()
        ax_image.clear()
        ax_bottom.clear()

        if places[current_index].get('photo') is not None:
            ax_image.imshow(places[current_index]['photo'])
        else:
            ax_image.imshow(default_image)
        ax_image.axis('off')

        info_text = f"Назва: {places[current_index]['name']}\n"
        info_text += f"Адреса: {places[current_index]['vicinity']}\n"
        info_text += f"Рейтинг: {places[current_index].get('rating', '----------')}\n"
        if 'opening_hours' in details[current_index]:
            info_text += f"Години: {"Відчинено" if details[current_index]['opening_hours']['open_now'] else "Зачинено"}\n"
        opening_hours = details[current_index].get('opening_hours')
        if opening_hours and 'weekday_text' in opening_hours:
            for line in opening_hours['weekday_text']:
                info_text+= line + "\n"
        else:
            info_text += "Години роботи не доступні.\n"
        
        info_text2 = ""
        if 'website' in details[current_index]:
            info_text2 += f"Веб-сайт: {details[current_index]['website'][:50]}\n"
        if 'formatted_phone_number' in details[current_index]:
            info_text2 += f"Телефон: {details[current_index]['formatted_phone_number']}\n"
        if 'price_level' in details[current_index]:
             info_text2 += f"Ціновий рівень: {price_level_map.get(str(details[current_index]['price_level']), '------')}\n"
        
       
        if delivery[current_index]:
            info_text2 += f"Час доставки(без приготування): {delivery[current_index]}\n"
        else:
            info_text2 += f"Час доставки(без приготування): -------- \n"
        img, dur = routes[current_index]
        if dur is not None:
            info_text2 += f"Час пішки: {dur}\n"
        else:
            info_text2 += f"Час пішки: -------- \n"
        if img is None:
            img = default_image

        ax_bottom.imshow(img)
        ax_bottom.axis('off')
        

        ax_info.text(0.5, 0.9, info_text, ha='center', va='top', fontsize=12)
        ax_info2.text(0.5, 0.9, info_text2, ha='center', va='top', fontsize=12)
        ax_info.axis('off')
        ax_info2.axis('off')
        plt.draw()
    
    update_places_info_display()

    def on_next_clicked(event):
        nonlocal current_index
        current_index = (current_index + 1) % len(places)
        update_places_info_display()
        

    def on_prev_clicked(event):
        nonlocal current_index
        current_index = (current_index - 1) % len(places)
        update_places_info_display()

    axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
    axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
    bprev = plt.Button(axprev, 'Попереднє')
    bprev.on_clicked(on_prev_clicked)
    bnext = plt.Button(axnext, 'Наступне')
    bnext.on_clicked(on_next_clicked)

    plt.show()

def get_location():  
    url = f'https://www.googleapis.com/geolocation/v1/geolocate?key={API_KEY}'
    response = requests.post(url)
    
    if response.status_code == 200:
        data = response.json()

       
        lat = data['location']['lat']
        long = data['location']['lng']

        return lat, long
        
    else:
        return "Failed to make the request."

def find_nearbyrest(lat, lon):

    base_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'

    radius = 500
    data = None
    all_results = {}
    while radius < 3000 and len(all_results) < 5:
        radius = radius + 500

        for food_type in food_types:
            params = {
                'location': f'{lat},{lon}', 
                'radius': radius,
                'type': food_type, 
                'language': 'uk',
                'key': API_KEY
            }
            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'OK':
               
                    for place in data['results']:
                        place_id = place['place_id']
                        if place_id not in all_results:
                            all_results[place_id] = place                
            else:
                print(f"Помилка запиту для типу {food_type}: {response.status_code}")
    
    
    results = list(all_results.values())
    sorted_results = sorted(results, key=lambda place: calculate_distance(lat, lon, place['geometry']['location']['lat'], place['geometry']['location']['lng']))

    closest_5 = sorted_results[:5]   
    
    return closest_5


def get_dist_dur(start, end):
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    params = {
        "origins": start,
        "destinations": end,
        "key": API_KEY
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()

        if data["status"] == "OK":
            distance = data["rows"][0]["elements"][0]["distance"]["text"]
            duration = data["rows"][0]["elements"][0]["duration"]["text"]

            return distance, duration

        else:
            messagebox.showinfo("Error", "Request failed.")
            return None, None
    else:
        messagebox.showinfo("Error", "Failed to make the request.")
        return None, None

def get_coordinates(address):
    
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    # Параметри запиту
    params = {
        "address": address,
        "key": API_KEY
    }
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data['status'] == "OK":
            results = data['results']
            if results:
                first_result = results[0]
                location = first_result['geometry']['location']
                latitude = location['lat']
                longitude = location['lng']
                return latitude, longitude
            else:
                return "Адреса не знайдена."
        else:
            if data['status'] == 'ZERO_RESULTS':
                return "Адреса не знайдена."
            return f"Помилка у відповіді API: {data['status']}"
    else:
        return f"Помилка HTTP-запиту: {response.status_code}"

#start = "Palace Lucerna, Nové Město"
#end = "Project FOX, Praha 3-Žižkov"

def get_place_details(place_id):
    base_url = 'https://maps.googleapis.com/maps/api/place/details/json'
    params = {
        'place_id': place_id,
        'key': API_KEY,
        'language': 'uk'
    }
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()

        if data['status'] == 'OK':
            return data['result']
        else:
            print(f"Не вдалося отримати деталі місця: {data['status']}")
    else:
        print(f"Помилка запиту до Places Details API: {response.status_code}")

    return None

def search_cafes_by_coords(lat, lon):
    places = find_nearbyrest(lat, lon)
    details = []
    delivery = []
    routes = []
    if len(places) == 0:
        messagebox.showinfo("Нам дуже прикро", "Нажаль поблизу немає закладів харчування.\nСпробуйте іншу адресу.")
        return
    for place in places:
        if 'photos' in place and len(place['photos']) > 0:
            photo_reference = place['photos'][0]['photo_reference']
            place['photo'] = download_image(photo_reference)
        else:
            place['photo'] = None
        place_id = place['place_id']
        place_detail = get_place_details(place_id)
        details.append(place_detail)
        route = get_route_image(f"{lat},{lon}",f"{place['geometry']['location']['lat']},{place['geometry']['location']['lng']}") 
        routes.append(route)
        deliv = get_delivery_time(f"{lat},{lon}",f"{place['geometry']['location']['lat']},{place['geometry']['location']['lng']}")
        delivery.append(deliv)

    display_places_info(places, details, delivery, routes)



# Функція для обробки введення користувача
def search_cafes():
    clear_error_messages()

    if choice_var.get() == "coords":
        lat = None
        lon = None
        try:
            str_lat = lat_entry.get()
            if not str_lat:
                raise ValueError("Поле не має бути пустим")
            lat = float(str_lat)
            if not (-90 <= lat <= 90):
                raise ValueError("Широта має бути в межах [-90, 90]")
        except ValueError as e:
            show_error_message(lat_entry, str(e))

        try:
            str_lon = lon_entry.get()
            if not str_lon:
                raise ValueError("Поле не має бути пустим")
            lon = float(str_lon)
            if not (-180 <= lon <= 180):
                raise ValueError("Довгота має бути в межах [-180, 180]")
                
        except ValueError as e:
            show_error_message(lon_entry, str(e))

        if lat is not None and lon is not None:
            search_cafes_by_coords(lat, lon)

    elif choice_var.get() == "address":
        address = address_entry.get()
        if not address:
            show_error_message(address_entry, "Будь ласка, введіть адресу.")
        else:
            location = get_coordinates(address)
            if isinstance(location, str):
                show_error_message(address_entry, location)
            else: 
                latitude, longitude = location
                search_cafes_by_coords(latitude, longitude)
            
    elif choice_var.get() == "geolocation":
        location = get_location()
        if isinstance(location, str):
                show_error_message(address_entry, location)
        else:
            latitude, longitude = location
            search_cafes_by_coords(latitude, longitude)

def clear_error_messages():
    for entry in [lat_entry, lon_entry, address_entry]:
        entry.config(bg="white")
        error_label_dict.get(entry, None).config(text="")

def show_error_message(entry, message):
    entry.config(bg="lightcoral")
    error_label_dict[entry].config(text=message, fg="red")

def update_input_fields(*argc):
    lat_entry.grid_forget()
    lon_entry.grid_forget()
    lat_label.grid_forget()
    lon_label.grid_forget()
    address_entry.grid_forget()
    address_label.grid_forget()
    search_button.grid_forget()
    
    clear_error_messages()
    
    if choice_var.get() == "coords":
        lat_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        lat_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        lon_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        lon_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        search_button.grid(row=4, column=0, columnspan=2, pady=10)
    elif choice_var.get() == "address":
        address_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        address_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        search_button.grid(row=2, column=0, columnspan=3, pady=10)
    elif choice_var.get() == "geolocation":
        search_button.grid(row=1, column=0, columnspan=3, pady=10)



# Створення головного вікна
root = tk.Tk()
root.title("Пошук закладів поблизу")

# Змінна для вибору користувача
choice_var = tk.StringVar(value="coords")
choice_var.trace("w", update_input_fields)

# Створення кнопок вибору
tk.Radiobutton(root, text="Ввести координати", variable=choice_var, value="coords").grid(row=0, column=0, padx=5, pady=5)
tk.Radiobutton(root, text="Ввести адресу", variable=choice_var, value="address").grid(row=0, column=1, padx=5, pady=5)
tk.Radiobutton(root, text="Використати геолокацію", variable=choice_var, value="geolocation").grid(row=0, column=2, padx=5, pady=5)

# Поля для введення координат
lat_label = tk.Label(root, text="Широта:")
lat_entry = tk.Entry(root)
lon_label = tk.Label(root, text="Довгота:")
lon_entry = tk.Entry(root)

# Поле для введення адреси
address_label = tk.Label(root, text="Адреса:")
address_entry = tk.Entry(root, width=40)

# Кнопка пошуку
search_button = tk.Button(root, text="Пошук", command=search_cafes)

# Словник для зберігання віджетів повідомлень про помилки
error_label_dict = {
    lat_entry: tk.Label(root, text=""),
    lon_entry: tk.Label(root, text=""),
    address_entry: tk.Label(root, text=""),
}

# Розміщення віджетів для повідомлень про помилки
for i, entry in enumerate([lat_entry, lon_entry, address_entry]):
    error_label_dict[entry].grid(row=1 + i, column=2, padx=5, pady=5, sticky="w")


update_input_fields()
root.mainloop()



