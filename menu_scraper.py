import requests
from bs4 import BeautifulSoup
import json
import time
import math
import re
import os

if not os.path.exists("menu_items"):
    os.mkdir("menu_items")

already_scraped = set()
for line in open("already_menu_scraped.txt"):
    already_scraped.add(line.rstrip("\n"))

print(already_scraped)

for filename in os.listdir("./reviews/"):
    restaurant = filename.split(".")[0]
    print(restaurant)
    if restaurant not in already_scraped:
        try: 
            source = requests.get("https://www.yelp.com/menu/"+restaurant)
            soup = BeautifulSoup(source.content, features = "html.parser")
            items = soup.find_all('div', class_="menu-item")
            if not items:
                raise Exception
        except:
            print("No menu exists")
            with open("already_menu_scraped.txt", "a+") as g: 
                g.write(restaurant + "\n")
            continue
        

        with open("menu_items/"+ restaurant + ".txt", "w+") as f:
            for index, item in enumerate(items):
                try:
                    name = item.find("h4").text.replace("\n","")
                    name = re.findall("[\s\d\.]*(.+)", name)[0]
                    #print(name)
                    if name not in already_scraped:
                        f.write(name+"\n")
                        already_scraped.add(name)
                except:
                    continue
        with open("already_menu_scraped.txt", "a+") as g: 
            g.write(restaurant + "\n")