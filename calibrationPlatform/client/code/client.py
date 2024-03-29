from urllib import response
import requests
import numpy as np
import urllib.request
import os
import shutil
from PIL import Image
import glob
from datetime import date


class Menu():
    def __init__(self):
        # self.rigIP = "calibrationPlatform.local"
        # self.wandIP = input("Input IP of wand (default: danwand.local): ")
        self.rigIP = "calibrationPlatform.local"
        self.wandIP = "cm.local"
        self.clearImg()

    def infoPage(self):
        print("\n Welcome! You have the following options. \n \
    1: Change hostnames \n \
    2: Calibrate \n \
    3: Get current pose\n \
    4: Move stepper x mm in y direction \n \
    5: Go to pose x in mm \n \
    6: Take a picture \n \
    7: Move n steps with x mm spacing and capture images \n \
    8: To capture images independent of the platform")

        self.option = 0

        self.option = int(input("Please enter a number: "))
        if(self.option == 1):
            self.changeHostname()
        elif (self.option == 2):
            self.height = self.calibrate()
        elif(self.option == 3):
            self.heigt = self.getCurrentPose()
        elif(self.option == 4):
            self.height = self.moveStepper()
        elif(self.option == 5):
            pose = input("Enter pose in mm: ")
            code = self.go2pose(pose)
            # print(code.text)
        elif(self.option == 6):
            name = input("input pic fileName: ")
            self.takePic(name)
        elif(self.option == 7):
            self.clearImg()
            self.height = self.moveInterval()
        elif(self.option == 8):
            self.clearImg()
            test = self.takePic_dataset()
        else:
            self.infoPage()

    def calibrate(self):
        response = requests.get(f"http://{self.rigIP}:5000/calibrate/")
        self.getCurrentPose()
        return response

    def getCurrentPose(self):
        response = requests.get(f"http://{self.rigIP}:5000/getCurrentPose_mm/")
        print(f"\nCurrent pose is: {response.text}")
        return response

    def moveStepper(self):
        direction = input("Enter direction 1 for up. 0 for down: ")
        if (direction == "1"):
            direction = "up"
        elif (direction == "0"):
            direction = "down"
        else:
            print(f"{direction} is an invalid option")
            self.moveStepper()

        x_mm = input("Enter travel in mm: ")

        response = requests.get(
            f"http://{self.rigIP}:5000/moveStepper_mm/{direction}/{x_mm}/")
        return response

    def changeHostname(self):
        rigIP_change = input(
            "Enter new hostname/IP for the rig (press enter to leave unchanged): ")
        wandIP_change = input(
            "Enter new hostname/IP for the wand (press enter to leave unchanged): ")
        if(rigIP_change != ""):
            self.rigIP = rigIP_change
        if(wandIP_change != ""):
            self.wandIP = wandIP_change
        print(
            f"\nRig hostname/IP = {self.rigIP} \nWand hostname/IP = {self.wandIP}")

    def go2pose(self, pose):
        print("Moving stepper")
        # pose = input("Enter desired pose: ")
        response = requests.get(f"http://{self.rigIP}:5000/go2pose_mm/{pose}/")
        return response

    def takePic(self, name):

        url = f"http://{self.wandIP}:8080/pic/picture?size=160"
        # response = requests.get(url)
        pwd = os.path.dirname(os.path.realpath(__file__))
        try:
            os.mkdir(f"{pwd}/images/")
        except:
            pass
        try:
            os.mkdir(f"{pwd}/images/render{name}")
        except:
            pass

        print("Taking a picture - no light")
        urllib.request.urlretrieve(
            f"{url}", f"{pwd}/images/render{name}/image9.jpg")
        im = Image.open(f"{pwd}/images/render{name}/image9.jpg")
        im.save(f"{pwd}/images/render{name}/image9.png")

        print("Taking a picture - flash")
        urllib.request.urlretrieve(
            f"{url}&flash=1", f"{pwd}/images/render{name}/image8.jpg")
        im = Image.open(f"{pwd}/images/render{name}/image8.jpg")
        im.save(f"{pwd}/images/render{name}/image8.png")

        print("Taking a picture - dias")
        urllib.request.urlretrieve(
            f"{url}&dias=1", f"{pwd}/images/render{name}/image0.jpg")
        im = Image.open(f"{pwd}/images/render{name}/image0.jpg")
        im.save(f"{pwd}/images/render{name}/image0.png")

        self.clearJPG(name)

    def takePic_dataset(self):
        takePic_dataset_name = 0
        while(1):

            command = input(
                'Press enter to capture new image or enter "exit" to exit: ')
            if(command == ""):
                self.takePic(takePic_dataset_name)
                takePic_dataset_name += 1
            elif(command == "exit"):
                takePic_dataset_name = 0
                break
        return 1

    def moveInterval(self):
        print("The platform will start at height A and move down to heigt B at an interval x given in mm")
        startPose = input("Enter start pose A: ")
        endPose = input("Enter end pose B: ")
        stepInterval = input("Enter step interval x in mm: ")

        stepArray = np.arange(float(startPose), float(
            endPose), float(stepInterval))
        print(stepArray)
        name_height_translation = ""
        for idx, i in enumerate(stepArray):
            self.go2pose(i)
            self.takePic(idx)
            print(f"moving to: {i}")
            name_height_translation += f"{idx}:{i}\n"
        # post-fence fix
        self.go2pose(i+float(stepInterval))
        self.takePic(idx+1)
        print(f"moving to: {i+float(stepInterval)}")
        name_height_translation += f"{idx}:{i+float(stepInterval)}\n"

        zoom = self.getParams()
        today = date.today()
        pwd = os.path.dirname(os.path.realpath(__file__))
        f = open(f"{pwd}/images/params.txt", 'w')
        f.write(f"Number of images: {len(stepArray)+1}\n \
Start height: {startPose} mm\n \
End height : {endPose} mm\n \
Distance between images: {stepInterval} mm\n \
Zoom (last value is zoom): {zoom}\n \
Date: {today}")

        f.close()

        self.calibrate()

    def clearImg(self):
        pwd = os.path.dirname(os.path.realpath(__file__))

        # os.rmdir(f"{pwd}/images/")
        try:
            shutil.rmtree(f"{pwd}/images")
        except:
            pass

    def clearJPG(self, name):
        pwd = os.path.dirname(os.path.realpath(__file__))

        files = glob.glob(f"{pwd}/images/render{name}/*.jpg")
        for f in files:
            os.remove(f)

    def getParams(self):
     #       response = requests.get(f"http://{self.wandIP}:8080/pic/info")
        # print(response.content)
      #      response_json = json.loads(str(response.content))
      #      print(response_json["zoom"])

        import json
        import urllib.request
        data = urllib.request.urlopen(
            f"http://{self.wandIP}:8080/pic/info").read()
        data = str(data)
        idx = data.find("zoom")
        data = data[idx-1:]

        data = data.replace("\\", "")
        data = data.replace('<br><a href="/">', "")
        data = data.replace("Back</a>'", "")
        data = data.replace("<br />", "")
        data = data.replace("'", '"')
        data = data.replace("}", "")
        data = data.replace('"zoom": ', "")
        return data

        # print(data)
        #output = json.loads(str(data))
        #print (output)


if __name__ == "__main__":
    menu = Menu()

    if(menu.wandIP == ""):
        menu.wandIP = "danwand.local"

    while(1):
        menu.infoPage()
