'''
podcast cleaning module by Douglas Pizac
takes podcast csvs, merges and cleans them for analysis

Four functions:

test_rankings(ranks_df, num_times): returns average p-value for determining differences between
Apple and Spotify rankings 

clean_genres(obj): removes leading and trailing characters to get genre strings.

list_unpacking(df,colname): unpacks nested list and lengthens DataFrame

chartable_merge(chart_file, podcast_file): joins chart & data csvs. Also cleans and adds columns
'''

from scipy import stats
import pandas as pd



def test_rankings(ranks_df,num_times):
    '''runs ind T-Test num_times to determine if there is a difference in rank across platforms

    args: 
    ranks_df: str, merged DataFrame of podcasts that have both an apple and platform rank
    num_times: int, number of times to run the T-test to determine differences'''

    #create empty list for p-values of each T-test
    p_values =[]
    for i in range(num_times):
        ranks_sample = ranks_df.sample(50,replace = True) #collect 50 podcasts randomly w/ replacement
        
        #if variances different, T-test will use if statement. Otherwise, T-test will use else statement
        bartletts, bart_p = stats.bartlett(ranks_sample['apple_rank'], ranks_sample['spotify_rank'])
        if bart_p <.05:
            T, T_p =  stats.ttest_ind(ranks_sample['apple_rank'],ranks_sample['spotify_rank'],equal_var=False)
        elif bart_p >.05:
            T, T_p = stats.ttest_ind(ranks_sample['apple_rank'],ranks_sample['spotify_rank'],equal_var=True)
        
        p_values.append(T_p)

    #calculate the average p-value of the tests conducted
    final_p = sum(p_values)/len(p_values)
    if final_p >0.05:
        print('No significant difference in rank across platforms!')
    else:
        print('Significant difference in rank across platforms!')
    return final_p


def clean_genres(obj):
    '''removes leading and trailing characters from each element in pandas Series to get list of genres

    args:
    obj: each element in genre Series called by the lambda function'''
    if obj.find('[') == -1:
        return obj
    else:
        return obj[2:-2].replace("'",'').split(', ')
    
def list_unpacking(df,colname):
    '''
    Unpacks list of nested genres and pivots DataFrame longer for genre analyses

    args:
    df: DataFrame
    colname: str, name of column to unpack values
    '''
    index = 0
    list_ = []
    for item in df[colname]:
        list_.extend(map(lambda x: [index,x],item))
        index +=1
    new_df = pd.DataFrame(list_, columns = ['index', colname[:-1]])
    df = df.merge(new_df,left_index = True, right_on = 'index')
    df.drop(['genres','index'],axis = 1, inplace = True)
    return df


def chartable_merge(chart_file,podcast_file):
    '''returns DataFrame of merged chart and podcast data csvs
    args:
    chart_file: str, filepath/name of rank file
    podcast_file, str, filepath/name of podcast data file'''


    if chart_file.find('ranks')==-1:
        raise ImportError('Input file for chart_file argument does not contain podcast chart')
    elif podcast_file.find('data')==-1:
        raise ImportError('Input file for podcast_file arguement does not contain podcast chart')
    
    platform_ = pd.read_csv(chart_file)
    podcast = pd.read_csv(podcast_file, names = ['genres', 'stars', 'ratings','url','episode_date'])
    platform= platform_.merge(podcast, on = 'url')
    platform.drop('url',axis = 1, inplace = True)

    platform['episode_date'] = pd.to_datetime(platform['episode_date'])
    platform['date_scraped'] = pd.to_datetime(platform['date_scraped'])
    platform['episode_day_of_week'] = platform['episode_date'].dt.day_name()


    episodes = platform.groupby('name')[['episode_date']].agg(['count','min']).reset_index()
    episodes.columns = ['name','num_episodes','first_archived_episode']


    platform = platform.merge(episodes,on = 'name')


    platform['days_since_first'] = (platform.date_scraped-platform.first_archived_episode).dt.days
    platform['days_since_update'] = (platform.date_scraped-platform.episode_date).dt.days

    platform['genres'] = platform['genres'].apply(lambda G: G if G!= '[]' else "['Unknown']")
    platform.genres = platform['genres'].apply(lambda s: clean_genres(s))
    return platform
