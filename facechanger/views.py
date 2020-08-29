from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.core.cache import cache
import os
import cv2
from PIL import Image
from facechanger.models import MyModel
from django.conf import settings
import json

global filename


def index(request):
    cache.clear()
    if request.method == 'POST' and request.FILES['myfile']:
        your_media_root = settings.MEDIA_ROOT
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        new_photo = MyModel()
        new_photo.original_model = myfile
        # filename_original = fs.save("unrendered" + myfile.name, myfile)
        imagePath = fs.open(myfile.name)
        cascPath = fs.open("haarcascade_frontalface_default.xml")
        faceCascade = cv2.CascadeClassifier(str(cascPath))
        image = cv2.imread(str(imagePath))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        print("Found {0} faces!".format(len(faces)))
        for (x, y, w, h) in faces:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imwrite(str(imagePath), image)
        new_photo.faceselected_model = str(imagePath)
        print(new_photo.faceselected_model)
        new_photo.save()
        return render(request, "facedetection.html",
                      {"filename": your_media_root + "/" + new_photo.original_model.name,
                       "filename_detected": new_photo.faceselected_model, 'face_count': len(faces)})
    return render(request, 'index.html')


def facedetection(request):
    return render(request, "facedetection.html", {'filename': filename})


def faceshuffle(request):
    fs = FileSystemStorage()
    list = MyModel.objects.last()
    imagePath = fs.open(list.original_model.path)
    cascPath = fs.open("haarcascade_frontalface_default.xml")
    faceCascade = cv2.CascadeClassifier(str(cascPath))
    image = cv2.imread(str(imagePath))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    img_counter = 0
    # print("Found {0} faces!".format(len(faces)))
    os.mkdir(str(settings.MEDIA_ROOT) + "/" + str(list.id))
    json_data = dict()
    faces_coordinates_list = []
    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        faces_coordinates_list.append((x, y))
        # print((x, y, x + w, y + w))
        original = Image.open(imagePath)
        croped_img = original.crop((x, y, x + w, y + w))
        croped_img.save(str(settings.MEDIA_ROOT) + "/" + str(list.id) + "/" + str(img_counter) + ".jpeg")

        json_data["{}".format(img_counter)] = {"id": img_counter,
                              "img_path": str(settings.MEDIA_ROOT) + "/" + str(list.id) + "/" + str(
                                  img_counter) + ".jpeg",
                              "heigth": (x + w) - x,
                              "width": (y + h) - y
                              }
        img_counter += 1
    json_data = str(json_data).replace("'",'"')
    with open(str(settings.MEDIA_ROOT) + "/" + str(list.id) + "/" + "faces.json", "w") as json_file:
        json.dump(json_data, json_file)
    new_img = Image.open(imagePath)
    faces_list = [x for x in range(0, len(faces))]
    faces_list.reverse()
    # print(faces_coordinates_list)
    # print(faces_list)
    # faces_list.reverse()
    # print(faces_list)
    with open(str(settings.MEDIA_ROOT) + "/" + str(list.id) + "/" + "faces.json" ) as json_file :
        data = json.load(json_file)
    print(data[4])
    face_count = 0
    for image_no in faces_list:
        im2 = Image.open(str(settings.MEDIA_ROOT) + "/" + str(list.id) + "/" + str(image_no) + ".jpeg")
        new_img.paste(im2, faces_coordinates_list[face_count])
        face_count += 1
    new_img.save(str(settings.MEDIA_ROOT) + "/" + str(list.id) + "/" + "output" + ".jpeg")
    shuffled_face_path = str(settings.MEDIA_ROOT) + "/" + str(list.id) + "/" + "output" + ".jpeg"
    return render(request, "faceshuffle.html",
                  {'detected_model': list.faceselected_model, 'shuffled_model': shuffled_face_path})


def restart(request):
    cache.clear()
    return redirect('index')


def download_image(request):
    list = MyModel.objects.last()
    shuffled_face_path = str(settings.MEDIA_ROOT) + "/" + str(list.id) + "/" + "output" + ".jpeg"
    return render(request, "downloadimage.html", {"face": shuffled_face_path})
