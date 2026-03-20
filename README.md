# DataScienceProjectGroup8

Kaan Sevinc
Beytullah yigit
Jeremy Chaniago
Milad Sahili

Welcome to our Project Repository.

We are investigating how the media shapes our view of the world. 
Instead of relying on gut feelings, we use data from GDELT to measure sentiment, focus, and emotional intensity in global news coverage.

The fundamental part of this Project is the Tone field.
In order to measure how the media shapes our views, gdelt offers a number of tone values.


   
tone	            total-Sentiment (−100 bis +100)
positive_score	    share of positive words
negative_score	    share of negative words
polarity	        emotionality in language
activity_density	"activeness" in language
self_group_density	amount of pronouns used
word_count	Anzahl  amount of words


Gdelt uses a dictionary they created themselfs in order to map the words to their specific group.

In order to retrive the data we used numerous SQL queries to operate on the gdelt dataset via google big query.

The Dataset used for our Streamlit site is mostly the parquet data file, wich contains all relevant fields.
