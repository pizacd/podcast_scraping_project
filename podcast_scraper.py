'''podcast web scraping module made by Douglas Pizac
obtains podcast rankings and information from third-party podcast website

Contains four functions:

podcast_config(config_file): take in conf.ini and returns user email and password for website account

podcast_login(): enters login info to website and returns browser session to scrape site

get_podcast_ranks(num_ranks,platform): returns csv file containing top number of podcasts specified

get_podcast_info(filename): take in get_podcast_ranks csv file and writes info for all podcasts'''

#import all required libraries
from configparser import ConfigParser
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
from datetime import date
import pandas as pd



#Add User agent to scrape the site
opts = Options()
opts.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36")




# ## Get desired podcast ranks
def podcast_config(config_file):
    '''returns account email and password for chartable.com
    
    args:
    config_file: str, configuration file (ex: "conf.ini")'''
    cfg = ConfigParser(interpolation=None) 
    try:
        cfg.read(config_file) #conf.ini
    except:
        raise ImportError('Cannot read configuration file')
    login_conf = cfg['chartable']
    user_email = login_conf['email'] 
    passwd = login_conf['passwd']
    return user_email, passwd


def podcast_login():
    '''uses podcast_config function to open browser and enter login info
    args: None

    returns browser to keep open login session'''

    
    user_email, passwd = podcast_config('conf.ini')
    
    driver = webdriver.Chrome(options=opts)

    driver.get('https://www.chartable.com/sign_in')

    email = driver.find_element_by_id('Email')

    password = driver.find_element_by_id('Password')
    
    
    email.send_keys(user_email)
    password.send_keys(passwd)

    driver.find_element_by_name('commit').click()
    time.sleep(5)
    return driver


def get_podcast_ranks(num_ranks, platform): 
    '''returns a csv file containing the podcast ranks for 
    either Spotify or Apple.
    
    args:
    
    num_ranks: int, number of ranks to scrape. Must be <=250 for Apple and 
    <=200 for Spotify.
    platform: str, specify whether to get rankings from Apple or Spotify.'''




    platform = platform.lower()
    
    #raise potential errors before initialing web scraper
    if not isinstance(num_ranks,int):
        raise TypeError('Rank number must be an integer')
    
    elif num_ranks >250 and platform=='apple':
        raise ValueError('Rank number exceeds Apple chart: select number <=250.')
    elif num_ranks >200 and platform == 'spotify':
        raise ValueError('Rank number exceeds Spotify chart: select number <=200.')
    elif platform not in ['apple','spotify']:
        raise ValueError('Platform must be either: apple or spotify')
    
    #initialize browser and log in
    driver = podcast_login()

    # initialize file, starting url based on platform
 
    if platform == 'apple':
        chart_url = 'https://www.chartable.com/charts/itunes/us-all-podcasts-podcasts'
        filename = f'apple_{num_ranks}_ranks.csv'
        if num_ranks<=100:
            num_pages = 1
        else:
            num_pages = num_ranks//100+1
            
    elif platform == 'spotify':
        chart_url = 'https://chartable.com/charts/spotify/united-states-of-america-top-podcasts'
        filename = f'spotify_{num_ranks}_ranks.csv' 
        if num_ranks <=50:
            num_pages = 1
        else:
            num_pages = num_ranks//50+1
    
    
    csv_chart_file = open(filename, 'w', encoding='utf-8', newline='')
    chart_writer = csv.writer(csv_chart_file)

    #Open Google Chrome bot
    

    #Get ranks of all on each page
    page_index = 0
    while page_index< num_pages: #keep scraping next page until desired num_ranks are obtained
        try:
            print(f'Scraping page {page_index+1}...')
            
            driver.get(chart_url)
            ranks_elems = driver.find_elements_by_xpath('//div[@class = "b header-font f2 tc"]')
            ranks = [int(rank.text) for rank in ranks_elems]
            rows = driver.find_elements_by_xpath('//td[@class = "pv2 ph1"]')
            
            #write row for each ranked podcast
            for row in rows:
                podcast_dict = {}
                try:
                    podcast_url = row.find_element_by_xpath('./div[@class = "title f3"]/a').get_attribute('href')
                except:
                    ranks.pop(0)
                    continue
                if row.text.find('\n') ==-1:
                    name = row.text
                    network = 'Unaffiliated'
                else:
                    network, name= row.text.split('\n')

                podcast_dict['rank']=ranks.pop(0)
                podcast_dict['name'] = name
                podcast_dict['network'] = network
                podcast_dict['date_scraped'] = date.today().strftime('%Y-%m-%d')
                podcast_dict['url'] = podcast_url

                chart_writer.writerow(podcast_dict.values())

                
            #get url of next page of podcast ranks
            chart_url = driver.find_element_by_xpath('//span[@class = "next"]/a').get_attribute('href')
            time.sleep(4)
            page_index +=1
        except:
            break
    
    print(f'All {num_ranks} podcasts obtained')
    csv_chart_file.close()
    driver.close()
    
    #create column names for returned csv file
    colnames = [f'{platform}_rank','name','network','date_scraped','url']
    import pandas as pd
    df = pd.read_csv(filename,names = colnames)
    df = df.loc[df[f'{platform}_rank']<=num_ranks]
    return df.to_csv(filename,index = False)




