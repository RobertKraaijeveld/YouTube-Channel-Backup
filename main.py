#!/usr/bin/python
import argparse
import os
import re

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
API_KEY = ''

# Setting API key from apikey.secret file and setting YOUTUBE_API var
with open('apikey.secret', 'r') as apikeyfile:
    API_KEY = apikeyfile.read().replace('\n', '')
    print(API_KEY)

YOUTUBE_API = build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)



def get_channel_id_by_username(username):
    requestResult = YOUTUBE_API.channels().list(part='id',forUsername=username).execute()
    return requestResult['items'][0]['id']


def get_videos_of_channel(channelId):
    videosIdsPerPage = 10
    firstResult = YOUTUBE_API.search().list(part='id',channelId=channelId,type='video',maxResults=videosIdsPerPage).execute()

    # if the first result contains all the vids already we obviously dont bother with paginating
    if 'nextPageToken' in firstResult:
        return paginate_video_ids_of_channel(firstResult['nextPageToken'], [], videosIdsPerPage) 
    else: 
        return get_video_ids_from_searchresult(firstResult)


def get_video_ids_from_searchresult(result):
    ids = []
    for videoItem in result['items']:
        ids.append(videoItem['id']['videoId'])
    return ids


def paginate_video_ids_of_channel(pageToken, videoIds, videosIdsPerPage):
    currentPage = YOUTUBE_API.search().list(part='id',pageToken=pageToken,type='video',maxResults=videosIdsPerPage).execute()
    videosIdsInCurrentPage = get_video_ids_from_searchresult(currentPage)
    videoIds = videoIds + videosIdsInCurrentPage

    if len(videosIdsInCurrentPage) < videosIdsPerPage: # current page was last page, we're done.
        return videoIds
    else: # Not done yet, so recurse and process next page.
        nextPageToken = currentPage['nextPageToken']
        return paginate_video_ids_of_channel(nextPageToken, videoIds, videosIdsPerPage)


if __name__ == '__main__':
    try:
        testChannelId = get_channel_id_by_username('davidr64yt')
        channelVideoIds = get_videos_of_channel(testChannelId)
        print(channelVideoIds)
    except HttpError as e:
        print(e)