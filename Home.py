import streamlit as st

st.header('YouTube Data Harvesting and Warehousing')
conn = st.connection('youtubeapi_db', type='sql')

#Initialzise table
with conn.session as s:
    s.execute('''CREATE TABLE IF NOT EXISTS Channel( channel_id varchar(255) PRIMARY KEY,
              channel_name varchar(255),
              channel_description text,
              channel_country varchar(10),
              channel_views int, 
              channel_subscription_count int,               
              channel_status varchar(255));
              ''')
    s.execute('''CREATE TABLE IF NOT EXISTS Playlist( playlist_id varchar(255) PRIMARY KEY,
               channel_id varchar(255),
               playlist_name varchar(255),
               FOREIGN KEY (channel_id) REFERENCES Channel(channel_id));
               ''')
    s.execute('''CREATE TABLE IF NOT EXISTS Video( video_id varchar(255) PRIMARY KEY,
                 playlist_id varchar(255),
                 video_name varchar(255),
                 video_description text,
                 published_data datatime,
                 view_count int,
                 like_count int,
                 dislike_count int,
                 favorite_count int,
                 comment_count int,
                 duration int,
                 thumbnail varchar(255),
                 caption_status varchar(255),
                 FOREIGN KEY (playlist_id) REFERENCES Playlist(playlist_id));
                 ''')
    s.execute('''CREATE TABLE IF NOT EXISTS Comment(comment_id varchar(255) PRIMARY KEY,
                   video_id varchar(255),
                   comment_text text,
                   comment_author varchar(255),
                   comment_published_date datetime,
                   FOREIGN KEY (video_id) REFERENCES Video(video_id));
                   ''')
    s.commit()
    s.close()

