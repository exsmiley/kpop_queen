# need to install boost-python (can brew install boost-python on mac)
import face_recognition

images = ['img/jatin1.jpg', 'img/nick1.jpg']

# face_recognition.load_image_file("../jatin1.jpg")

known_images = map(face_recognition.load_image_file, images)
encodings = map(lambda x: face_recognition.face_encodings(x)[0], known_images)

unknown = face_recognition.load_image_file('img/zach1.jpg')
unknown_encoding = face_recognition.face_encodings(unknown)[0]

results = face_recognition.compare_faces(encodings, unknown_encoding)
print results
