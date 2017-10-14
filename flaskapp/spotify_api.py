import spotipy
import spotipy.util as util
from boto3.dynamodb.conditions import Key
import boto3
from secrets import AWS_ACCESS_KEY, AWS_SECRET_KEY
import face_recognition
import urllib, cStringIO
from decimal import Decimal

REGION="us-east-1"
scope = "user-follow-read"

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_KEY,
                            region_name=REGION)
table = dynamodb.Table('Spotify')

def get_user_info(username=None):
    token = util.prompt_for_user_token(username, scope)
    if token:
        sp = spotipy.Spotify(auth=token)
        music_taste = [
            {'id': item['id'], 'name': item['name'], 'popularity': item['popularity']}
            for item in sp.current_user_followed_artists()['artists']['items']
        ]
        current_user = sp.current_user()
        image_urls = [
            image['url']
            for image in current_user['images']
        ]
        image_pre_cached = [
            {
                'url': url,
                'cache': [
                    Decimal(elem)
                    for elem in face_recognition.face_encodings(
                                    face_recognition.load_image_file(
                                        file = cStringIO.StringIO(urllib.urlopen(url).read())
                                    )
                                )[0]
                ]
            }
            for url in image_urls
        ]
        response = table.scan(
            FilterExpression=Key('user_id').eq(current_user['id'])
        )
        if response['Count'] == 0:
            table.put_item(Item={
                'user_id': current_user['id'],
                'name': current_user['display_name'],
                'music_taste': music_taste,
                'images': image_pre_cached
            })
    else:
        print "Can't get token for", username

if __name__ == '__main__':
    get_user_info('frognamekrog')