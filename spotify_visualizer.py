#!/usr/bin/env python
# coding: utf-8

# # Finding the Number of New Song Listens per Month

# ## Modules

# In[1]:


import pandas as pd
import numpy as np
import json
import ast


# ## Function Converting String Dictionaries to Literal Dictionaries

# The JSON file containing the personal library information is a JSON file with nested objects. When the file is read, the entries are returned as string representations of a Python dictionary. This function is used to convert those string dictionaries to literal dictionaries and put it into an appropriate Pandas DataFrame format. 

# In[16]:


def strDictsToDF(strDicts): 
    """
    Makes a new Pandas Dataframe object
    from the literal interpretation of another Dataframe
    containing string representations of Python dictionaries.
    To be used when parsing the YourLibrary.json
    Input: DataFrame of dictionaries represented as strings
    Output: DataFrame created from the literal interpretation of those string dictionaries
                 as actual Python dictionaries. 
    """
    for i in range (0, len(strDicts)):
        # The ast module allows literal interpretation of the string dictionaries
        temp_dict = ast.literal_eval(str(strDicts.loc[i][0]))
        
        # This is to find the dictionary keys which will be the column names.  
        # However, 
        if i == 0: 
            try:
                output = pd.DataFrame(columns=temp_dict.keys())
            except:
                print("An exception occurred: Object of Nonetype found in first position")
                return
            
        # Converts the dictionary values into literals and puts them into a dataframe row
        try: 
            output.loc[i] = temp_dict.values()
        except:
            print("An exception occurred: Object of Nonetype found before expected end")
            break
    return output; 


# ## JSON Filepaths

# These two filepaths are for the two JSON files containing the required information to find new song listens each month. 

# In[3]:


streamingPath = 'my_spotify_data\MyData\StreamingHistory0.json'
libraryPath = 'my_spotify_data\MyData\YourLibrary.json'


# ## Read the streaming history JSON file

# In[4]:


dataStream = pd.read_json(streamingPath)
dataStream['minsPlayed'] = dataStream['msPlayed']/60000
dataStream['UniqueID'] = dataStream['artistName'] + ':' + dataStream['trackName']

dataStream.head(5)


# ## Read the nested your library JSON file containing multiple objects

# The JSON file associated with the user's library is a JSON file with nested objects. There are several objects of varying length and can at some times be empty. In this code implementation, it's known that the object containing artists in a library is not empty. However, it is important to check for other objects if they are empty. This code is also only interested in the yourArtists section of the JSON file containing the library information. 

# In[15]:


dataLibrary = pd.read_json(libraryPath, orient='index')

# The index entries for tracks, albums, shows, episodes, bannedTracks, other are as follows: 0, 1, 2, 3, 4, 5, 6, 7
yourArtists = strDictsToDF(pd.DataFrame(dataLibrary.iloc[0]))


# ## Processing the Data

# Generate a new column in the yourArtists dataframe called, "UniqueID." This column is made by combining the artist and track columns with a semicolon splitting them. Then another column is made consisting of just the Spotify track URI, called, "track_uri."

# In[6]:


yourArtists['UniqueID'] = yourArtists['artist'] + ':' + yourArtists['track']
yourArtists_uri = yourArtists['uri'].str.split(":", expand=True)
yourArtists['track_uri'] = yourArtists_uri[2]


# Find all unique artist names found in the yourArtists dataframe that was created. This will be used later to compare between if a streamed item is a Podcast or not, this will help determine new monthly listens of songs. 

# In[7]:


uniqueArtistNames = yourArtists['artist'].unique()

print(uniqueArtistNames)


# Generate a master dataframe which is based on the streaming history dataframe. Then create two new columns called, "In Library" and "Podcast." In Library is a column that consists of either 0s or 1s, if both the master dataframe and yourArtists contain the same UniqueID, then that means the track that was streamed is already in the library. Next, the Podcast column is used to determine if the streamed item is a song or a podcast. The artistName column in the master dataframe is compared with the list of uniqueArtistNames found. The list of uniqueArtistNames only list musical artists. Finally, the columns of "album," "UniqueID," and "track_uri" from yourArtists are merged with the master dataframe. 

# In[8]:


dataTableau = dataStream.copy()
dataTableau_len = len(dataTableau)
dataTableau['In Library'] = np.where(dataTableau['UniqueID'].isin(yourArtists['UniqueID'].tolist()), 1, 0)
dataTableau['Podcast'] = np.where(dataTableau['artistName'].isin(uniqueArtistNames.tolist()), 0, 1)
dataTableau = pd.merge(dataTableau, yourArtists[['album', 'UniqueID', 'track_uri']], how='left', on=['UniqueID'])


# In order to determine new song listens, the columns of "In Library" and "Podcast" of a given entry must be, 0. Once an entry is determined to be a new listen of a song, then the month when the song was listened to is found and recorded. 

# In[9]:


newListensMonthly = pd.DataFrame([(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)], index=['2020', '2021'], 
                                 columns=['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'])

newListensMonthlyPerc = pd.DataFrame(index=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'],  
                                     columns=['2020', '2021'])

# Calculate how many new song listens occurred each month
for i in range(0, len(dataTableau)): 
    if ((dataTableau['In Library'][i] == 0) and dataTableau['Podcast'][i] == 0): 
        # End time expanded to [year, month, day hour:min]
        expandedTime = dataTableau['endTime'][i].split("-")
        newListensMonthly[expandedTime[1]][expandedTime[0]] = newListensMonthly[expandedTime[1]][expandedTime[0]] + 1
    else: 
        continue

# Calculate percentage of new song listens to total songs listened to
for j in range(0, 2): 
    for i in range(0, len(newListensMonthlyPerc)):
        newListensMonthlyPerc.iloc[i, j] = (newListensMonthly.iloc[j, i]/dataTableau_len)*100


# Initially, the columns for the DataFrame newListensMonthly is the format of a string that looks like a two digit number. This format is useful when trying to count how many new listens per month occur but this will be changed in the code below which is nicer to display on a plot. 

# In[10]:


newListensMonthly.rename(columns={'01': 'Jan', '02': 'Feb', '03':'Mar', '04':'Apr', '05':'May',
                                 '06':'Jun', '07':'Jul', '08':'Aug', '09':'Sept', '10':'Oct', '11':'Nov', '12':'Dec'}, inplace=True)


# ## Plotting the Data

# Plot a bar graph of new monthly song listens on Spotify for the given years on one plot.  

# In[11]:


newListensMonthly.plot.bar(xlabel='Months', ylabel='No. of Listens', title='New Monthly Listens on Spotify 2020-2021', colormap='Paired').grid(axis='y')


# Separate the two years of the dataframe into separate Series. 

# In[12]:


newListens0 = newListensMonthly.iloc[0].squeeze()
newListens1 = newListensMonthly.iloc[1].squeeze()


# Plot a bar graph of the data from 2020.

# In[13]:


newListens0.plot.bar(xlabel='Months', ylabel='No. of Listens', title='New Song Listens per Month on Spotify in 2020').grid(axis='y')


# Plot a bar graph of the data from 2021.

# In[14]:


newListens1.plot.bar(xlabel='Months', ylabel='No. of Listens', title='New Song Listens per Month on Spotify in 2021').grid(axis='y')


# In[ ]:




