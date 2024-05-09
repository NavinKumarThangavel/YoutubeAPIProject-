import streamlit as st
import sqlalchemy
from sqlalchemy import create_engine
import pandas as pd

option_list = ["1.What are the names of all the videos and their corresponding channels?",
               "2.Which channels have the most number of videos, and how many videos do they have?",
               "3.What are the top 10 most viewed videos and their respective channels?",
               "4.How many comments were made on each video, and what are their corresponding video names?",
               "5.Which videos have the highest number of likes, and what are their corresponding channel names?",
               "6.What is the total number of likes and dislikes for each video, and what are their corresponding "
               "video names?",
               "7.What is the total number of views for each channel, and what are their corresponding channel names?",
               "8.What are the names of all the channels that have published videos in the year 2022?",
               "9.What is the average duration of all videos in each channel, and what are their corresponding "
               "channel names?",
               "10.Which videos have the highest number of comments, and what are their corresponding channel names?"
               ]

st.header('Select any question to get Insights')
option = st.selectbox(
    "Questions",
    option_list, placeholder='Click the question that you would like to query', index=None)

selected_option = option_list.index(option) + 1 if option in option_list else 0
sql_query = ''

if selected_option == 1:
    sql_query = ''' select                
                      video.video_name [Video Name]
                     ,channel.channel_name [Youtube channel]
               from channel
               join Playlist on channel.channel_id=Playlist.channel_id
               join video on Playlist.playlist_id=video.playlist_id                      
               '''
elif selected_option == 2:
    sql_query = '''  select 
                        channel.channel_name [Youtube channel]
                        ,video_count Videos
                   from  channel
                   join Playlist on channel.channel_id=Playlist.channel_id          
                   join(select 
                              video.playlist_id
                              ,count(1) video_count 
                        from video
                        group by video.playlist_id)as video on  Playlist.playlist_id=video.playlist_id               
                   '''
elif selected_option == 3:
    sql_query = ''' select                          
                          video.Video_Name [Video Name]
                         ,view_count Views
                         ,channel.channel_name [Youtube channel]
                    from
                    channel
                    join Playlist on channel.channel_id=Playlist.channel_id          
                    join(select 
                               Video_Name
                               ,video.playlist_id
                               ,view_count
                               ,RANK() OVER (PARTITION BY video.playlist_id ORDER BY view_count desc ) Rank
                         from video                        
                         )as video on  Playlist.playlist_id=video.playlist_id  
                  Where Rank<=10                
                   '''
elif selected_option == 4:
    sql_query = '''    select 
                           video.video_name [Video Name]
                           ,count(*) Comments
                    from  video
                    join Comment on video.video_id=Comment.video_id  
                    group by video.video_id                 
                    '''
elif selected_option == 5:
    sql_query = '''  select                          
                         video.Video_Name [Video Name]
                        ,Like_Count Likes
                        ,channel.channel_name [Youtube channel]
                    from channel
                    join Playlist on channel.channel_id=Playlist.channel_id          
                    join(select 
                              Video_Name
                              ,video.playlist_id
                              ,Like_Count
                        from video
                        order by video.Like_Count desc 
                        )as video on  Playlist.playlist_id=video.playlist_id  
                    order by like_count desc              
                    '''
elif selected_option == 6:
    sql_query = ''' select 
                        video.Video_Name [Video Name]
                       ,Like_Count Likes
                       ,Dislike_Count Dislikes
                    from video  
                 '''
elif selected_option == 7:
    sql_query = '''  select 
                            channel.channel_name  [Youtube channel]
                            ,channel.channel_views Views
                       from channel 
                       order by channel_views desc '''
elif selected_option == 8:
    sql_query = '''  select 
                            distinct channel.channel_name  [Youtube channel]
                       from channel
                       join Playlist on channel.channel_id=Playlist.channel_id
                       join video on Playlist.playlist_id=video.playlist_id
                       where strftime('%Y',published_data)='2022'
                       '''
elif selected_option == 9:
    sql_query = '''  select 
                            channel.channel_name  [Youtube channel],
                            avg(duration) Duration
                       from channel
                       join Playlist on channel.channel_id=Playlist.channel_id
                       join video on Playlist.playlist_id=video.playlist_id
                       group by video.playlist_id
                       '''
elif selected_option == 10:
    sql_query = '''  select                         
                          video.video_name [video name]
                         ,Comment.Count[Comments]
                         ,channel.channel_name  [Youtube channel]
                     from channel
                     join Playlist on channel.channel_id=Playlist.channel_id
                     join Video on Video.playlist_id=Playlist.playlist_id
                     join (select                            
                                Comment.video_id
                                ,count(1) Count                            
                        from  Comment                     
                        group by Comment.video_id)as Comment on  video.video_id=Comment.video_id 
                     Order by Comment.count desc                                    
                   '''

if sql_query != '':
    dbEngine = create_engine('sqlite:///youtubeapi.db')
    with dbEngine.connect() as conn1:
        df = pd.read_sql(
            sql=sql_query,
            con=conn1.connection
        )
        st.write(df)
        if selected_option in [7, 2, 9]:
            st.bar_chart(df, x=df.columns[0], y=df.columns[1])
        elif selected_option in [3, 5,10]:
            st.bar_chart(df, x=df.columns[2], y=df.columns[1])

