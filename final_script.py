import pandas as pd
import re
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
import os
import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import numpy as np
import json
#MAP from restaurant name to list [filtered reviews in a dataframe, list of menu items]
def big_object():
    mapping  = {}
    for restaurant in os.listdir("menu_items/")[1:]: #get rid of the first DS_Store name TAKE OUT THE 2
        name = restaurant[:-4]
        menu = []
        try:
            reviews = pd.read_json("reviews/"+name+".json",lines = True)
        except:
            continue
        with open("menu_items/" + restaurant) as f:
            content = f.read().splitlines()
            for item in content:
                menu.append(''.join(re.findall(r'[\w\d]*[\s]*[\w\d]*[^\s]', item)))
        mapping[name] = [reviews, menu]
    for restaurant in mapping:
        mapping[restaurant][0]['rating'] = mapping[restaurant][0]["reviewRating"].apply(func = lambda x: x["ratingValue"])
        mapping[restaurant][0] = mapping[restaurant][0][["description", "rating"]]
        mapping[restaurant][0] = mapping[restaurant][0].rename(index = str, columns = {'description':'review'})
    return mapping

#IMPORT BIG DATA HERE WHEN AFTER DONE TESTING
#stop words
sw = set([w for w in stopwords.words("english")])
#Cleans the dish name of punctuation
def clean_menu_item(dish):
    # TODO: append 
    dish = dish.lower()
    dish = re.sub("[\'\".!?\\-\n\/]", "", dish)
    return dish

#Checks if the sentence contains a wording similar to a menu item
def contains(sentence, menu_items):
    most_likely_match = 0
    most_likely_length = 0
    complete_matches = []
    for item in menu_items:
        item_words = [w for w in item.split(" ") if w not in sw]
        match = sum([1 for word in item_words if word.lower() in sentence])/len(item_words)
        if match > most_likely_match:
            most_likely_match = match
            most_likely_length = len(item_words)
            most_likely_dish = item
        elif match == most_likely_match and len(item_words) >= most_likely_length:
            most_likely_match = match
            most_likely_length = len(item_words)
            most_likely_dish = item
    if most_likely_length < 4 and most_likely_match != 1: 
        return ""
    elif most_likely_match <= 0.75:
        return ""
    return most_likely_dish


#generate a dictionary mapping menu item to a list of sentences mentioning it. 
def generate_dish_reviews(data, menu):
    reviews = data['review']
    
    menu_items = [clean_menu_item(dish) for dish in menu]
    dish_reviews = {dish:[0,0] for dish in menu_items}
    index = 0
    for r in list(reviews):
        sentences = sent_tokenize(r)
        #assuming that one food is mentioned per sentence
        curr_food = None;
        mentioned_foods = set()
        counter = 0;
        for sentence in sentences:
            sentence = re.sub("[\n]", " ", sentence)
            sentence = sentence.lower()
            dish = contains(sentence, menu_items)
            if dish:
                if curr_food != dish:
                    curr_food = dish
            if curr_food == None:
                continue
            if counter < 2:
                dish_reviews[curr_food].append(sentence)
                mentioned_foods.add(curr_food)
                counter += 1
            else:
                counter = 0 
        for food in mentioned_foods:
            dish_reviews[food][0] += data.rating[index]
            dish_reviews[food][1] += 1
        #get average rating
        index += 1
        
        
    return dish_reviews

def calculate_rating(mapping, data):
    analyser = SentimentIntensityAnalyzer()
    dish_ratings = {}
    for dish in mapping:
        reviews = mapping[dish]
        
        comp_scores = [analyser.polarity_scores(review)['compound'] for review in reviews[2:]]
        if len(comp_scores) == 0:
            continue

        avg_comp = sum(comp_scores)/len(comp_scores)
    
        pos_scores = [analyser.polarity_scores(review)['pos'] for review in reviews[2:]]
    
        avg_pos = sum(pos_scores)/len(pos_scores)
    
        neg_scores = [analyser.polarity_scores(review)['neg'] for review in reviews[2:]]
        avg_neg = sum(neg_scores)/len(neg_scores)
    
        sentiment_score = 2 * avg_comp + avg_pos - avg_neg
    
        appearance_score = np.log(len(reviews))
        
        average_rating = reviews[0]/reviews[1]
        dish_ratings[dish] = 0.45 * sentiment_score + 0.30 * appearance_score + 0.25 * average_rating
    dish_ratings = sorted(dish_ratings.items(), key = lambda kv: kv[1], reverse = True)
        
    return dish_ratings

def main():
    top_five = {}
    mapping = big_object()
    
    for restaurant in mapping:
        test_data = mapping[restaurant]
        data = test_data[0]
        menu_items = test_data[1]
        scores = calculate_rating(generate_dish_reviews(data, menu_items), data)
        top_five[restaurant] = [dish[0] for dish in scores]
       
    return top_five

with open('FINAL_OUTPUT.json', 'w') as outfile:
    json.dump(main(), outfile)