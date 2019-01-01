#!/usr/bin/python
import argparse
import os
import re
import isodate

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


###############################################
# FUNCTIONS FOR GETTING VIDEO IDS FROM CHANNEL 
###############################################

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


######################################################
# FUNCTIONS FOR GETTING VIDEO DETAILS USING VIDEO IDS
######################################################

AVG_MBS_PER_HD_SECOND = 0.23
AVG_MBS_PER_SD_SECOND = 0.09

# Per quality type, get the avg length TODO: PAGING PLS
def get_videos_for_ids(videosIds):
    videoIdsAsStr = ",".join(videosIds)
    return YOUTUBE_API.videos().list(part='snippet,contentDetails',id=videoIdsAsStr).execute()

def get_videos_by_quality_type(videos):
    # Only 2 quality types, SD or k
    vids = {}
    vids['hd'] = [v for v in videos if v['contentDetails']['definition']]
    vids['sd'] = [v for v in videos if v['contentDetails']['definition'] == 'sd']
    return vids

def get_average_vid_length_per_quality_type(videosPerQualityType):
    hdVids = videosPerQualityType['hd']
    sdVids = videosPerQualityType['sd']

    sdTotalLengths = sum(isodate.parse_duration(v['contentDetails']['duration']).total_seconds() for v in sdVids)
    hdTotalLengths = sum(isodate.parse_duration(v['contentDetails']['duration']).total_seconds() for v in hdVids)

    averageVidLengthsPerQuality = {}
    averageVidLengthsPerQuality['hd'] = hdTotalLengths / len(hdVids)
    averageVidLengthsPerQuality['sd'] = sdTotalLengths / len(sdVids)
    return averageVidLengthsPerQuality

def get_estimated_total_size(averageVidLengthsPerQuality, amountOfHdVids, amountOfSdVids):
    sdVidsEstimatedSize = (amountOfSdVids * averageVidLengthsPerQuality['sd']) * AVG_MBS_PER_SD_SECOND
    hdVidsEstimatedSize = (amountOfHdVids * averageVidLengthsPerQuality['hd']) * AVG_MBS_PER_HD_SECOND
    return sdVidsEstimatedSize + hdVidsEstimatedSize



if __name__ == '__main__':
    try:
        testChannelId = get_channel_id_by_username('romulus310')
        channelVideoIds = get_videos_of_channel(testChannelId)

        if any(channelVideoIds):
            channelVideos = get_videos_for_ids(channelVideoIds)['items']
            videosByQualityType = get_videos_by_quality_type(channelVideos)

            averageVidLengths = get_average_vid_length_per_quality_type(videosByQualityType)
            print(get_estimated_total_size(averageVidLengths, len(videosByQualityType['hd']), len(videosByQualityType['sd'])))
        else:
            print("Sorry, this channel has no videos.")

    except HttpError as e:
        print(e)