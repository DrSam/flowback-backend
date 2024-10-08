from django.core.exceptions import ValidationError
import os


def allowed_image_extensions(value):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', 'avif', '.gif']
    ext = os.path.splitext(value.name)[1]
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')
