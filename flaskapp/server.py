from werkzeug.utils import secure_filename
from secrets import AWS_ACCESS_KEY, AWS_SECRET_KEY
import face_recognition
from flask import Flask, jsonify, request, redirect, url_for
from boto3.dynamodb.conditions import Key
import boto3
import numpy as np

REGION="us-east-1"

s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY,
                        aws_secret_access_key=AWS_SECRET_KEY,
                        region_name=REGION)

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_KEY,
                            region_name=REGION)

table = dynamodb.Table('Spotify')
BUCKET = 'spotify-profile-pictures'

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

@app.route("/connect")
def hello():
    return 'Hello world'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file_to_s3(file, bucket_name, acl="private"):
    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )

    except Exception as e:
        print("Something Happened: ", e)
        return e

    return "{}{}".format('http://{}.s3.amazonaws.com/'.format(BUCKET), file.filename)

def determine_likes(other_music_taste, current_username):
    response = table.scan(
        FilterExpression=Key('user_id').eq(current_username)
    )
    user_music_taste = response['Items'][0]['music_taste']
    lookup = {}
    user_keys = set()
    other_keys = set()
    for item in user_music_taste:
        lookup[item['id']] = (item['name'], item['popularity'])
        user_keys.add(item['id'])
    for item in other_music_taste:
        other_keys.add(item['id'])
        if item['id'] not in lookup:
            lookup[item['id']] = (item['name'], item['popularity'])
    mutual_ids = user_keys.intersection(other_keys)
    mutual = {key:lookup[key] for key in mutual_ids}
    first_three = sorted(mutual, lambda x: x[1])[:3]
    return [lookup[item][0] for item in first_three]

@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    # Check if a valid image file was uploaded
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        current_username = request.form['username']
        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # The image file seems valid! Detect faces and return the result.
            file.filename = secure_filename(file.filename)
            # upload_file_to_s3(file, BUCKET)
            match = detect_faces_in_image(file)
            if not match:
                output = jsonify({"error": "No matches found."})
                output.status_code = 400
                return output
            response = table.scan(
                FilterExpression=Key('user_id').eq(match)
            )
            item = response['Items'][0]
            output = {
                'user_id': match,
                'name': item['name'],
                'likes': determine_likes(item['music_taste'], current_username)
            }
            return jsonify(output)

    # If no valid image file was uploaded, show the file upload form:
    return '''
    <!doctype html>
    <title>Augmented Reality</title>
    <h1>Upload a picture and find out a topic of conversation with that person</h1>
    <form method="POST" enctype="multipart/form-data">
        <input type="text" name="username">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    '''

def match_face(data, unknown_face):
    known_face_encodings = {}
    for item in data:
        for image in item['images']:
            known_face_encodings[item['user_id']] = np.array(image['cache'], dtype=float)
    match_results = face_recognition.compare_faces(known_face_encodings.values(), unknown_face)
    y = (i for i,v in enumerate(match_results) if v)
    try:
        return known_face_encodings.keys()[y.next()]
    except (StopIteration, IndexError):
        return None

def detect_faces_in_image(file_stream):
    # Load the uploaded image file
    img = face_recognition.load_image_file(file_stream)
    # Get face encodings for any faces in the uploaded image
    unknown_face_encodings = face_recognition.face_encodings(img)
    if len(unknown_face_encodings) == 0:
        return jsonify({'error': 'Image must include a face.'})

    response = table.scan(Limit=5)
    matched = match_face(response['Items'], unknown_face_encodings[0])
    print matched
    if matched:
        return matched

    while response.get('LastEvaluatedKey'):
        response = table.scan(Limit=5, ExclusiveStartKey=response['LastEvaluatedKey'])
        matched = match_face(response['Items'], unknown_face_encodings[0])
        print matched
        if matched:
            return matched    
    return None

if __name__ == '__main__':
    app.run(debug=True, port=8000)