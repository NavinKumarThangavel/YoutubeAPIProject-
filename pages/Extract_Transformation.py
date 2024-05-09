import streamlit as st
import googleapiclient.discovery
import pprint
import sqlalchemy
from sqlalchemy import create_engine
import pandas as pd

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"
api_key = "AIzaSyDQ-q0NXC9fyTs9jE8UGt9VOZzjAY2ei_w"
# AIzaSyDQ-q0NXC9fyTs9jE8UGt9VOZzjAY2ei_w
# AIzaSyAh9hUbdkprcXEDa68RL-WOGPt-8nd-i2c
# AIzaSyBB46o8G3QgGn3XjVLwWcl6Ykxou4kvusM
youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=api_key)

st.title('EXTRACT TRANSFORMATION')
st.header('Enter YouTube Channel_ID below')
st.text('Hint:Go to channel\'s home page>>Right click>>view page source>>Find channel id')
youtube_channel_id = st.text_input('Enter some Channel ID 👇,')

conn = st.connection('youtubeapi_db', type='sql')


# Reading videos information based on video id
def get_video_info(video_id):
    response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    ).execute()

    if len(response['items']) != 0:
        video_item = response['items'][0]
        video_detail = {
            "Video_Id": video_item['id'],
            "Video_Name": video_item['snippet']['title'],
            "Video_Description": video_item['snippet']['description'],
            "Tags": [] if (video_item['snippet'].get('tags') is None) else video_item['snippet']['tags'],
            "PublishedAt": video_item['snippet']['publishedAt'],
            "View_Count": '0' if (video_item['statistics'].get('viewCount') is None) else video_item['statistics']['viewCount'],
            "Like_Count": '0' if (video_item['statistics'].get('likeCount') is None) else video_item['statistics']['likeCount'],
            "Dislike_Count": '0' if (video_item['statistics'].get('dislikeCount') is None) else video_item['statistics']['dislikeCount'],
            "Favorite_Count": '0' if (video_item['statistics'].get('favoriteCount') is None) else video_item['statistics']['favoriteCount'],
            "Comment_Count": '0' if (video_item['statistics'].get('commentCount') is None) else video_item['statistics']['commentCount'],
            "Duration": video_item['contentDetails']['duration'],
            "Thumbnail": video_item['snippet']['thumbnails']['default']['url'],
            "Caption_Status": video_item['contentDetails']['caption'],
            "Comments": {} if ((video_item['statistics'].get('commentCount') is None) or (
                    video_item['statistics']['commentCount'] == '0')) else get_comment_info(video_item['id'])
        }

    return video_detail


# Reading comments information based on video id
def get_comment_info(video_id):
    response = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id
    ).execute()

    comments = {}
    for i in range(0, len(response['items'])):
        comment_item = response['items'][i]
        comments["Comment_Id_" + str(i + 1)] = {"Comment_Id": comment_item['id'],
                                                "Comment_Text": comment_item['snippet']['topLevelComment']['snippet'][
                                                    'textDisplay'],
                                                "Comment_Author": comment_item['snippet']['topLevelComment']['snippet'][
                                                    'authorDisplayName'],
                                                "Comment_PublishedAt":
                                                    comment_item['snippet']['topLevelComment']['snippet']['publishedAt']
                                                }

    return comments


# getting video information based on playlist id
def get_playlist_info(playlist_id, video_count=1):
    response = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=playlist_id
    ).execute()

    next_page_token = response['nextPageToken']
    videos = {}

    while next_page_token != '':
        for i in response['items']:
            videos["Videos_Id_" + str(video_count)] = get_video_info(i['contentDetails']['videoId'])
            video_count = video_count + 1

        if response.get('nextPageToken') is not None:
            next_page_token = response['nextPageToken']
            response = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                pageToken=next_page_token
            ).execute()
        else:
            next_page_token = ''

    return videos


# getting channel information based on youtube id
def get_channel_info(channel_id):
    response = youtube.channels().list(
        part="statistics,snippet,contentDetails,status,brandingSettings",
        id=channel_id
    ).execute()

    item_info = response['items'][0]

    channel_details = {"Channel_name": item_info['snippet']['title'],
                       "Channel_id": item_info['id'],
                       "Subscription_Count": item_info['statistics']['subscriberCount'],
                       "Channel_Views": item_info['statistics']['viewCount'],
                       "Channel_Description": item_info['snippet']['description'],
                       "Channel_country": 'IN' if (item_info['brandingSettings']['channel'].get('country') is None) else
                       item_info['brandingSettings']['channel']['country'],
                       "Channel_status": item_info['status']['privacyStatus'],
                       "Playlist_id": item_info['contentDetails']['relatedPlaylists']['uploads']
                       }
    video_details = get_playlist_info(item_info['contentDetails']['relatedPlaylists']['uploads'])

    return channel_details, video_details