#Get all rankings for spotify, saved as "spotify_200_ranks.csv"
#get_podcast_ranks(200,'spotify')




#Get all rankings for apple, saved as "apple_250_ranks.csv"
#get_podcast_ranks(250,'apple')




#get_podcast_ranks(100,'spotify')


# Scraping episode info

def get_podcast_info(filename):
    '''writes a file containing stars, ratings, and episode dates
    for each podcast specified in filename arugment
    
    args:
    filename: str, filepath/filename of csv file returned from 
    get_podcast_ranks function'''

    #make sure filename argument is valid before launching browser
    try:
        chart_file = pd.read_csv(filename)
    except:
        raise ValueError(r'File cannot be found: please use a valid file (example: "spotify_100_ranks.csv")')

    csv_podcast_file = open('podcast_data.csv', 'w', encoding='utf-8', newline='') 
    podcast_writer = csv.writer(csv_podcast_file)



    #initialize browser and log in
    driver = podcast_login



    #Open each podcast page
    for url in chart_file['url']:
        driver.get(url)

        try:
            find_genre = driver.find_elements_by_xpath('//div[@class = "links bg-white pa3 br2 b--near-white ba f6"]//div/a[contains(@href,"genre")]')
            try:
                genre = find_genre.text
            except:
                genre = [i.text for i in find_genre]
        except:
            genre = 'Unknown'

        #scrape stars and ratings. If unavailable, set to None
        try:
            stars_ratings = driver.find_element_by_xpath('//div[@class = "gray"]').text
            stars, ratings = stars_ratings.split(' stars from ')
            try:
                ratings = int(ratings.replace(',','').replace('ratings',''))
            except:
                ratings = int(ratings.replace('ratings',''))
        except:
            stars = None
            ratings = None

        podcast_dict = {}

        podcast_dict['genre'] = genre
        podcast_dict['stars'] = stars
        podcast_dict['ratings'] = ratings
        podcast_dict['url'] = url


        #get the episodes url for the podcast
        episodes_url = driver.find_element_by_xpath('//div[@class = "link mb2"]/a').get_attribute('href')
        time.sleep(4)
        driver.get(episodes_url)


        #Scrape episodes for each page, get next page, and repeat until all are scraped
        index = 1
        while True:
            try:
                wait_episodes = WebDriverWait(driver, 10)
                episodes = wait_episodes.until(EC.presence_of_all_elements_located((By.XPATH,'//div[@class = "mb4"]')))
                for episode in episodes:
                    episode_info = episode.find_elements_by_xpath('.//div')
                    episode_info = [i.text for i in episode_info]
                    if episode_info:
                        episode_date = episode_info.pop()
                    else:
                        continue
                    podcast_dict['episode_date'] = episode_date.replace('Published ','')

                    podcast_writer.writerow(podcast_dict.values())   
                next_episodes_link = driver.find_element_by_xpath('//span[@class = "next"]/a').get_attribute('href')
                time.sleep(4)
                driver.get(next_episodes_link)
            except:
                #once all episodes are collected, break loop and scrape next podcast
                break 





    csv_podcast_file.close()
    driver.close()
    print('All episode information scraped!')






# ## Run line below if error leaves csv/driver open


#lines written for jupyter notebook when scraping bot had unexpected errors
#close the csv and browser, if able to
# try:
#     csv_file.close()
#     driver.close()
# except:
#     driver.close()




#get_podcast_info('spotify_100_ranks.csv')

