import face_recognition
from os import listdir, remove
import numpy as np


def transform_name(x):
    x = x[4:].replace('_', ' ').replace('.jpg', '').replace('.jpeg', '') # get rid of img/ and .jpg
    if '(' in x:
        i = x.index('(')
        return x[i+1:-1]
    return x


def load_encodings_from_images():
    try:
        remove('img/.DS_Store')
    except:
        pass
    base_dir = 'img/'
    images = ['img/' + s for s in listdir('img')]
    encodings = []
    for img in images:
        try:
            encodings.append(face_recognition.face_encodings(face_recognition.load_image_file(img))[0])
        except:
            print img
    names = map(transform_name, images)
    return names, encodings

def save_encodings(names, encodings, fname='kpopEncodings.txt'):
    with open(fname, 'w') as f:
        for i, e in enumerate(encodings):
            name = names[i].replace(' ', "_")
            f.write('{} '.format(name))
            np.savetxt(f, e, newline=' ')
            f.write('\n')


def load_encodings(fname='kpopEncodings.txt'):
    names = []
    encodings = []
    with open(fname, 'r') as f:
        for line in f:
            line = line.split()
            name = transform_name('img/'+line[0])
            names.append(name)
            nums = map(np.float, line[1:])
            encodings.append(np.array(nums))
    return names, encodings


def get_most_similar(encodings, names, img):
    img = face_recognition.load_image_file(img)
    unknown_encoding = face_recognition.face_encodings(img)[0]
    results = face_recognition.face_distance(encodings, unknown_encoding)
    r = np.argmin(results)
    return {'name': names[r], 'score': results[r]}


class KpopSimilarity(object):

    def __init__(self):
        self.names, self.encodings = load_encodings()

    def get_most_similar(self, img):
        return get_most_similar(self.encodings, self.names, img)


if __name__ == '__main__':
    # names, encodings = load_encodings_from_images()
    # save_encodings(names, encodings)
    n, e = load_encodings()
