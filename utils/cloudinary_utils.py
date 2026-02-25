import cloudinary.uploader

def upload_file(file, folder):
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        resource_type="auto"
    )
    return result["secure_url"]