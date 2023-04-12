from flask import Flask, render_template
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from bs4 import BeautifulSoup 
import requests

#don't change this
matplotlib.use('Agg')
app = Flask(__name__) #do not change this

#insert the scrapping here
url_gets = [] 
n_of_pages = 15 # number of pages to scrap
for i in range (1, n_of_pages+1):
    url_gets.append(requests.get('https://www.kalibrr.id/id-ID/job-board/te/data/'+str(i)))

url_get = url_gets[0].content # get the first page
# combine with the rest of pages
for i in range (1, n_of_pages):
    url_get += url_gets[i].content

soup = BeautifulSoup(url_get,"html.parser")

#find your right key here
tables = soup.find_all('div', attrs={'class':'k-bg-white k-divide-y k-divide-solid k-divide-tertiary-ghost-color'})
total_row_length = 0
for i in range (len(tables)):
    row = tables[i].find_all('div', attrs={'class':'k-col-start-3 k-row-start-1'})
    row_length = len(row)
    total_row_length += row_length

import pandas as pd
from dateutil.relativedelta import relativedelta #library to do arithmethic calculation with datetime data

now = pd.Timestamp.now() #get the current time

temp = [] #initiating a tuple
for j in range(len(tables)): #looping through each table
    for i in range(0, row_length): #looping through each job post
        
        #title
        title = tables[j].find_all('div', attrs={'class':'k-col-start-3 k-row-start-1'})[i].text
        
        #location
        location = tables[j].find_all('div', attrs={'class':'k-flex k-flex-col md:k-flex-row'})[i].text
        location = location[ : location.find(',')] #only taking the region field
        
        #date
        date = tables[j].find_all('span', attrs={'class':'k-block k-mb-1'})[i].text #contain info for date posted and due date
        #date posted
        date_posted = date[date.find(' ')+1 : date.find('•')] #only taking the date posted phrase
        #change word 'an' or 'a' to a number (1) 
        if(date_posted[0:2]=='an'):
            date_posted = '1' + date_posted[2:]
        elif(date_posted[0]=='a'):
            date_posted = '1' + date_posted[1:] 
        number = int(date_posted[ : date_posted.find(' ')]) #get the number field
        letter = date_posted[date_posted.find(' ')+1]       #get the first letter field
        if(letter=='d'):   #if it's a day
            date_posted = now - relativedelta(days=number)   #substract the current day with the amount of number field
        elif(letter=='m'): #if it's a month
            date_posted = now - relativedelta(months=number) #substract the current month with the amount of number field
        elif(letter=='h'): #if it's an hour
            date_posted = now - relativedelta(hours=number)  #substract the current hour with the amount of number field
        else:
            print('Error')
        date_posted = str(date_posted.date()) #get only the date field and convert it to a string
        
        #due date
        due_date = date[date.find('before')+7 : ] #only taking the due date phrase
        d = int(due_date[ : due_date.find(' ')])  #get the day field
        months = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 
                  'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
        m = due_date[due_date.find(' ')+1 :]      #get the month field
        m = months[m]                             #change the month abreviation to the according number
        due_date = now + relativedelta(day=d, month=m) #change the current day and month to the specified number
        due_date = str(due_date.date())                #get only the date field and convert it to a string
        
        #company
        company = tables[j].find_all('span', attrs={'class':'k-inline-flex k-items-center k-mb-1'})[i].text

        temp.append((title, location, date_posted, due_date, company))

#change into dataframe
df = pd.DataFrame(temp, columns=('title','location','post_date','due_date','company'))

#insert data wrangling here
df = df.drop_duplicates()
df.reset_index(inplace=True)
df.drop('index', axis=1, inplace=True)
df[['post_date','due_date']] = df[['post_date','due_date']].astype('datetime64[ns]')
df.dtypes

df['location'] = df['location'].str.replace('City','')      #remove the word 'City'
df['location'] = df['location'].str.replace('Kota','')      #remove the word 'Kota'
df['location'] = df['location'].str.replace('Kabupaten','') #remove the word 'Kabupaten'
df['location'] = df['location'].str.strip()                 #remove leading and trailing whitespace

for i in range(len(df['location'])):
    
    find_whitespace = df['location'][i].find(' ')            #search for the first whitespace
    first_word = df['location'][i][ : find_whitespace]       #take the first word
    remaining_word = df['location'][i][find_whitespace+1 : ] #take the remaining words
    
    region = {'North':'Utara', 'South':'Selatan', 'East':'Timur', 'West':'Barat', 'Central':'Pusat'} #dict mapping English to Bahasa
    region_keys = list(region.keys()) #take the dict key
    
    if first_word in (region_keys): #if the first word was one of the dict key
        fixed_location = remaining_word + ' ' + region[first_word] #take the remaining words and add with the corresponding word
        df['location'][i] = fixed_location  #replace with the new value
#end of data wranggling 

#data to visualize
viz = pd.crosstab(
    index=df['location'],
    columns='count',
    colnames=' ',
).sort_values(by='count',ascending=False)

@app.route("/")
def index(): 
	
	card_data = f'{viz[viz["count"] == viz["count"].max()].index.values[0]}' #be careful with the " and ' 

	# generate plot
	ax = viz.T.plot(
		kind = 'bar',
		xticks = [],
        figsize = (10,9)
	)   
	
	# Rendering plot
	# Do not change this
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True)
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_result = str(figdata_png)[2:-1]

	# render to html
	return render_template('index.html',
		card_data = card_data, 
		plot_result = plot_result
		)


if __name__ == "__main__": 
    app.run(debug=True)