# Extracting Youtube channel information from Youtube API.
if st.button("Extract Data"):
    print('Extraction Begin')
    (channel_Details, video_Details) = get_channel_info(youtube_channel_id)
    st.session_state['channel_Details'] = channel_Details
    st.session_state['video_Details'] = video_Details
    print('Extraction Completed')

# Inserting Youtube channel information into tables
if st.button("Upload SQLITE"):
    print('Uploaded Begin')
    with conn.session as s:
        s.execute('''INSERT OR REPLACE INTO Channel (channel_id,
                                          channel_name,
                                          channel_description,
                                          channel_country,
                                          channel_views,
                                          channel_subscription_count,
                                          channel_status) VALUES (:Channel_id, :Channel_name,:Channel_Description,:Channel_country,
                                          :Channel_Views,:Channel_subscription_count,:Channel_status);'''
                  , params=dict(Channel_id=st.session_state['channel_Details']['Channel_id'],
                                Channel_name=st.session_state['channel_Details']['Channel_name'],
                                Channel_Description=st.session_state['channel_Details']['Channel_Description'],
                                Channel_country=st.session_state['channel_Details']['Channel_country'],
                                Channel_Views=st.session_state['channel_Details']['Channel_Views'],
                                Channel_subscription_count=st.session_state['channel_Details']['Subscription_Count'],
                                Channel_status=st.session_state['channel_Details']['Channel_status']
                                ))

        s.execute('''INSERT OR REPLACE into Playlist (playlist_id,
                                             channel_id,
                                             playlist_name)
                                              VALUES (:Playlist_id,:Channel_id, :Playlist_name);'''
                  , params=dict(Playlist_id=st.session_state['channel_Details']['Playlist_id'],
                                Channel_id=st.session_state['channel_Details']['Channel_id'],
                                Playlist_name=st.session_state['channel_Details']['Channel_name']
                                ))

        for i in range(1, len(st.session_state['video_Details']) + 1):
            video_info = st.session_state['video_Details']['Videos_Id_' + str(i)]
            s.execute('''INSERT OR REPLACE into Video (video_id,
                                                        playlist_id,
                                                        video_name,
                                                        video_description,
                                                        published_data,
                                                        view_count,
                                                        like_count,
                                                        dislike_count,
                                                        favorite_count,
                                                        comment_count,
                                                        duration,
                                                        thumbnail,
                                                        caption_status)
                                                         VALUES (:Video_Id,:playlist_id, :Video_Name,:Video_Description,
                                                         :published_data,:View_Count,:Like_Count,:Dislike_Count,:Favorite_Count,
                                                         :Comment_Count,:Duration,:Thumbnail,:CaptionStatus);'''
                      , params=dict(Video_Id=video_info['Video_Id'],
                                    playlist_id=st.session_state['channel_Details']['Playlist_id'],
                                    Video_Name=video_info['Video_Name'],
                                    Video_Description=video_info['Video_Description'],
                                    published_data=video_info['PublishedAt'],
                                    View_Count=video_info['View_Count'],
                                    Like_Count=video_info['Like_Count'],
                                    Dislike_Count=video_info['Dislike_Count'],
                                    Favorite_Count=video_info['Favorite_Count'],
                                    Comment_Count=video_info['Comment_Count'],
                                    Duration=video_info['Duration'].replace('PT', ''),
                                    Thumbnail=video_info['Thumbnail'],
                                    CaptionStatus=video_info['Caption_Status']
                                    ))

            comment_list = video_info['Comments']
            for i in range(1, len(comment_list) + 1):
                comment_info = comment_list['Comment_Id_' + str(i)]
                s.execute('''INSERT OR REPLACE into Comment (comment_id,
                                                             video_id,
                                                             comment_text,
                                                             comment_author,
                                                             comment_published_date
                                                             )
                                                              VALUES (:comment_id,:Video_Id, :Comment_Text,
                                                              :Comment_Author,:PublishedAt);'''
                          , params=dict(comment_id=comment_info['Comment_Id'],
                                        Video_Id=video_info['Video_Id'],
                                        Comment_Text=comment_info['Comment_Text'],
                                        Comment_Author=comment_info['Comment_Author'],
                                        PublishedAt=comment_info['Comment_PublishedAt']
                                        ))

        s.commit()
        s.close()
        print('Uploaded End')
