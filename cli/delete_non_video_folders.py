root_path = "/System/Resources/Komorebi"

video_file_extensions = [".mp4", ".webm", ".mov", ".avi", ".wmv", ".flv", ".mkv", ".m4v", ".mpg", ".mpeg", ".m2v", ".3gp", ".3g2", ".mxf", ".roq", ".nsv", ".f4v", ".f4p", ".f4a", ".f4b"]
import os

for folder in os.listdir(root_path):
    folder_path = os.path.join(root_path, folder)

    if os.path.isdir(folder_path):
        files = os.listdir(folder_path)

        # check if any mp4 file is in folder
        has_video = False
        for file in files:
            for extension in video_file_extensions:
                if file.endswith(extension):
                    has_video = True
                    break
            if has_video:
                break

        # check if any picture file is in folder
        has_picture = False
        for file in files:
            if file.endswith(".png") or file.endswith(".jpg"):
                has_picture = True
                break

        # if folder has neither a picture nor an mp4, delete it
        if not has_picture and not has_video:
            print("Folder missing both wallpaper thumbnail pic and video " + folder_path)
            print("Deleting " + folder_path)
            # shutil.rmtree(folder_path)

        if not has_video:
            print("Folder missing video " + folder_path)
            print("Deleting " + folder_path)
            # shutil.rmtree(folder_path)

