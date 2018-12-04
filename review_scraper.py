import requests
from bs4 import BeautifulSoup
import json
import time
import math
import os

already_scanned = set()
scanned_restaurants = open("completed_restaurants.txt")
for line in scanned_restaurants:
    already_scanned.add(line.rstrip("\n"))
print(already_scanned)
scanned_restaurants.close()

restaurants_list = open("sf_restaurant_names.txt")
base_url = "https://www.yelp.com/biz/"
for restaurant_line in restaurants_list:
    restaurant = restaurant_line.rstrip("\n")
    if restaurant in already_scanned:
        continue
    restaurant_url = base_url + restaurant
    print(restaurant_url)
    source = requests.get(restaurant_url)
    soup = BeautifulSoup(source.content, features = "html.parser")
    #print(soup.prettify())
    if len(soup.find_all("script", {"type": "application/ld+json"})) == 1:
        json_data = soup.find_all("script", {"type": "application/ld+json"})[0].text
    else:
        json_data = soup.find_all("script", {"type": "application/ld+json"})[1].text
        if 'review' not in json_data:
            json_data = soup.find_all("script", {"type": "application/ld+json"})[2].text
    json_data = json.loads(json_data)
    if 'aggregateRating' not in json_data:
        with open("skipped_restaurants.txt", "a+") as f:
            print("Skipped " + restaurant_line)
            f.write(restaurant_line)
        with open("completed_restaurants.txt", "a+") as f:
            f.write(restaurant_line)
        continue
    num_reviews = json_data['aggregateRating']['reviewCount']
    num_pages = math.ceil(num_reviews / 20)

    if num_reviews >= 100:
        reviews = []

        # First page
        current_reviews = json_data['review']
        for r in current_reviews:
            reviews.append(r)
    
        # Every page after the first page
        for page in range(1, num_pages+1):
            print(restaurant + " page " + str(page) + " of " + str(num_pages))
            url = restaurant_url + "?start=" + str(page*20)
            source = requests.get(url)
            soup = BeautifulSoup(source.content, features = "html.parser")
            if len(soup.find_all("script", {"type": "application/ld+json"})) == 1:
                json_data = soup.find_all("script", {"type": "application/ld+json"})[0].text
            else:
                json_data = soup.find_all("script", {"type": "application/ld+json"})[1].text
                if 'review' not in json_data:
                    json_data = soup.find_all("script", {"type": "application/ld+json"})[2].text
            json_data = json.loads(json_data)
            current_reviews = json_data['review']
            for r in current_reviews:
                reviews.append(r)
            time.sleep(0.2)
            
        # Write to disk
        file_name = "reviews/" + restaurant + ".json"
        with open(file_name, 'w+') as f:
            for review in reviews:
                f.write(json.dumps(review))
                f.write("\n")
    
    with open("completed_restaurants.txt", "a+") as f:
        f.write(restaurant_line)